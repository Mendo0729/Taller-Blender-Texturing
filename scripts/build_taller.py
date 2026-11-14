import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path.cwd()
SOURCES = ROOT / "Textures_files"
MAPS = ROOT / "tank_texture" / "tank_texture"
OUT = ROOT / "entrega"
OUT.mkdir(parents=True, exist_ok=True)

def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return True
    return False

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def remove_old_studio():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in list(bpy.data.objects):
        if ob.type in {'CAMERA', 'LIGHT'}:
            bpy.data.objects.remove(ob, do_unlink=True)

def bsdf_material(name, rgb, metallic=0, roughness=.5, coat=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    nt = mat.node_tree
    p = nt.nodes.get("Principled BSDF")
    set_input(p, ["Base Color"], (*rgb, 1))
    set_input(p, ["Metallic"], metallic)
    set_input(p, ["Roughness"], roughness)
    set_input(p, ["Coat Weight", "Clearcoat", "Coat"], coat)
    return mat

def shader(mat):
    nt = mat.node_tree
    return nt, nt.nodes.get("Principled BSDF")

def nodes_image(nt, path, label, noncolor=False, box=False, blend=.2):
    im = bpy.data.images.load(str(Path(path).resolve()), check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    node = nt.nodes.new("ShaderNodeTexImage")
    node.label = label
    node.image = im
    if box:
        node.projection = 'BOX'
        node.projection_blend = blend
    return node

def mapping_for(nt, link, box=True, scale=(1,1,1)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-780, 0)
    m = nt.nodes.new("ShaderNodeMapping")
    m.location = (-570, 0)
    m.inputs["Scale"].default_value = scale
    link.new(tc.outputs["Object" if box else "UV"], m.inputs["Vector"])
    return m

def image_material(name, image_path, box=False, scale=(1,1,1), roughness=.55):
    mat = bsdf_material(name, (.60,.60,.60), roughness=roughness)
    nt, p = shader(mat)
    m = mapping_for(nt, nt.links, box=box, scale=scale)
    im = nodes_image(nt, image_path, "Imagen original", box=box)
    im.location = (-280, 20)
    nt.links.new(m.outputs["Vector"], im.inputs["Vector"])
    nt.links.new(im.outputs["Color"], p.inputs["Base Color"])
    p.location = (80,0)
    return mat

def procedural_camo(name="Camuflaje procedural", colors=None):
    if colors is None:
        colors=((.115,.18,.067,1),(.30,.34,.145,1),(.055,.077,.046,1))
    mat=bsdf_material(name, colors[0][:3], roughness=.75)
    nt,p=shader(mat)
    tc=nt.nodes.new("ShaderNodeTexCoord")
    tc.location=(-920,0)
    mapping=nt.nodes.new("ShaderNodeMapping")
    mapping.location=(-710,0)
    mapping.inputs["Scale"].default_value=(1.6,1.6,1.6)
    nt.links.new(tc.outputs["Object"],mapping.inputs["Vector"])
    n1=nt.nodes.new("ShaderNodeTexNoise");n1.location=(-480,220)
    n1.inputs["Scale"].default_value=2.0
    set_input(n1, ["Roughness"], 0.0)
    nt.links.new(mapping.outputs["Vector"],n1.inputs["Vector"])
    r1=nt.nodes.new("ShaderNodeValToRGB");r1.location=(-255,240)
    r1.color_ramp.interpolation='CONSTANT'
    r1.color_ramp.elements[0].position=.22
    r1.color_ramp.elements[0].color=colors[0]
    r1.color_ramp.elements[1].position=.50
    r1.color_ramp.elements[1].color=colors[1]
    nt.links.new(n1.outputs["Fac"],r1.inputs["Fac"])
    n2=nt.nodes.new("ShaderNodeTexNoise");n2.location=(-470,-210)
    n2.inputs["Scale"].default_value=2.8
    set_input(n2, ["Roughness"], 0.0)
    nt.links.new(mapping.outputs["Vector"],n2.inputs["Vector"])
    r2=nt.nodes.new("ShaderNodeValToRGB");r2.location=(-255,-185)
    r2.color_ramp.interpolation='CONSTANT'
    r2.color_ramp.elements[0].position=.35
    r2.color_ramp.elements[1].position=.43
    nt.links.new(n2.outputs["Fac"],r2.inputs["Fac"])
    mix=nt.nodes.new("ShaderNodeMixRGB");mix.location=(-15,140)
    mix.blend_type='MIX'
    mix.inputs[2].default_value=colors[2]
    nt.links.new(r1.outputs["Color"],mix.inputs[1])
    nt.links.new(r2.outputs["Color"],mix.inputs[0])
    nt.links.new(mix.outputs["Color"],p.inputs["Base Color"])
    bump=nt.nodes.new("ShaderNodeBump")
    bump.location=(-10,-170)
    bump.inputs["Strength"].default_value=.10
    bump.inputs["Distance"].default_value=.035
    nt.links.new(n1.outputs["Fac"],bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"],p.inputs["Normal"])
    p.location=(250,70)
    return mat

def pbr_material(name, color_file, rough_file=None, normal_file=None, metal_file=None,
                 metal=.35, rough=.55, tint=None):
    mat=bsdf_material(name, (.32,.35,.25), metallic=metal, roughness=rough)
    nt,p=shader(mat)
    mp=mapping_for(nt, nt.links, box=True, scale=(1.75,1.75,1.75))
    albedo=nodes_image(nt, MAPS/color_file, "Albedo", box=True)
    albedo.location=(-320,330)
    nt.links.new(mp.outputs["Vector"],albedo.inputs["Vector"])
    if tint:
        mix=nt.nodes.new("ShaderNodeMixRGB");mix.blend_type='MULTIPLY';mix.location=(-70,320)
        mix.inputs[0].default_value=.78
        mix.inputs[2].default_value=(*tint,1)
        nt.links.new(albedo.outputs["Color"],mix.inputs[1])
        nt.links.new(mix.outputs["Color"],p.inputs["Base Color"])
    else:
        nt.links.new(albedo.outputs["Color"],p.inputs["Base Color"])
    if rough_file:
        tex=nodes_image(nt, MAPS/rough_file, "Rugosidad", noncolor=True, box=True)
        tex.location=(-320,0)
        nt.links.new(mp.outputs["Vector"],tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"],p.inputs["Roughness"])
    if metal_file:
        tex=nodes_image(nt, MAPS/metal_file, "Metallic", noncolor=True, box=True)
        tex.location=(-320,-200)
        nt.links.new(mp.outputs["Vector"],tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"],p.inputs["Metallic"])
    if normal_file:
        tex=nodes_image(nt, MAPS/normal_file, "Normal", noncolor=True, box=True)
        tex.location=(-310,-390)
        tex.projection='BOX'
        nt.links.new(mp.outputs["Vector"],tex.inputs["Vector"])
        normal=nt.nodes.new("ShaderNodeNormalMap");normal.location=(-40,-350)
        normal.inputs["Strength"].default_value=.60
        nt.links.new(tex.outputs["Color"],normal.inputs["Color"])
        nt.links.new(normal.outputs["Normal"],p.inputs["Normal"])
    p.location=(180,100)
    return mat

def assign(obj, mat):
    if obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    elif obj.type == 'CURVE':
        obj.data.materials.clear()
        obj.data.materials.append(mat)

def look_at(obj, point):
    direction=Vector(point)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def lights_and_camera(target=(0,0,1), cam_pos=(6,-11,8), ortho=11.5):
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=24
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1000
    scene.render.resolution_y=650
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.camera=None
    world=bpy.data.worlds.new("Entorno estudio")
    scene.world=world
    world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.19,.21,.25,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=.65
    cam_data=bpy.data.cameras.new("Cámara entrega")
    cam=bpy.data.objects.new("Cámara entrega",cam_data)
    scene.collection.objects.link(cam)
    cam.location=cam_pos;look_at(cam,target)
    cam.data.type='ORTHO';cam.data.ortho_scale=ortho
    scene.camera=cam
    for name,loc,power,size,color in [
      ("Luz principal",(-3,-4,9),1200,7,(1,.92,.82)),
      ("Luz de relleno",(5,2,8),950,6,(.70,.81,1)),
      ("Luz de contorno",(0,6,7),1100,5,(1,1,1))]:
        data=bpy.data.lights.new(name,"AREA")
        data.energy=power;data.shape='DISK';data.size=size;data.color=color
        obj=bpy.data.objects.new(name,data)
        scene.collection.objects.link(obj)
        obj.location=loc;look_at(obj,target)
    return cam

def ground(height=-.05):
    mat=bsdf_material("Plataforma grafito",(.075,.085,.105),roughness=.84)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,height))
    ob=bpy.context.object;ob.name="Plataforma de estudio";assign(ob,mat)
    return ob

def label(body, position, cam, size=.32):
    cu=bpy.data.curves.new("Texto",type='FONT');cu.body=body
    cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER'
    cu.extrude=.0004
    obj=bpy.data.objects.new("Etiqueta - "+body,cu)
    bpy.context.scene.collection.objects.link(obj)
    obj.location=position
    obj.rotation_euler=cam.rotation_euler
    assign(obj,bsdf_material("Blanco roto",(.82,.87,.9),roughness=.98))
    return obj

def save_and_render(label_name, title):
    scene=bpy.context.scene
    path=OUT/(label_name+".blend")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()), compress=True)
    scene.render.filepath=str((OUT/(label_name+".png")).resolve())
    bpy.ops.render.render(write_still=True)
    meshes=[o for o in bpy.data.objects if o.type=='MESH']
    print("ENTREGA",title,"blend",path.name,"meshes",len(meshes),"materials",len(bpy.data.materials),
          "packed_images",len([i for i in bpy.data.images if i.packed_file]))

def split_cube_material():
    verts=[]
    for z in [-.72,0,.72]:
        verts.extend([(-.75,-.75,z),(.75,-.75,z),(.75,.75,z),(-.75,.75,z)])
    faces=[(3,2,1,0),(8,9,10,11)]
    for ring in [0,1]:
        for i in range(4):
            ni=(i+1)%4
            faces.append((ring*4+i,ring*4+ni,(ring+1)*4+ni,(ring+1)*4+i))
    mesh=bpy.data.meshes.new("Cubo con Loop Cut")
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new("Cubo con dos materiales",mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location=(4.25,0,.99)
    olive=bsdf_material("Verde militar mate",(.24,.32,.115),roughness=.79)
    gold=bsdf_material("Mostaza satinado",(.69,.40,.08),metallic=.28,roughness=.33)
    mesh.materials.append(olive);mesh.materials.append(gold)
    for face in mesh.polygons: face.material_index=1 if face.center.z>0 else 0
    bevel=ob.modifiers.new("Bisel de bordes","BEVEL");bevel.width=.045;bevel.segments=3
    normal=ob.modifiers.new("Normales ponderadas","WEIGHTED_NORMAL")
    return ob

def make_gallery():
    bpy.ops.wm.open_mainfile(filepath=str((SOURCES/"spheres.blend").resolve()))
    remove_old_studio()
    cubes=sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda x:x.name)
    for o,x in zip(cubes,[-3.8,-1.4,1.0]):
        o.location=(x,0,.95);o.scale=(1,1,1)
        for face in o.data.polygons: face.use_smooth=True
    # Se conserva la fibra de carbono del archivo original y se incorporan propiedades adicionales.
    carbon=bpy.data.materials.get("Carbon Fiber")
    if carbon and carbon.use_nodes:
        p=carbon.node_tree.nodes.get("Principled BSDF")
        if p:
            set_input(p,["Coat Weight","Clearcoat","Coat"],.67)
            set_input(p,["Roughness"],.24)
    split_cube_material()
    ground(-.06)
    cam=lights_and_camera(target=(0,0,1.1),cam_pos=(5,-12,8),ortho=12.7)
    for x,s in [(-3.8,"DIELÉCTRICO"),(-1.4,"METÁLICO"),(1.0,"FIBRA DE CARBONO"),(4.25,"DOS MATERIALES")]:
        pass  # Los nombres de los materiales se detallan en LEEME.md
    label("01 / MATERIALES Y PROPIEDADES",(0,1.5,3.60),cam,.44)
    save_and_render("01_materiales","Color base, metálico, rugosidad, clearcoat, material por cara")

def make_camo():
    bpy.ops.wm.open_mainfile(filepath=str((SOURCES/"Camo.blend").resolve()))
    remove_old_studio()
    for o in [o for o in bpy.data.objects if o.type=='MESH']:
        bpy.data.objects.remove(o,do_unlink=True)
    camomat=procedural_camo()
    colors=((.25,.22,.10,1),(.40,.32,.10,1),(.10,.13,.07,1))
    desert=procedural_camo("Camuflaje bosque y tierra",colors)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=1.0,location=(-2.4,0,1.1))
    sphere=bpy.context.object;sphere.name="Esfera - ruido con rampa constante";assign(sphere,camomat)
    for p in sphere.data.polygons:p.use_smooth=True
    bpy.ops.mesh.primitive_cube_add(size=2,location=(.2,0,1.06))
    cube=bpy.context.object;cube.name="Cubo - patrón de camuflaje alterno";assign(cube,desert)
    bev=cube.modifiers.new("Bisel","BEVEL");bev.width=.12;bev.segments=4
    cube.modifiers.new("Normales ponderadas","WEIGHTED_NORMAL")
    bpy.ops.mesh.primitive_plane_add(size=2.15,location=(3.0,0,.08))
    plate=bpy.context.object;plate.name="Plano - CamoTexture original"
    imat=image_material("Camuflaje PNG usando UV",SOURCES/"CamoTexture.png",box=False,scale=(1,1,1))
    assign(plate,imat)
    ground(-.08)
    cam=lights_and_camera(target=(.0,0,1.0),cam_pos=(5,-11,8),ortho=11.4)
    for x,s in [(-2.4,"NOISE + COLOR RAMP"),(.2,"MEZCLA DE 3 COLORES"),(3,"TEXTURA DE IMAGEN")]:
        pass  # Evitar texto superpuesto sobre la geometria
    label("02 / NODOS Y CAMUFLAJE PROCEDURAL",(0,1.5,3.85),cam,.42)
    save_and_render("02_camuflaje","Noise, ColorRamp, MixRGB, imagen UV")

def make_uv():
    fresh()
    grid=image_material("Cuadrícula de comprobación UV",SOURCES/"ColorGridTexture.png",box=False)
    camouv=image_material("Camuflaje con coordenadas UV",SOURCES/"CamoTexture.png",box=False)
    camobox=image_material("Camuflaje con mapeo objeto BOX",SOURCES/"CamoTexture.png",box=True,scale=(1.8,1.8,1.8))
    for x, mat, nm in [(-3.2,grid,"UV Grid"),(0.0,camouv,"Camo UV"),(3.2,camobox,"Camo Object Box")]:
        bpy.ops.mesh.primitive_cube_add(size=1.8,location=(x,0,1.12))
        cube=bpy.context.object;cube.name=nm;assign(cube,mat)
        # Mantener UV predeterminadas y suavizar solo bordes, no modificar UV.
        bevel=cube.modifiers.new("Bordes","BEVEL");bevel.width=.055;bevel.segments=3
        cube.modifiers.new("Normales ponderadas","WEIGHTED_NORMAL")
    ground(-.03)
    cam=lights_and_camera(target=(0,0,1.0),cam_pos=(6,-11,8),ortho=11.5)
    for x, s in [(-3.2,"CUADRÍCULA UV"),(0,"PROYECCIÓN UV"),(3.2,"OBJECT + BOX")]:
        pass  # Evitar texto superpuesto sobre la geometria
    label("03 / COMPARACIÓN DE COORDENADAS",(0,1.3,3.75),cam,.42)
    save_and_render("03_mapeo_uv","UV, coordenadas de objeto y proyección BOX")

def make_tank():
    bpy.ops.wm.open_mainfile(filepath=str((SOURCES/"Tank.blend").resolve()))
    remove_old_studio()
    # El origen usa codificacion FFMPEG. Reubicar la geometria en una nueva
    # escena evita restricciones del formato de salida heredado.
    old_scene=bpy.context.scene
    new_scene=bpy.data.scenes.new("Tanque - entrega PBR")
    for existing in list(old_scene.objects):
        if existing.type in {'MESH','CURVE'}:
            new_scene.collection.objects.link(existing)
    bpy.context.window.scene=new_scene
    bpy.data.scenes.remove(old_scene)
    body=next(o for o in bpy.data.objects if o.type=='MESH')
    # Materiales PBR basados en todos los mapas suministrados.
    paint=pbr_material("Pintura militar desgastada PBR","Paint_Rusted_1K_albedo.tif",
              "Rusted_1K_roughness.tif","Rusted_1K_normal.tif",
              metal=.22,rough=.65,tint=(.21,.34,.12))
    rusty=pbr_material("Óxido de orugas PBR","Paint_Rusted_1K_albedo.tif",
              "Rusted_1K_roughness.tif","Rusted_1K_normal.tif",metal=.42,rough=.72)
    bronze=pbr_material("Bronce envejecido PBR","BronzeStatue_1K_albedo.tif",
              None,"BronzeStatue_1K_normal.tif",
              "BronzeStatue_1K_metallic.tif",metal=.75,rough=.35)
    body.data.materials.clear()
    for mat in [paint,rusty,bronze]:body.data.materials.append(mat)
    zs=[v.co.z for v in body.data.vertices]
    xmin=min(v.co.x for v in body.data.vertices);xmax=max(v.co.x for v in body.data.vertices)
    zmin=min(zs);zmax=max(zs)
    h=max(zmax-zmin,.01);width=max(xmax-xmin,.01)
    tally=[0,0,0]
    for poly in body.data.polygons:
        zz=(poly.center.z-zmin)/h
        xx=abs(poly.center.x-(xmax+xmin)/2)/width
        if zz<.16 or (xx>.43 and zz<.43):
            index=1
        elif zz>.76 and xx<.23:
            index=2
        else:
            index=0
        poly.material_index=index
        tally[index]+=1
        poly.use_smooth=True
    for ob in bpy.data.objects:
        if ob.type=='CURVE':
            assign(ob,bronze)
    bbox=[body.matrix_world @ Vector(c) for c in body.bound_box]
    center=Vector((sum(p.x for p in bbox)/8,sum(p.y for p in bbox)/8,sum(p.z for p in bbox)/8))
    # Mover el modelo y sus curvas como grupo conservando sus posiciones relativas.
    delta=Vector((-center.x,-center.y,0))
    for ob in bpy.data.objects:
        if ob.type in {'MESH','CURVE'}:ob.location+=delta
    bbox=[body.matrix_world @ Vector(c) for c in body.bound_box]
    low=min(p.z for p in bbox);hi=max(p.z for p in bbox)
    ground(low-.12)
    target=(0,0,(low+hi)/2)
    cam=lights_and_camera(target=target,cam_pos=(5.0,-8.7,5.2),ortho=7.0)
    # Luz extra para destacar volumen de las orugas y cilindros.
    pass  # La toma del tanque se presenta sin titulos 3D
    print("TANK_FACES",tally,"rangeZ",(zmin,zmax),"bbox",(low,hi))
    save_and_render("04_tanque_pbr","Tanque original con pinturas, rugosidad, normal, metallic")

if __name__=="__main__":
    print("START_WORKSHOP Blender",bpy.app.version_string)
    for build in [make_gallery,make_camo,make_uv,make_tank]:
        try: build()
        except Exception:
            import traceback
            traceback.print_exc()
            raise
    print("WORKSHOP_COMPLETED")
