import bpy, math, os
from mathutils import Vector

# Nila procedural humanoid prototype. Run:
# blender --background --python create_nila.py
# Exports nila_avatar.glb beside this script.
# This is a base model, not a photoreal scanned human.

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=.45, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return m

skin=mat("Nila skin",(0.66,.39,.29),.5)
hair=mat("Nila dark espresso hair",(.018,.012,.025),.28)
hairshine=mat("Hair sheen",(.07,.045,.1),.3)
blue=mat("Midnight blue eyes",(.012,.035,.16),.2,.1)
black=mat("Pupils",(.002,.003,.008),.1)
white=mat("Eye whites",(.9,.86,.8),.25)
brow=mat("Brows",(.035,.022,.028),.5)
lip=mat("Lips",(.39,.12,.13),.4)
outfit=mat("Midnight blue outfit",(.018,.035,.13),.38)
trim=mat("Blue trim",(.08,.16,.42),.3,.15)

groups={}
def sphere(name, loc, scale, material, bone=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    if bone: groups.setdefault(bone,[]).append(o)
    return o

def linkseg(name,a,b,r,material,bone,depth=None):
    mid=(Vector(a)+Vector(b))*.5; d=Vector(b)-Vector(a)
    o=sphere(name,mid,(r,depth or r,d.length*.58),material,bone)
    o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat("Z","Y")
    return o

# Skeleton
ad=bpy.data.armatures.new("Nila_Rig"); rig=bpy.data.objects.new("Nila_Rig",ad)
bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active=rig; rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT"); eb={}
def addbone(n,h,t,parent=None,connected=False):
    b=ad.edit_bones.new(n); b.head=h; b.tail=t
    if parent: b.parent=eb[parent]; b.use_connect=connected
    eb[n]=b
addbone("root",(0,0,.08),(0,0,.95))
addbone("spine",(0,0,.95),(0,0,1.48),"root")
addbone("chest",(0,0,1.48),(0,0,1.72),"spine",True)
addbone("neck",(0,0,1.72),(0,0,1.88),"chest",True)
addbone("head",(0,0,1.88),(0,0,2.22),"neck",True)
for s,x in (("L",1),("R",-1)):
    addbone("upper_arm."+s,(x*.22,0,1.63),(x*.48,0,1.35),"chest")
    addbone("forearm."+s,(x*.48,0,1.35),(x*.57,0,1.06),"upper_arm."+s,True)
    addbone("hand."+s,(x*.57,0,1.06),(x*.58,0,.91),"forearm."+s,True)
    addbone("thigh."+s,(x*.13,0,.98),(x*.14,0,.55),"root")
    addbone("shin."+s,(x*.14,0,.55),(x*.14,0,.12),"thigh."+s,True)
    addbone("foot."+s,(x*.14,0,.12),(x*.14,-.2,.07),"shin."+s,True)
bpy.ops.object.mode_set(mode="OBJECT"); rig.select_set(False)

# Body
sphere("Pelvis",(0,0,.99),(.22,.14,.20),skin,"root")
sphere("Torso",(0,0,1.39),(.30,.16,.43),skin,"spine")
sphere("Chest",(0,0,1.62),(.34,.17,.23),skin,"chest")
sphere("Neck",(0,0,1.82),(.105,.105,.18),skin,"neck")
sphere("Head",(0,0,2.08),(.205,.18,.27),skin,"head")
sphere("Jaw",(0,-.012,1.96),(.16,.16,.13),skin,"head")
for s,x in (("L",1),("R",-1)):
    linkseg("Upper arm "+s,(x*.25,0,1.62),(x*.48,0,1.35),.095,skin,"upper_arm."+s,.09)
    linkseg("Forearm "+s,(x*.48,0,1.35),(x*.57,0,1.06),.073,skin,"forearm."+s,.07)
    sphere("Hand "+s,(x*.58,-.005,.99),(.075,.055,.12),skin,"hand."+s)
    linkseg("Thigh "+s,(x*.13,0,.99),(x*.14,0,.55),.115,skin,"thigh."+s,.11)
    linkseg("Calf "+s,(x*.14,0,.55),(x*.14,0,.13),.075,skin,"shin."+s,.075)
    sphere("Foot "+s,(x*.14,-.10,.09),(.09,.19,.07),skin,"foot."+s)

# Clothing overlay
sphere("Dress bodice",(0,-.004,1.48),(.315,.17,.31),outfit,"chest")
sphere("Dress waist",(0,-.004,1.19),(.245,.15,.18),outfit,"spine")
sphere("Skirt",(0,0,1.04),(.30,.19,.24),outfit,"root")
sphere("Neckline",(0,-.155,1.68),(.18,.025,.035),trim,"chest")

# Face, front is negative Y
for s,x in (("L",.082),("R",-.082)):
    sphere("Eye white "+s,(x,-.163,2.115),(.052,.025,.033),white,"head")
    sphere("Blue iris "+s,(x,-.187,2.114),(.022,.012,.024),blue,"head")
    sphere("Pupil "+s,(x,-.197,2.114),(.010,.007,.015),black,"head")
    sphere("Eye glint "+s,(x-.006,-.204,2.125),(.005,.004,.006),white,"head")
    sphere("Eyebrow "+s,(x,-.17,2.166),(.055,.018,.012),brow,"head")
sphere("Nose",(0,-.185,2.055),(.027,.03,.07),skin,"head")
sphere("Nose tip",(0,-.197,2.025),(.035,.028,.022),skin,"head")
sphere("Upper lip",(0,-.176,1.99),(.052,.014,.012),lip,"head")
sphere("Lower lip",(0,-.176,1.975),(.047,.014,.012),lip,"head")

# Hair cap, back length and side locks
sphere("Hair cap",(0,.015,2.22),(.22,.19,.18),hair,"head")
sphere("Long hair back",(0,.105,2.02),(.205,.105,.34),hair,"head")
for s,x in (("L",1),("R",-1)):
    linkseg("Hair lock "+s,(x*.17,0,2.19),(x*.19,.01,1.91),.055,hair,"head",.06)
sphere("Hair fringe",(0,-.135,2.245),(.18,.055,.075),hair,"head")
sphere("Hair highlight",(-.07,-.17,2.265),(.075,.012,.018),hairshine,"head")

# Parent each part to its corresponding bone
for bn,objs in groups.items():
    for o in objs:
        o.parent=rig; o.parent_type="BONE"; o.parent_bone=bn

# Simple named animation actions
def make_action(name, keys):
    bpy.context.view_layer.objects.active=rig; bpy.ops.object.mode_set(mode="POSE")
    for p in rig.pose.bones: p.rotation_mode="XYZ"
    for frame,pose in keys:
        for bn,rot in pose.items():
            p=rig.pose.bones.get(bn)
            if p:
                p.rotation_euler=rot
                p.keyframe_insert(data_path="rotation_euler",frame=frame,group=bn)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.animation_data.action.name=name
make_action("Nila_Stand",[(1,{}),(24,{"spine":(0,0,.015)}),(48,{})])
make_action("Nila_Walk",[(1,{"thigh.L":(.4,0,0),"thigh.R":(-.4,0,0),"upper_arm.L":(-.3,0,0),"upper_arm.R":(.3,0,0)}),(13,{"thigh.L":(-.4,0,0),"thigh.R":(.4,0,0),"upper_arm.L":(.3,0,0),"upper_arm.R":(-.3,0,0)}),(25,{"thigh.L":(.4,0,0),"thigh.R":(-.4,0,0),"upper_arm.L":(-.3,0,0),"upper_arm.R":(.3,0,0)})])
make_action("Nila_Wave",[(1,{"upper_arm.R":(0,0,-1.0),"forearm.R":(0,0,-1.0)}),(8,{"upper_arm.R":(0,0,-1.0),"forearm.R":(0,0,-1.6)}),(16,{"upper_arm.R":(0,0,-1.0),"forearm.R":(0,0,-.5)}),(24,{"upper_arm.R":(0,0,-1.0),"forearm.R":(0,0,-1.6)})])

# Export selected mesh + rig as GLB
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.context.scene.objects:
    if o.type in {"MESH","ARMATURE"}: o.select_set(True)
bpy.context.view_layer.objects.active=rig
path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"nila_avatar.glb")
bpy.ops.export_scene.gltf(filepath=path,export_format="GLB",use_selection=True,export_animations=True,export_skins=True)
print("Exported:",path)
