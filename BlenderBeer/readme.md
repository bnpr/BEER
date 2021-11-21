# BlenderBeer

## Panel
[*BeerPanel.py*](BeerPanel.py) is the UI for the *Beer* material and layer system. It currently exists in the 3D view panel, independent of the *Malt* panels.

## Materials

[*BeerMaterial.py*](BeerMaterial.py) contains the material and layer system used by *Beer*. Functionally, *Beer* layers are a *Blender* property group with a pointer to a *Malt* material. *Beer* materials consist both of a linked *Malt* material, as well as a list of *Beer* layers. These layers are dynamically compiled into a *Malt* readable shader file.