# Copyright (c) 2021 BlenderNPR and contributors. MIT license. 

from tempfile import template
from typing import Text
import bpy
from bpy.props import EnumProperty
from BlenderMalt import MaltProperties
from BlenderMalt import MaltMaterial
from pygments.token import Comment, Generic, Keyword, Name, Operator, Other, Punctuation
from enum import Enum
import pygments
import pygments.lexers



def update_index(self, context):
    if self["index"] == 0:
        self["index"] = 1
    self["masking_index"] = ["masking_index"]
    self["input_index"] = ["input_index"]

def update_masking(self, context):
    if self["index"]:
        current_index = self["index"]
        masking_index = self["masking_index"]

        if masking_index >= current_index:
            self["masking_index"] = 0
            self["masked_layer"] = False
    else:
        self["masking_index"] = 0
        self["masked_layer"] = False

def update_input(self, context):
    if self["index"]:
        current_index = self["index"]
        input_index = self["input_index"]

        if input_index >= current_index:
            self["input_index"] = 0
    else:
        self["input_index"] = 0


def filter_beer(self, object):
    return not object.beer.is_beer_mat

default_shader = '''
#include "Pipelines/NPR_Pipeline.glsl"

uniform vec4 input_color = vec4(1.0, 0.0, 1.0, 1.0);

void COMMON_PIXEL_SHADER(Surface S, inout PixelOutput PO)
{
    PO.color = input_color;
}
'''

class Blends(Enum):
    DEFAULT = 1
    ADD = 2
    SUBTRACT = 3
    MULTIPLY = 4
    DIVIDE = 5
    SCREEN = 6
    OVERLAY = 7
    DIFFERENCE = 8
    LIGHTEN = 9 
    DARKEN = 10
    DODGE = 11
    BURN = 12

def blend_enums():
    enum = []
    for blend_mode in Blends:
        enum.append((blend_mode.name, blend_mode.name.capitalize(), ""))
    return enum

def input_layer_enums(index):
    enum = []
    i = 0
    if index:
        while i < index:
            if i == 0:
                enum.append(("LAYER0", "None", "Default input method"))
            else: 
                enum.append(("LAYER" + i, "Layer " + i, ""))
            i = i+1
    else: 
        enum.append(("LAYER0", "None", "Default input method"))
    return enum

def layer_index_to_enum(index):
    return str("LAYER" + index)

def layer_enum_to_index(enum):
    layer_index = enum.lstrip("LAYER")
    return int(layer_index)

def get_prefix(index):
    return "beergen" + str(index)

def get_blend(blend):
    if blend is Blends.DEFAULT:
        return "blend_default"
    if blend is Blends.ADD:
        return "blend_add"
    elif blend is Blends.SUBTRACT:
        return "blend_subtract"
    elif blend is Blends.MULTIPLY:
        return "blend_multiply"
    elif blend is Blends.DIVIDE:
        return "blend_divide"
    elif blend is Blends.SCREEN:
        return "blend_screen"
    elif blend is Blends.OVERLAY:
        return "blend_overlay"
    elif blend is Blends.DIFFERENCE:
        return "blend_difference"
    elif blend is Blends.LIGHTEN:
        return "blend_lighten"
    elif blend is Blends.DARKEN:
        return "blend_darken"
    elif blend is Blends.DODGE:
        return "blend_dodge"
    elif blend is Blends.BURN:
        return "blend_burn"

#using mix functions from blender/source/blender/gpu/shaders/material/gpu_shader_material_mix_rgb.glsl    
def get_blend_source(blend):
    if blend is Blends.DEFAULT:
        return '''
void blend_default(inout PixelOutput base, in PixelOutput blending){
    base.line_color = alpha_blend(base.color, blending.line_color);
    base.line_width = blending.line_width;
    base.color = alpha_blend(base.color, blending.color);
}
        '''
    elif blend is Blends.ADD:
        return '''
void mix_add(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    outcol = mix(col1, col1 + col2, fac);
    outcol.a = col1.a;
    }

void blend_add(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_add(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_add(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.SUBTRACT:
        return '''
void mix_sub(float fac, vec4 col1, vec4 col2, out vec4 outcol){
  fac = clamp(fac, 0.0, 1.0);
  outcol = mix(col1, col1 - col2, fac);
  outcol.a = col1.a;
}

void blend_subtract(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_sub(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_sub(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.MULTIPLY:
        return '''
void mix_mult(float fac, vec4 col1, vec4 col2, out vec4 outcol){
  fac = clamp(fac, 0.0, 1.0);
  outcol = mix(col1, col1 * col2, fac);
  outcol.a = col1.a;
}

void blend_multiply(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_mult(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_mult(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.DIVIDE:
        return '''
void mix_div(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    float facm = 1.0 - fac;

    outcol = col1;

    if (col2.r != 0.0) {
        outcol.r = facm * outcol.r + fac * outcol.r / col2.r;
    }
    if (col2.g != 0.0) {
        outcol.g = facm * outcol.g + fac * outcol.g / col2.g;
    }
    if (col2.b != 0.0) {
        outcol.b = facm * outcol.b + fac * outcol.b / col2.b;
    }
}

void blend_divide(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_div(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_div(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.SCREEN:
        return '''
void mix_screen(float fac, vec4 col1, vec4 col2, out vec4 outcol){
  fac = clamp(fac, 0.0, 1.0);
  float facm = 1.0 - fac;

  outcol = vec4(1.0) - (vec4(facm) + fac * (vec4(1.0) - col2)) * (vec4(1.0) - col1);
  outcol.a = col1.a;
}

void blend_screen(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_screen(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_screen(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.OVERLAY:
        return '''
void mix_overlay(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    float facm = 1.0 - fac;

    outcol = col1;

    if (outcol.r < 0.5) {
        outcol.r *= facm + 2.0 * fac * col2.r;
    }
    else {
        outcol.r = 1.0 - (facm + 2.0 * fac * (1.0 - col2.r)) * (1.0 - outcol.r);
    }

    if (outcol.g < 0.5) {
        outcol.g *= facm + 2.0 * fac * col2.g;
    }
    else {
        outcol.g = 1.0 - (facm + 2.0 * fac * (1.0 - col2.g)) * (1.0 - outcol.g);
    }

    if (outcol.b < 0.5) {
        outcol.b *= facm + 2.0 * fac * col2.b;
    }
    else {
        outcol.b = 1.0 - (facm + 2.0 * fac * (1.0 - col2.b)) * (1.0 - outcol.b);
    }
    }

void blend_overlay(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_overlay(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_overlay(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.DIFFERENCE:
        return '''
void mix_diff(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    outcol = mix(col1, abs(col1 - col2), fac);
    outcol.a = col1.a;
}

void blend_difference(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_diff(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_diff(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.LIGHTEN:
        return '''
void mix_light(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    outcol.rgb = mix(col1.rgb, max(col1.rgb, col2.rgb), fac);
    outcol.a = col1.a;
}

void blend_lighten(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_light(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_light(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.DARKEN:
        return '''
void mix_dark(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    outcol.rgb = mix(col1.rgb, min(col1.rgb, col2.rgb), fac);
    outcol.a = col1.a;
}

void blend_darken(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_dark(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_dark(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.DODGE:
        return '''
void mix_dodge(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    outcol = col1;

    if (outcol.r != 0.0) {
        float tmp = 1.0 - fac * col2.r;
        if (tmp <= 0.0) {
        outcol.r = 1.0;
        }
        else if ((tmp = outcol.r / tmp) > 1.0) {
        outcol.r = 1.0;
        }
        else {
        outcol.r = tmp;
        }
    }
    if (outcol.g != 0.0) {
        float tmp = 1.0 - fac * col2.g;
        if (tmp <= 0.0) {
        outcol.g = 1.0;
        }
        else if ((tmp = outcol.g / tmp) > 1.0) {
        outcol.g = 1.0;
        }
        else {
        outcol.g = tmp;
        }
    }
    if (outcol.b != 0.0) {
        float tmp = 1.0 - fac * col2.b;
        if (tmp <= 0.0) {
        outcol.b = 1.0;
        }
        else if ((tmp = outcol.b / tmp) > 1.0) {
        outcol.b = 1.0;
        }
        else {
        outcol.b = tmp;
        }
    }
}

void blend_dodge(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_dodge(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_dodge(blending.color.a, base.color, blending.color, base.color);
}
        '''
    elif blend is Blends.BURN:
        return '''
void mix_burn(float fac, vec4 col1, vec4 col2, out vec4 outcol){
    fac = clamp(fac, 0.0, 1.0);
    float tmp, facm = 1.0 - fac;

    outcol = col1;

    tmp = facm + fac * col2.r;
    if (tmp <= 0.0) {
        outcol.r = 0.0;
    }
    else if ((tmp = (1.0 - (1.0 - outcol.r) / tmp)) < 0.0) {
        outcol.r = 0.0;
    }
    else if (tmp > 1.0) {
        outcol.r = 1.0;
    }
    else {
        outcol.r = tmp;
    }

    tmp = facm + fac * col2.g;
    if (tmp <= 0.0) {
        outcol.g = 0.0;
    }
    else if ((tmp = (1.0 - (1.0 - outcol.g) / tmp)) < 0.0) {
        outcol.g = 0.0;
    }
    else if (tmp > 1.0) {
        outcol.g = 1.0;
    }
    else {
        outcol.g = tmp;
    }

    tmp = facm + fac * col2.b;
    if (tmp <= 0.0) {
        outcol.b = 0.0;
    }
    else if ((tmp = (1.0 - (1.0 - outcol.b) / tmp)) < 0.0) {
        outcol.b = 0.0;
    }
    else if (tmp > 1.0) {
        outcol.b = 1.0;
    }
    else {
        outcol.b = tmp;
    }
}

void blend_burn(inout PixelOutput base, in PixelOutput blending){
    base.line_width = blending.line_width;
    mix_burn(blending.line_color.a, base.color, blending.line_color, base.line_color);

    mix_burn(blending.color.a, base.color, blending.color, base.color);
}
        '''

def lex_passes(token_generator):

    tokens = list(token_generator)
    r_tokens = reversed(tokens)
    nu_tokens = []
    mu_tokens = []

    dot_flag = False
    name_flag = False
    type_flag = False
    function_flag = False
    comment_flag = False
    declared_functions = []

    for ttype, value in r_tokens:
        ptype = str(ttype)
        if str(ttype) == "Token.Name":
            if function_flag:
                ptype = "Token.Name.Function"
            if not name_flag:
                name_flag = True
            else: 
                ptype = "Token.Keyword.Type"
        elif str(ttype) != "Token.Text" and str(ttype) != "Token.Comment":
            name_flag = False
            if str(value) == "(":
                function_flag = True
            else:
                function_flag = False
        nu_tokens.append((ptype, value))
    nu_tokens.reverse()
    tokens = nu_tokens.copy()
    
    for ttype, value in tokens:
        ptype = str(ttype)
        if comment_flag:
            if '\n' in str(value) or '\r' in str(value):
                comment_flag = False
            else:
                ptype = "Token.Comment"
        else:
            if str(value) == "#":
                comment_flag = True
            
            if dot_flag:
                if str(ttype) != "Token.Operator" and str(ttype) != "Token.Punctuation":
                    ptype = "Token.Other"
                else:
                    dot_flag = False
            if str(value) == ".":
                dot_flag = True

            if str(ttype) == "Token.Keyword.Type":
                type_flag = True
            else:
                if str(ttype) == "Token.Name.Function":
                    if type_flag:
                        declared_functions.append(value)
                    else:
                        if str(value) not in declared_functions:
                            ptype = "Token.Generic"
                elif str(ttype) != "Token.Text" and str(ttype) != "Token.Comment":
                    type_flag = False
        print(ptype, value)
        mu_tokens.append((ptype, value))

    return mu_tokens
    
def compile_layer_source(layers):
    compiled_source = []
    compiled_source.append('#include "Pipelines/NPR_Pipeline.glsl"' + '\n')
    for layer in layers:
        index = layer.index
        solo_layer = layer.solo_layer
        mute_layer = layer.mute_layer
        masked_layer = layer.masked_layer
        masking_index = layer.masking_index
        input_index = layer.input_index
        material = layer.material
        blend_mode =  layer.blend

        documentation = (
            "\n" + "/*"
            + "\n" + "LAYER INFO = ["
            + "\n" + "layer:" + str(index)
            + "\n" + "solo:" + str(solo_layer)
            + "\n" + "mute:" + str(mute_layer)
            + "\n" + "masked:" + str(masked_layer)
            + "\n" + "m_index:" + str(masking_index)
            + "\n" + "i_index:" + str(input_index)
             + "\n" + "blend_mode:" + str(blend_mode)
            + "\n" + "]"
            + "\n" + "*/" + "\n"
            )

        compiled_source.append(documentation)

        source = material.malt.get_source_path()
        shader = open(source)
        lexer = pygments.lexers.get_lexer_by_name("glsl")
        tokens = pygments.lex(shader.read(), lexer)
        filtered_tokens = lex_passes(tokens)
        for ttype, value in filtered_tokens:
            if str(ttype) == "Token.Name" or str(ttype) == "Token.Name.Function":
                if str(value) != "location":
                    private_mod = ""
                    prefix_suff = "_"
                    if str(value).startswith("_"):
                        private_mod = "_"
                        prefix_suff = ""
                    value = private_mod + get_prefix(index) + prefix_suff + value
            compiled_source.append(value)
    return compiled_source


def compile_function_source(layers):
    compiled_util = []
    compiled_function = []
    used_blendmodes = []

    compiled_function.append("""
        void COMMON_PIXEL_SHADER(Surface S, inout PixelOutput PO)\n
        {\n
            PixelOutput beergen0_layer = PO;\n
            PixelOutput compilation_layer = PO;\n
        """)

    for layer in layers:
        index = layer.index
        solo_layer = layer.solo_layer
        mute_layer = layer.mute_layer
        masked_layer = layer.masked_layer
        masking_index = layer.masking_index
        input_index = layer.input_index
        blend_mode =  layer.blend
        blend_mode = Blends[layer.blend]

        if blend_mode not in used_blendmodes:
            used_blendmodes.append(blend_mode)

        compiled_function.append("PixelOutput " + get_prefix(index) + "_" + "layer = " + get_prefix(input_index) + "_" + "layer;" + "\n")
        compiled_function.append(get_prefix(index) + "_" + "COMMON_PIXEL_SHADER(S, " + get_prefix(index) + "_" + "layer);" + "\n")
        if masked_layer: 
            compiled_function.append(get_prefix(index) + "_" + "layer.color *= " + get_prefix(masking_index) + "_" + "layer.g;" + "\n")
        if not mute_layer:
            if solo_layer:
                compiled_function.append("compilation_layer = " + get_prefix(index) + "_" + "layer;" + "\n")
            else: 
                compiled_function.append(get_blend(blend_mode) + "(compilation_layer, " + get_prefix(index) + "_" + "layer);" + "\n")
        
    compiled_function.append("""
            PO = compilation_layer;\n
        }\n
        
        """)

    for used_blend in used_blendmodes:
        compiled_util.append(get_blend_source(used_blend))

    return compiled_util + compiled_function

def compile_full_source(layers):
    print("compiling")
    print("compiling layer shaders")
    layer_source = compile_layer_source(layers)
    print("compiling function")
    function_source = compile_function_source(layers)
    print("compiling complete")
    return layer_source + function_source


class BeerLayer(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(update=update_index, default=1)
    solo_layer : bpy.props.BoolProperty(name="Solo", default=False)
    mute_layer : bpy.props.BoolProperty(name="Mute", default=False)
    masked_layer : bpy.props.BoolProperty(name="Mask", default=False)
    masking_index : bpy.props.IntProperty(name="Masking Layer", update=update_masking, default=0)
    input_index : bpy.props.IntProperty(name="Input Layer", update=update_input, default=0)
    material : bpy.props.PointerProperty(type=bpy.types.Material, poll=filter_beer)
    blend : bpy.props.EnumProperty(name="Blend Mode", items=blend_enums(), default="DEFAULT")

    def mat_setup(self, material):
        self["material"] = material

    def draw_ui(self, layout):
        row = layout.row() 
        row.template_ID(self, "material", new="material.new")
        row = layout.row()
        row.prop(self, "solo_layer")
        row.prop(self, "mute_layer")
        row.prop(self, "masked_layer")
        row = layout.row()
        row.prop(self, "input_index")
        if self.masked_layer:
            row = layout.row()
            row.prop(self, "masking_index")
        row = layout.row()
        row.prop(self, "blend")

        if self.material:
            row = layout.row()
            self.material.malt.draw_ui(layout, 'mesh', self.material.malt_parameters)
            row = layout.row()
            row.operator('beer.compile_layers', text='Update BEER Material')

    def reindex(self, index):
        self["index"] = index+1

class BeerMaterial(bpy.types.PropertyGroup):
    layers : bpy.props.CollectionProperty(name="Shader", type=BeerLayer)
    material : bpy.props.PointerProperty(type=bpy.types.Material)
    is_beer_mat : bpy.props.BoolProperty(name="BEER Material", default=False)
    shader_index : bpy.props.IntProperty(name="BEER Material", default=0)

    def draw_ui(self, layout):
        
        row = layout.row() 
        row.operator('beer.compile_layers', text='Update BEER Material')
        row = layout.row()

        row.template_list("BEER_UL_LayerList", "", self, "layers", self, "shader_index")

        col = row.column(align=True)

        col.operator("beer.new_layer", icon='ADD', text="")
        col.operator("beer.delete_layer", icon='REMOVE', text="")

        col.separator()

        col.operator("beer.move_layer", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("beer.move_layer", icon='TRIA_DOWN', text="").direction = 'DOWN'

        row = layout.row() 
        row.operator('beer.new_layer', text='New Layer')
        row = layout.row() 

        if self.layers:
            self.layers[self.shader_index].draw_ui(layout)

#File handling code from BlenderMalt/MaltNodes.py
    def get_generated_source_dir(self):
        import os, tempfile
        base_path = tempfile.gettempdir()
        if bpy.context.blend_data.is_saved:
            base_path = bpy.path.abspath('//')
        return os.path.join(base_path,'malt-shaders')

    def get_generated_source_path(self):
        import os
        file_prefix = 'temp'
        if bpy.context.blend_data.is_saved:  
            file_prefix = bpy.path.basename(bpy.context.blend_data.filepath).split('.')[0]
        return os.path.join(self.get_generated_source_dir(),'{}-{}{}'.format(file_prefix, self["material"].name, ".mesh.glsl"))

    def update_file(self, source):
        source_dir = self.get_generated_source_dir()
        source_path = self.get_generated_source_path()
        import pathlib
        pathlib.Path(source_dir).mkdir(parents=True, exist_ok=True)
        with open(source_path,'w') as f:
            f.write(source)
        self.copy_properties()
        return source_path
        
    def mat_setup(self, material ):
        self["material"] = material
        self["is_beer_mat"] = True
        material.malt.shader_source = self.update_file(default_shader)

    def index_layers(self):
        index = 0
        while index < len(self.layers):
            self.layers[index].reindex(index)
            name = "Layer " + str(self.layers[index].index)
            if self.layers[index].material:
                name = name + " - " + str(self.layers[index].material.name)
            self.layers[index].name = name
            index = index + 1

    def copy_layer_property(self, layer):
        overrides = {}
        resources = {}
        layer_parameters = layer.material.malt.parameters.get_parameters(resources, overrides)
        for key, value in layer_parameters.items():
            private_mod = ""
            prefix_suff = "_"
            if str(key).startswith("_"):
                private_mod = "_"
                prefix_suff = ""
            new_key = private_mod + get_prefix(layer["index"]) + prefix_suff + key
            if new_key in self.material.malt.parameters: 
                self.material.malt.parameters[new_key] = value

    def copy_properties(self):
        for layer in self.layers:
            self.copy_layer_property(layer)

class BeerMaterialOperator(bpy.types.Operator):
    bl_idname = "material.new_beer"
    bl_label = "New BEER Material"

    def execute(self, context):
        import os
        ob = context.object
        material_beer = bpy.data.materials.new(name = "BEER Material")
        material_beer.beer.mat_setup(material_beer)
        ob.data.materials.append(material_beer)
        ob.active_material = material_beer

    def invoke (self, context, event):
        self.execute(context)
        return {'RUNNING_MODAL'}

class BEER_UL_LayerList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


class LayerNewOperator(bpy.types.Operator):
    """Add a new item to the list."""

    bl_idname = "beer.new_layer"
    bl_label = "Add a new layer"

    def execute(self, context):
        ob = context.object
        ob.active_material.beer.layers.add()
        ob.active_material.beer.index_layers()

        return{'FINISHED'}


class LayerDeleteOperatorOperator(bpy.types.Operator):
    """Delete the selected item from the list."""

    bl_idname = "beer.delete_layer"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.object.active_material.beer.layers

    def execute(self, context):
        layers = context.object.active_material.beer.layers
        shader_index =  context.object.active_material.beer.shader_index

        
        layers.remove(shader_index)
        context.object.active_material.beer.shader_index = min(max(0, shader_index - 1), len(layers) - 1)
        context.object.active_material.beer.index_layers()

        return{'FINISHED'}


class LayerMoveOperator(bpy.types.Operator):
    """Move an item in the list."""

    bl_idname = "beer.move_layer"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))
    @classmethod
    def poll(cls, context):
        return context.object.active_material.beer.layers

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """

        index = context.object.active_material.beer.shader_index
        list_length = len(context.object.active_material.beer.layers) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)

        context.object.active_material.beer.shader_index = max(0, min(new_index, list_length))

    def execute(self, context):
        layers = context.object.active_material.beer.layers
        index = context.object.active_material.beer.shader_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        layers.move(neighbor, index)
        self.move_index(context)
        context.object.active_material.beer.index_layers()

        return{'FINISHED'}

class CompileLayerOperator(bpy.types.Operator):
    bl_idname = "beer.compile_layers"
    bl_label = "Update the BEER Material."

    @classmethod
    def poll(cls, context):
        layers = context.object.active_material.beer.layers
        if layers:
            safe = True
            for layer in layers:
                if layer.material:
                    layer_safe = layer.material.malt.get_source_path().endswith('.mesh.glsl')
                    layer_safe = layer_safe and layer.material.malt.compiler_error == ''
                    safe = safe and layer_safe
                else: 
                    return False
            return safe
        return False

    def execute(self, context):
        beer_mat = context.object.active_material.beer
        layers = beer_mat.layers
        compiled_source = "".join(compile_full_source(layers))
        print("saving source")
        beer_mat.update_file(compiled_source)
        print("finished")
        return{'FINISHED'}


def register():
    bpy.utils.register_class(BeerMaterialOperator)
    bpy.utils.register_class(CompileLayerOperator)
    bpy.utils.register_class(BEER_UL_LayerList)
    bpy.utils.register_class(LayerNewOperator)
    bpy.utils.register_class(LayerDeleteOperatorOperator)
    bpy.utils.register_class(LayerMoveOperator)
    bpy.utils.register_class(BeerLayer)
    bpy.utils.register_class(BeerMaterial)
    bpy.types.Material.beer = bpy.props.PointerProperty(type=BeerMaterial)


def unregister():
    del bpy.types.Material.beer
    bpy.utils.unregister_class(BeerMaterial)
    bpy.utils.unregister_class(BeerLayer)
    bpy.utils.unregister_class(LayerMoveOperator)
    bpy.utils.unregister_class(LayerDeleteOperatorOperator)
    bpy.utils.unregister_class(LayerNewOperator)
    bpy.utils.unregister_class(BEER_UL_LayerList)
    bpy.utils.unregister_class(CompileLayerOperator)
    bpy.utils.unregister_class(BeerMaterialOperator)