import bpy, pathlib, json
from collections import Counter
print("BLENDER_VERSION", bpy.app.version_string)
for path in sorted(pathlib.Path("Textures_files").glob("*.blend")):
    print("\n=== SCENE",path.name,"===")
    try: bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    except Exception as e:
        print("OPEN_ERROR",repr(e)); continue
    print("SCENES",[(s.name,len(s.objects),s.camera.name if s.camera else None) for s in bpy.data.scenes])
    print("OBJECTS", [(o.name,o.type,tuple(round(v,2) for v in o.dimensions),len(o.data.polygons) if o.type=='MESH' else 0) for o in bpy.data.objects][:100])
    print("MATERIALS",[(m.name,m.use_nodes,len(m.node_tree.nodes) if m.use_nodes else 0) for m in bpy.data.materials][:100])
    print("IMAGES",[(im.name,im.filepath,im.packed_file is not None) for im in bpy.data.images][:40])
    print("RENDER",bpy.context.scene.render.engine,bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y)
    for o in list(bpy.data.objects)[:20]:
        if o.type == 'MESH':
            print("MESH",o.name,"slots",[s.name for s in o.data.materials],"UV",list(o.data.uv_layers.keys()))
print("\nFINISHED")