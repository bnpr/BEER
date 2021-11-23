# Copyright (c) 2021 BlenderNPR and contributors. MIT license. 

bl_info = {
    "name" : "BlenderBeer",
    "author" : "Alice Lawrie",
    "description" : "A UI for a layer-based rendering system using the Malt backend",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "category" : "Rendering"
}

import sys, os
from os import path
import bpy


def get_modules():
    from . import BeerMaterial, BeerPanel
    return [ BeerMaterial, BeerPanel ]

classes=[
]

def register():
    import importlib
    for module in get_modules():
        importlib.reload(module)

    for _class in classes: bpy.utils.register_class(_class)

    for module in get_modules():
        module.register()


def unregister():
    for _class in reversed(classes): bpy.utils.unregister_class(_class)

    for module in reversed(get_modules()):
        module.unregister()

if __name__ == "__main__":
    register()
