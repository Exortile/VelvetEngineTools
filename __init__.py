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
from bpy_extras.io_utils import ExportHelper
from bpy.props import IntProperty, BoolProperty, StringProperty, EnumProperty, FloatProperty
from .export import export_vobj
from .exceptions import VException


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


def menu_export_func(self, context):
    self.layout.operator(VELVET_OT_export_vobj.bl_idname)


classes = [
    VELVET_OT_export_vobj
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_export_func)


if __name__ == "__main__":
    register()
