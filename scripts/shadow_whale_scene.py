import bpy, math, random, os
from mathutils import Vector
from math import sin,cos,pi
random.seed(3481)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.resolution_x=720;scene.render.resolution_y=1280;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX" if bpy.app.version[0]>=4 else "Filmic"
scene.view_settings.look="AgX - Medium High Contrast" if bpy.app.version[0]>=4 else "Medium High Contrast"
for engine in ("CYCLES",):
    try: scene.render.engine=engine;break
    except:pass
if scene.render.engine=="CYCLES":
    scene.cycles.samples=14
    scene.cycles.use_denoising=True
else:
    try:scene.eevee.taa_render_samples=64
    except:pass
world=bpy.data.worlds.new("Abyssal blue night")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.008,0.016,0.028,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.32
def mat(name,color,rough=.9,noise=True,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if noise:
        n=m.node_tree.nodes.new("ShaderNodeTexNoise");n.inputs["Scale"].default_value=4.1;n.inputs["Detail"].default_value=3.2
        bump=m.node_tree.nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=.36;bump.inputs["Distance"].default_value=.11
        m.node_tree.links.new(n.outputs["Fac"],bump.inputs["Height"]);m.node_tree.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m
def emissive(name,color,strength=5):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;n.clear()
    out=n.new("ShaderNodeOutputMaterial");em=n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value=(*color,1);em.inputs["Strength"].default_value=strength
    m.node_tree.links.new(em.outputs[0],out.inputs["Surface"]);return m
dark=mat("01 Shadowed slate - rock",(0.08,.12,.16))
slate=mat("02 Ancient stone",(0.12,.16,.2))
rock2=mat("03 Frost cliff",(0.115,.15,.18))
blue=mat("04 Living whale stone",(0.11,.17,.225),.93)
ridge=mat("05 Ridge stone",(0.093,.137,.165))
hoodmat=mat("06 Indigo travellers wool",(0.059,.081,.127))
cape=mat("07 Dusty blue cloak",(.073,.105,.163))
scarf=mat("08 Wine-red sash",(.28,.089,.112),.85,False)
black=mat("09 Hood void",(.008,.013,.018),1,False)
fire=emissive("10 Campfire amber",(1,.32,.054),5)
glyph=emissive("11 Runes of deep sea",(.045,.75,1),6)
eye=emissive("12 Eye of the ancient whale",(.08,.84,1),13)
mist=mat("13 Deep atmospheric fog",(.07,.12,.17),1,False)
def assign(ob,m): ob.data.materials.append(m);return ob
def uv(name,loc,scale,m,seg=32,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;assign(ob,m);return ob
def ico(name,loc,scale,m,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;assign(ob,m);return ob
def cylinder(name,a,b,r,m,v=10):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d.length,location=(a+b)*.5)
    ob=bpy.context.object;ob.name=name;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();assign(ob,m)
    return ob
def tube(name,points,m,radius=.035):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=radius;curve.bevel_resolution=2
    p=curve.splines.new('POLY');p.points.add(len(points)-1)
    for node,xyz in zip(p.points,points):node.co=(*xyz,1)
    ob=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(ob);assign(ob,m);return ob
def tri(name,pts,m):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(pts,[],[list(range(len(pts)))]);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);assign(ob,m);return ob
def light(name,kind,loc,color,power,size=6):
    data=bpy.data.lights.new(name,kind);data.energy=power;data.color=color
    if kind=="AREA":data.shape="DISK";data.size=size
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=loc;return ob
def look(obj,at):
    vec=Vector(at)-obj.location;obj.rotation_euler=vec.to_track_quat('-Z','Y').to_euler()
# camera 45 degree photographic projection
data=bpy.data.cameras.new("Cinematic portrait camera");cam=bpy.data.objects.new("Camera",data);bpy.context.collection.objects.link(cam);scene.camera=cam
data.type='PERSP';data.lens=29;data.clip_end=500
# Ancient landscape, layered and deliberately irregular rock silhouettes.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,9,-.65))
ground=bpy.context.object;ground.name="Obsidian pass";assign(ground,slate)
for side in [-1,1]:
    for j in range(85):
        y=random.uniform(-24,39)
        x=side*random.uniform(7.2,18)
        z=random.uniform(.4,9)
        s=random.uniform(1,4.7)
        m=random.choice([dark,slate,rock2])
        ob=ico("broken mountainside", (x,y,z), (s,random.uniform(2.2,5.5),random.uniform(3.5,11)),m,1)
        ob.rotation_euler=(random.uniform(-.12,.12),random.uniform(-.2,.2),random.uniform(-.6,.6))
# Mountain terraces and stepping stones
for j in range(160):
    x=random.uniform(-5.5,5.5);y=random.uniform(-18,22)
    ob=ico("pass broken stone",(x,y,-.5),(random.uniform(.2,.8),random.uniform(.2,.9),random.uniform(.11,.4)),random.choice([dark,slate,rock2]))
    ob.rotation_euler[2]=random.uniform(0,pi)
for j in range(45):
    x=random.uniform(-6.5,6.5);y=random.uniform(-15,18)
    ico("stone flake",(x,y,random.uniform(-.3,.3)),(random.uniform(.2,.6),random.uniform(.2,.7),random.uniform(.2,.7)),ridge)
# Whale-body will rise from rock, colossal and partially covered in strata
whale_group=[]
def track(ob):whale_group.append((ob,ob.location.copy()));return ob
track(uv("GIANT SHADOW WHALE - body",(0,12.0,6.7),(6.0,10.7,5.55),blue,64,32))
track(uv("Basalt whale head",(0,4.0,6.3),(5.25,5.5,4.8),blue,56,28))
track(uv("Ancient upper jaw",(0,1.6,4.3),(4.0,2.55,1.1),ridge,48,22))
# whale eye on camera-facing flank, blue glowing iris ring
for xside in [-1,1]:
    ex=xside*4.95
    track(uv("Eye socket",(ex,2.65,8.65),(.65,.7,.76),black,32,20))
    track(uv("Awakening eye",(xside*5.38,2.25,8.65),(.29,.35,.38),eye,32,20))
    track(uv("Eye pupil",(xside*5.64,2.08,8.65),(.14,.19,.22),black,24,16))
# long weathered fins, visibly whale-like
for side in [-1,1]:
    pts=[(side*3.8,4.2,6.2),(side*6.0,5.6,6.4),(side*11.6,10.8,4.1),(side*9.0,13.0,3.7),(side*4.8,12.1,5.2)]
    fin=tri("Colossal flank fin",pts,ridge);track(fin)
    for t in range(6):
        a=(side*(4.6+t*.7),5.8+t*.65,6.5-t*.21)
        b=(side*(5.5+t*.83),8.0+t*.63,5.8-t*.2)
        curve=tube("fin vein",[a,b],dark,.08);track(curve)
# forked tail at far end
for side in [-1,1]:
    fin=tri("Whale tail fluke",[(0,20,8),(side*5.3,25,11.7),(side*4.6,26.1,14.5),(side*.3,23,8.2)],blue)
    track(fin)
# irregular basalt ridges along the leviathan
for j in range(95):
    theta=random.uniform(.28,2.86);u=random.uniform(-1,1)
    yy=12+u*9.5
    xx=5.6*math.cos(theta)*math.sqrt(max(.1,1-u*u))
    zz=6.7+5.4*math.sin(theta)*math.sqrt(max(.1,1-u*u))
    size=random.uniform(.2,.9)
    track(ico("Rock grown from the back",(xx,yy,zz),(size*1.6,size*2.1,size*.65),random.choice([blue,ridge,slate])))
# protective armor grooves to differentiate whale from geological ridge
for k in range(7):
    pts=[]
    yy=2+k*2.8
    for i in range(15):
        x=-5.0+i*(10/14)
        z=6.7+4.7*math.sqrt(max(.05,1-(x/5.8)**2))
        pts.append((x,yy,z+.18))
    track(tube("Whale dorsal grooves",pts,dark,.065))
# floor luminous cracks (path along x/y)
for i in range(17):
    x=random.uniform(-5,5);yy=random.uniform(-10,11)
    pts=[(x,yy,-.32)]
    for j in range(4):
        x+=random.uniform(-1.3,1.3)
        yy+=random.uniform(.5,1.4)
        pts.append((x,yy,-.31))
    tube("Rune fissure",pts,glyph,random.uniform(.018,.057))
# distant ruin carved into the pass and standing runestones
for j in range(11):
    x=(-1 if j%2 else 1)*random.uniform(5.5,10)
    y=random.uniform(-14,20)
    p=ico("weathered upright",(x,y,2.1),(random.uniform(.7,1.5),random.uniform(.5,1),random.uniform(2.2,5)),dark)
    p.rotation_euler[1]=random.uniform(-.22,.22)
    for k in range(3):
        tube("Carved runes",[(x-.25,y-1,1.4+k*.5),(x+.1,y-1,1.7+k*.5)],glyph,.025)
# Traveler at foreground center
traveler=[]
def pt(ob):traveler.append((ob,ob.location.copy()));return ob
# tapered robe as cone pointing up, body facing toward whale
bpy.ops.mesh.primitive_cone_add(vertices=18,radius1=.76,radius2=.32,depth=2.65,location=(-1.35,-6.6,1.35))
pt(assign(bpy.context.object,cape))
pt(uv("Travellers hood",(-1.35,-6.6,2.91),(.57,.52,.67),hoodmat,32,20))
pt(uv("Shadow inside hood",(-1.35,-7.08,2.92),(.39,.13,.43),black,32,16))
pt(cylinder("Crimson collar",(-1.68,-6.68,2.38),(-1.1,-6.56,2.38),.19,scarf,14))
for side in [-1,1]:
    pt(cylinder("Travel worn sleeve",(-1.35+side*.33,-6.58,2.2),(-1.35+side*.75,-6.45,1.45),.2,cape))
    pt(cylinder("Boots",(-1.35+side*.30,-6.6,.55),(-1.35+side*.30,-6.5,-.15),.20,black))
# Campfire ember pit off edge of pass, warm glow
for i in range(9):
    angle=i*2*pi/9
    ico("charcoal ring",(2.5+.64*cos(angle),-4.0+.64*sin(angle),-.12),(.38,.3,.2),dark)
for k in range(4):
    dx=random.uniform(-.25,.25);dy=random.uniform(-.23,.23)
    uv("Embers",(2.5+dx,-4+dy,.33+k*.2),(.25-k*.04,.21-k*.03,.35+k*.08),fire,16,10)
torchlight=light("Low campfire light","POINT",(2.5,-4.0,.5),(1,.28,.08),750)
# Film light setup
light("Polar rim light","AREA",(-15,7,23),(.20,.53,1.0),2200,14)
light("Front cold fill","AREA",(-1,-16,13),(.36,.58,.82),2800,16)
light("Cold heaven","AREA",(9,20,23),(.22,.46,.78),2500,16)
light("Whale eye fill","POINT",(-6,2.5,9),(.12,.57,1),1150)
light("Dim moon","AREA",(0,-14,24),(.23,.36,.56),850,13)
# Dust in cold moonlight and fog sheets
for i in range(100):
    x=random.uniform(-15,15);y=random.uniform(-14,28);z=random.uniform(1,19)
    if random.random()<.4:
        uv("floating ash",(x,y,z),(.035,.035,.035),glyph,8,6)
# Atmospheric volume that adds depth without hiding subject
try:
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,5,9))
    fog=bpy.context.object;fog.name="Blue cinematic haze";fog.scale=(35,40,18)
    fm=bpy.data.materials.new("Haze over the shadow pass");fm.use_nodes=True
    ns=fm.node_tree.nodes;ns.clear()
    vo=ns.new("ShaderNodeVolumePrincipled")
    vo.inputs["Color"].default_value=(.14,.27,.4,1)
    vo.inputs["Density"].default_value=.011
    vo.inputs["Anisotropy"].default_value=.3
    out=ns.new("ShaderNodeOutputMaterial");fm.node_tree.links.new(vo.outputs["Volume"],out.inputs["Volume"]);assign(fog,fm)
except Exception as e: print("FOG",e)
frames=[
    ((0,-20,4.4), (0,8,5.5), -3.4,0.0, 0.55),
    ((-2,-16,3), (0,6,2.4), -1.2,0.0, 1.0),
    ((-2.5,-12,5.6), (-1,5.2,8.5), -0.3,0.0, 1.0),
    ((1.2,-21,6.7), (0,9,7.0), 0.4,0.0, 1.0),
    ((-3.0,-15,6.4), (0,8.5,8.6), 1.8,0.0, 1.0),
    ((-4,-13,7), (0,9,6), 1.1,1.5, 1.0),
    ((1.0,-12,4.6), (-1.1,3.5,3.5), -2.3,2.0, 1.0),
    ((2,-9,3), (2,0,.3), -4.3,0.0, 1.8),
    ((0,-19,5.8), (0,11,7.5), -3.5,0.0, .75),
]
outdir=os.getenv("WHALE_FRAMES","/tmp/whale_frames");os.makedirs(outdir,exist_ok=True)
for i,(pos,target,zoffset,traveler_z,firepower) in enumerate(frames):
    for ob,original in whale_group: ob.location=original+Vector((0,0,zoffset))
    for ob,original in traveler:ob.location=original+Vector((0,0,traveler_z))
    torchlight.data.energy=750*firepower
    cam.location=pos;look(cam,target)
    scene.render.filepath=os.path.join(outdir,f"shot_{i:02d}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED",scene.render.filepath,flush=True)
