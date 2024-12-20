from dataclasses import dataclass
import bpy


@dataclass
class VException(Exception):
    message: str

    def draw(self, popup, context):
        popup.layout.label(text=self.message)

    def invoke(self):
        bpy.context.window_manager.popup_menu(self.draw, title="Error", icon="ERROR")
