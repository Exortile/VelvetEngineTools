from ctypes import BigEndianStructure, c_uint32, c_uint8, c_char, sizeof, c_float
from ctypes import c_uint8 as c_bool  # big endian doesn't support c_bool lol
from enum import Enum


class BigEndianStructureExt(BigEndianStructure):
    def __len__(self):
        return sizeof(self)


class VHeader(BigEndianStructureExt):
    _fields_ = [
        ("id", c_char * 4),
        ("next_header_offset", c_uint32),
        ("pad", c_char * 8)
    ]


class VFileType(Enum):
    Model = 1
    Scene = 2


class VVFormatType(Enum):
    Normals = 1
    UVs = 2
    Colors = 3


class VInfo(BigEndianStructureExt):
    id = "VINF"
    data_version = 1

    _fields_ = [
        ("version", c_uint32),

        # File type
        ("model_file", c_uint32, 1),
        ("scene_file", c_uint32, 1),
    ]

    @staticmethod
    def make_file_type(file_type: VFileType) -> tuple:
        return file_type == VFileType.Model, \
               file_type == VFileType.Scene


class VObject(BigEndianStructureExt):
    id = "VOBJ"
    data_version = 1

    _fields_ = [
        ("version", c_uint32),

        # Vertex format (positions are implied)
        ("has_normals", c_uint32, 1),
        ("has_uvs", c_uint32, 1),
        ("has_colors", c_uint32, 1),

        ("vertex_data_offset", c_uint32),
        ("material_offset", c_uint32),

        ("display_list_offset", c_uint32),
        ("display_list_size", c_uint32),
    ]

    @staticmethod
    def make_vformat(vformat: list) -> tuple:
        return VVFormatType.Normals in vformat, \
               VVFormatType.UVs in vformat, \
               VVFormatType.Colors in vformat


class VVertexData(BigEndianStructureExt):
    id = "VVTX"
    data_version = 1

    _fields_ = [
        ("version", c_uint32),

        ("positions_offset", c_uint32),
        ("normals_offset", c_uint32),
        ("uvs_offset", c_uint32),
        ("colors_offset", c_uint32),
    ]


class VMaterials(BigEndianStructureExt):
    id = "VMAT"
    data_version = 2

    _fields_ = [
        ("version", c_uint32),

        # material flags
        ("disable_backface_culling", c_bool, 1),
        ("disable_specular_lighting", c_bool, 1),
        ("disable_lighting", c_bool, 1),

        ("diffuse_color", c_uint8 * 3),
        ("specular_color", c_uint8 * 3),
        ("has_texture", c_bool),

        ("shininess", c_float),
    ]
