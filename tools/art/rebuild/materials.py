"""Portable PBR materials for Character01. Colours are specified in sRGB."""
import bpy

def linear(c):
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)

def base(name, color, rough=.5, metallic=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    m.diffuse_color=(*linear(color),1)
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Specular IOR Level'].default_value=.32
    return m,bs

def palette():
    out={}
    skin,bs=base('Skin | cool slate',(.475,.482,.565),.48)
    bs.inputs['Subsurface Weight'].default_value=.065
    bs.inputs['Subsurface Radius'].default_value=(.12,.06,.035)
    nodes=skin.node_tree.nodes;links=skin.node_tree.links
    attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='Complexion'
    links.new(attr.outputs['Color'],bs.inputs['Base Color'])
    tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=850;tex.inputs['Detail'].default_value=2
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00018
    links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    out['skin']=skin
    for key,name,col,rough in [('hair','Hair | ivory silver',(.83,.845,.87),.38),('horn','Horns | dark keratin',(.095,.09,.13),.36),('cloth','Cloth | warm ivory',(.76,.73,.65),.77),('cord','Cord | charcoal',(.075,.068,.082),.77),('lash','Lashes | ink',(.04,.035,.065),.56),('brow','Eyebrows | soft ivory',(.77,.79,.84),.56),('mouth','Mouth | shadow',(.115,.075,.125),.59),('teeth','Teeth | ivory',(.79,.77,.68),.3),('nail','Nails | charcoal violet',(.20,.18,.255),.35),('sclera','Sclera | soft white',(.73,.76,.8),.15),('inner_ear','Ears | inner tone',(.35,.335,.435),.57)]:
        m,bs=base(name,col,rough);out[key]=m
        if key=='hair':
            bs.inputs['Anisotropic'].default_value=.35
            nodes=m.node_tree.nodes;links=m.node_tree.links
            uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(95,2,1);links.new(uv.outputs['UV'],mapping.inputs[0])
            tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1;tex.inputs['Detail'].default_value=2;links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
            ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=(*linear((.52,.55,.62)),1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*linear((.88,.9,.94)),1)
            links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color'])
            bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.00035;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
        if key=='cloth':
            bs.inputs['Sheen Weight'].default_value=.2
            nodes=m.node_tree.nodes;links=m.node_tree.links
            noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1250;noise.inputs['Detail'].default_value=1
            bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=.00022;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
    return out
