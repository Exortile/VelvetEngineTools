from dataclasses import dataclass, field

import bpy

from .exceptions import VException
from .file import VelvetFileWriter
from .gx import *
from .structures import *
from .util import read_struct


def check_node_id(node, identifier):
    return node.bl_idname == "ShaderNode" + identifier


def convert_color_to_rgba(color):
    return int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)


@dataclass
class Material:
    flags: list[bool] = field(default_factory=list)
    diffuse_color: tuple = (200, 200, 200)
    specular_color: tuple = (255, 255, 255)
    shininess: float = 64.0
    has_texture: bool = False
    texture_name: str = ""


@dataclass
class Mesh:
    bpy_mesh: bpy.types.Mesh

    positions: list = field(default_factory=list)
    normals: list = field(default_factory=list)
    uvs: list = field(default_factory=list)
    colors: list = field(default_factory=list)

    # each vertex will correspond to a list with indices to all elements of it (pos, norms, uvs, etc.)
    indices: list[list[int]] = field(default_factory=list)

    draw_format: int = GX_DRAW_QUADS

    has_uvs: bool = False
    has_colors: bool = False
    vformat: list[VVFormatType] = field(default_factory=list)

    material: Material = field(default_factory=Material)

    display_list_offset: int = 0
    display_list_size: int = 0
    pos_offset: int = 0
    norms_offset: int = 0
    uvs_offset: int = 0
    colors_offset: int = 0

    def calc_draw_format(self):
        if self.bpy_mesh.polygons[0].loop_total == 4:
            self.draw_format = GX_DRAW_QUADS
        elif self.bpy_mesh.polygons[0].loop_total < 4:
            self.draw_format = GX_DRAW_TRIANGLES

    def calc_vertex_format(self):
        self.vformat.append(VVFormatType.Normals)

        if self.bpy_mesh.uv_layers:
            self.vformat.append(VVFormatType.UVs)
            self.has_uvs = True

        if self.bpy_mesh.vertex_colors:
            self.vformat.append(VVFormatType.Colors)
            self.has_colors = True

    def calc_vertices(self):
        for v in self.bpy_mesh.vertices:
            self.positions.append(v)

        uv_layer = self.bpy_mesh.uv_layers.active.data if self.has_uvs else None
        color_layer = self.bpy_mesh.vertex_colors.active.data if self.has_colors else None

        for p in self.bpy_mesh.polygons:
            vertices = []

            for li in range(p.loop_start, p.loop_start + p.loop_total):
                vertex = []

                pos_idx = self.bpy_mesh.loops[li].vertex_index
                vertex.append(pos_idx)

                norm = self.bpy_mesh.loops[li].normal
                normal_exists = norm in self.normals
                norm_idx = self.normals.index(norm) if normal_exists else len(self.normals)
                if not normal_exists:
                    self.normals.append(norm)

                vertex.append(norm_idx)

                if self.has_colors:
                    color = color_layer[li].color
                    color_exists = color in self.colors
                    color_idx = self.colors.index(color) if color_exists else len(self.colors)
                    if not color_exists:
                        self.colors.append(color)

                    vertex.append(color_idx)

                if self.has_uvs:
                    uv = uv_layer[li].uv
                    uv_exists = uv in self.uvs
                    uv_idx = self.uvs.index(uv) if uv_exists else len(self.uvs)
                    if not uv_exists:
                        self.uvs.append(uv)

                    vertex.append(uv_idx)

                vertices.append(vertex)

            vertices[0], vertices[1] = vertices[1], vertices[0]  # swapped for proper culling order
            for v in vertices:
                self.indices.append(v)

    def calc_material(self):
        if len(self.bpy_mesh.materials) > 1:
            raise VException("You can only have one material assigned to a mesh!")

        bpy_material = self.bpy_mesh.materials[0]

        # get material flags
        self.material.flags.append(bpy_material.vobj_props.disable_backface_culling)
        self.material.flags.append(bpy_material.vobj_props.disable_specular_lighting)
        self.material.flags.append(bpy_material.vobj_props.disable_lighting)

        nodes = bpy_material.node_tree.nodes
        material_output = None

        for n in nodes:
            if check_node_id(n, "OutputMaterial"):
                material_output = n
                break

        if material_output is None:
            raise VException("Couldn't find material output node in material!")

        shader_input = material_output.inputs[0]
        if not shader_input.is_linked:
            raise VException("Material output node doesn't have have an input shader!")

        shader = shader_input.links[0].from_node
        if not check_node_id(shader, "BsdfPrincipled"):
            raise VException("Only Principled BSDF shaders allowed.")

        base_color_input = shader.inputs[0]
        self.material.diffuse_color = convert_color_to_rgba(base_color_input.default_value)
        if base_color_input.is_linked and check_node_id(base_color_input.links[0].from_node, "TexImage"):
            self.material.has_texture = True
            self.material.texture_name = base_color_input.links[0].from_node.image.name

        specular_color_input = shader.inputs[13]
        if not specular_color_input.is_linked:
            self.material.specular_color = convert_color_to_rgba(specular_color_input.default_value)
        elif check_node_id(specular_color_input.links[0].from_node, "RGB"):
            self.material.specular_color = convert_color_to_rgba(
                specular_color_input.links[0].from_node.outputs[0].default_value)

    def setup(self):
        self.calc_vertex_format()
        self.calc_draw_format()
        self.calc_vertices()
        self.calc_material()

    def write_display_list(self, file: VelvetFileWriter):
        file.align(32)

        self.display_list_offset = file.tell()

        draw_cmd = self.draw_format | GX_VTXFMT0
        file.write_u8(draw_cmd)
        file.write_u16(len(self.indices))  # vert count

        for idx_list in self.indices:
            for idx in idx_list:
                file.write_u16(idx)

        file.write_u8(GX_NOP)
        file.align(32)

        self.display_list_size = file.tell() - self.display_list_offset

    def write_vertex_data(self, file: VelvetFileWriter):
        self.pos_offset = file.tell()
        [file.write_f32(f) for p in self.positions for f in p.co]

        self.norms_offset = file.tell()
        [file.write_f32(f) for n in self.normals for f in n]

        if self.has_colors:
            pass
            # color_offset = file.tell()
            # [file.write_f32(f) for n in mesh.normals for f in n]

        if self.has_uvs:
            self.uvs_offset = file.tell()
            for uv in self.uvs:
                u = uv[0]
                v = -(uv[1] - 1)
                file.write_f32(u)
                file.write_f32(v)


def export_vobj(**keywords):
    if not bpy.context.object:
        raise VException("You don't have an object selected!")

    if bpy.context.object.data.id_type != "MESH":
        raise VException("The selected object is not a mesh!")

    bpy_obj = bpy.context.object
    bpy_mesh = bpy_obj.data

    mesh = Mesh(bpy_mesh)
    mesh.setup()

    with VelvetFileWriter(open(keywords["filepath"], "wb")) as file:
        file.write_section(VInfo.id, VInfo(VInfo.data_version, *VInfo.make_file_type(VFileType.Model)))

        # object info
        vobj = VObject(VObject.data_version, *VObject.make_vformat(mesh.vformat))
        vobj_offset = file.write_section(VObject.id, vobj)

        # material
        vmat = VMaterials(VMaterials.data_version, *mesh.material.flags, mesh.material.diffuse_color,
                          mesh.material.specular_color,
                          mesh.material.has_texture, 64.0)

        if mesh.material.has_texture:
            vmat_data = (vmat, bytes(mesh.material.texture_name, "ascii") + b'\x00')  # 0x00 for string terminator
        else:
            vmat_data = vmat

        vmat_offset = file.write_section(VMaterials.id, *vmat_data)

        # vertex data
        vvtx = VVertexData(VVertexData.data_version)
        vvtx_offset = file.write_section(VVertexData.id, vvtx)

        # data
        vdat_header_offset = file.tell()
        file.write_header_only("VDAT")

        mesh.write_vertex_data(file)
        mesh.write_display_list(file)

        vdat_next_offset = file.tell()
        file.write_end()

    # Add necessary offsets
    with open(keywords["filepath"], "+rb") as file:
        # update VOBJ offsets
        file.seek(vobj_offset)
        new_vobj = read_struct(file, VObject)

        new_vobj.vertex_data_offset = vvtx_offset
        new_vobj.display_list_offset = mesh.display_list_offset
        new_vobj.display_list_size = mesh.display_list_size
        new_vobj.material_offset = vmat_offset

        file.seek(vobj_offset)
        file.write(new_vobj)

        # update VVTX offsets
        file.seek(vvtx_offset)
        new_vvtx = read_struct(file, VVertexData)

        new_vvtx.positions_offset = mesh.pos_offset
        new_vvtx.normals_offset = mesh.norms_offset
        new_vvtx.uvs_offset = mesh.uvs_offset
        new_vvtx.colors_offset = mesh.colors_offset

        file.seek(vvtx_offset)
        file.write(new_vvtx)

        # update VDAT header offset
        file.seek(vdat_header_offset)
        vdat_header = read_struct(file, VHeader)

        vdat_header.next_header_offset = vdat_next_offset

        file.seek(vdat_header_offset)
        file.write(vdat_header)
