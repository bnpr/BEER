# Blender Extended Expressive Renderer

Blender Extended Expressive Renderer (BEER) is a free and open source realtime non-photoreal (NPR) rendering engine with Malt as the backend. The main feature of BEER is the ability to extend the rendering capability from the ease of adding custom shaders to a customizable shader graph.

BEER will have a layer stack UI (like in raster painting software). There will be a list of shaders provided by Malt's shader library. 

There will be 3 interfaces to create and to assemble shaders for BEER:
1. GLSL Code via Malt
2. Malt nodes (Code like node tree)
3. Layer stack (BEER UI)

Advanced users can create custom rendering pipelines optimize for their production.

Development update will be posted at: https://blendernpr.org/beer/

# Dependencies
Installation of the *BlenderBeer* addon for *Blender* currently requires *prior* installation of:
1. [BlenderMalt](https://github.com/bnpr/Malt)
2. [Pygments](https://github.com/pygments/pygments) as a module for *Blender.* Future releases will have a stripped down version of *Pygments* included.

# Instructions
After installation, switch the render-engine to *Malt*. A new panel will be accessible in the 3D view window. 
New *Beer* materials can be created in the new panel. New *Beer* layers can be created and linked to new or preexisting *Malt* materials.
To compile layers into a single *Malt* material, make sure that all *Malt* materials compile without errors, and click the "Update BEER Material* button.

# Current Limitations
*Beer* materials will not automatically compile when layers are moved or changed. The "Update BEER Material" must be used to update the *Beer* material and the linked *Malt* material.
The *Beer* material uniforms can only be updated in realtime using the *Malt* panel. To propogate layer properties to the main material, the "Update BEER Material" button must currently be used. Automatic linking of the two will be available in the next update.