bl_info = {
    "name": "Velvet Engine Tools",
    "description": "Hosts a bunch of tools to handle Velvet Engine files for the GameCube version.",
    "author": "Exortile",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "File > Export, File > Import",
    "warning": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

from .exceptions import VException
from .export import export_vobj


class VELVET_OT_export_vobj(bpy.types.Operator, ExportHelper):
    """Exports a Velvet 3D object"""

    bl_idname = "velvet.export_vobj"
    bl_label = "Export VOBJ"

    filename_ext = ".vobj"
    filter_glob: StringProperty(
        default="*.vobj",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords()

        try:
            export_vobj(**keywords)
        except VException as exc:
            exc.invoke()
            return {"CANCELLED"}

        return {"FINISHED"}


class VelvetMaterialProperties(bpy.types.PropertyGroup):
    disable_backface_culling: BoolProperty(
        name="Disable Backface Culling",
        description="Turns off backface culling for this material",
        default=False
    )

    disable_specular_lighting: BoolProperty(
        name="Disable Specular Lighting",
        description="Turns off specular lighting for this material",
        default=False
    )

    disable_lighting: BoolProperty(
        name="Disable Lighting",
        description="Turns off lighting for this material (makes it fullbright)",
        default=False
    )


class VelvetMaterialPropertiesPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    bl_idname = "MATERIAL_PT_vobj"
    bl_label = "VOBJ Material Properties"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'MESH' and context.active_object.active_material is not None

    def draw(self, context):
        layout = self.layout
        properties = context.active_object.active_material.vobj_props

        box = layout.box()
        box.prop(properties, "disable_backface_culling")
        box.prop(properties, "disable_specular_lighting")
        box.prop(properties, "disable_lighting")


def menu_export_func(self, context):
    self.layout.operator(VELVET_OT_export_vobj.bl_idname)


classes = [
    VELVET_OT_export_vobj,
    VelvetMaterialProperties,
    VelvetMaterialPropertiesPanel
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_export_func)

    bpy.types.Material.vobj_props = bpy.props.PointerProperty(type=VelvetMaterialProperties)


if __name__ == "__main__":
    register()
