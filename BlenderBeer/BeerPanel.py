# Copyright (c) 2021 BlenderNPR and contributors. MIT license. 

import bpy
from BlenderMalt import MaltProperties
from BlenderMalt import MaltMaterial


class Beer_PT_MainPanel(bpy.types.Panel):
    bl_label = "BEER"
    bl_idname = "PT_BEER_MAINPANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BEER'
    COMPAT_ENGINES = {'MALT'}

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'MALT' and context.object is not None


    def draw(self, context):
        layout = self.layout

        row = layout.row()
        ob = context.object
        if ob:
            row = layout.row()
            row.operator("material.new_beer", text= "New BEER Material")
            if ob.active_material.beer.is_beer_mat:
                row = layout.row()
                ob.active_material.beer.draw_ui(layout)

            
def register():
    bpy.utils.register_class(Beer_PT_MainPanel)


def unregister():
    bpy.utils.unregister_class(Beer_PT_MainPanel)


if __name__ == "__main__":
    register()
