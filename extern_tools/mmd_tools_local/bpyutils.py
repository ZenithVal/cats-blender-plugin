# -*- coding: utf-8 -*-

import bpy

matmul = (lambda a, b: a*b) if bpy.app.version < (2, 80, 0) else (lambda a, b: a.__matmul__(b))

class __EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        self.__obj = obj
        self.__obj_select = obj.select
        with select_object(obj) as act_obj:
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self.__obj.data

    def __exit__(self, type, value, traceback):
        if self.__prevMode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT') # update edited data
        bpy.ops.object.mode_set(mode=self.__prevMode)
        self.__obj.select = self.__obj_select

class __SelectObjects:
    def __init__(self, active_object, selected_objects=[]):
        if not isinstance(active_object, bpy.types.Object):
            raise ValueError
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for i in bpy.context.selected_objects:
            i.select = False

        self.__active_object = active_object
        self.__selected_objects = [active_object]+selected_objects

        self.__hides = []
        scene = SceneOp(bpy.context)
        for i in self.__selected_objects:
            self.__hides.append(i.hide)
            scene.select_object(i)
        scene.active_object = active_object

    def __enter__(self):
        return self.__active_object

    def __exit__(self, type, value, traceback):
        for i, j in zip(self.__selected_objects, self.__hides):
            i.hide = j

def addon_preferences(attrname, default=None):
    if hasattr(bpy.context, 'preferences'):
        addon = bpy.context.preferences.addons.get(__package__, None)
    else:
        addon = bpy.context.user_preferences.addons.get(__package__, None)
    return getattr(addon.preferences, attrname, default) if addon else default

def setParent(obj, parent):
    ho = obj.hide
    hp = parent.hide
    obj.hide = False
    parent.hide = False
    select_object(parent)
    obj.select = True
    bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False)
    obj.hide = ho
    parent.hide = hp

def setParentToBone(obj, parent, bone_name):
    import bpy
    select_object(parent)
    bpy.ops.object.mode_set(mode='POSE')
    select_object(obj)
    SceneOp(bpy.context).active_object = parent
    parent.select = True
    bpy.ops.object.mode_set(mode='POSE')
    parent.data.bones.active = parent.data.bones[bone_name]
    bpy.ops.object.parent_set(type='BONE', xmirror=False, keep_transform=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def edit_object(obj):
    """ Set the object interaction mode to 'EDIT'

     It is recommended to use 'edit_object' with 'with' statement like the following code.

        with edit_object:
            some functions...
    """
    return __EditMode(obj)

def select_object(obj, objects=[]):
    """ Select objects.

     It is recommended to use 'select_object' with 'with' statement like the following code.
     This function can select "hidden" objects safely.

        with select_object(obj):
            some functions...
    """
    return __SelectObjects(obj, objects)

def duplicateObject(obj, total_len):
    for i in bpy.context.selected_objects:
        i.select = False
    obj.select = True
    assert(len(bpy.context.selected_objects) == 1)
    assert(bpy.context.selected_objects[0] == obj)
    last_selected = objs = [obj]
    while len(objs) < total_len:
        bpy.ops.object.duplicate()
        objs.extend(bpy.context.selected_objects)
        remain = total_len - len(objs) - len(bpy.context.selected_objects)
        if remain < 0:
            last_selected = bpy.context.selected_objects
            for i in range(-remain):
                last_selected[i].select = False
        else:
            for i in range(min(remain, len(last_selected))):
                last_selected[i].select = True
        last_selected = bpy.context.selected_objects
    assert(len(objs) == total_len)
    return objs

def makeCapsuleBak(segment=16, ring_count=8, radius=1.0, height=1.0, target_scene=None):
    import math
    target_scene = SceneOp(target_scene)
    mesh = bpy.data.meshes.new(name='Capsule')
    meshObj = bpy.data.objects.new(name='Capsule', object_data=mesh)
    vertices = []
    top = (0, 0, height/2+radius)
    vertices.append(top)

    f = lambda i: radius*i/ring_count
    for i in range(ring_count, 0, -1):
        z = f(i-1)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z+height/2))

    for i in range(ring_count):
        z = -f(i)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z-height/2))

    bottom = (0, 0, -(height/2+radius))
    vertices.append(bottom)

    faces = []
    for i in range(1, segment):
        faces.append([0, i, i+1])
    faces.append([0, segment, 1])
    offset = segment + 1
    for i in range(ring_count*2-1):
        for j in range(segment-1):
            t = offset + j
            faces.append([t-segment, t, t+1, t-segment+1])
        faces.append([offset-1, offset+segment-1, offset, offset-segment])
        offset += segment
    for i in range(segment-1):
        t = offset + i
        faces.append([t-segment, offset, t-segment+1])
    faces.append([offset-1, offset, offset-segment])

    mesh.from_pydata(vertices, [], faces)
    target_scene.link_object(meshObj)
    return meshObj

def createObject(name='Object', object_data=None, target_scene=None):
    target_scene = SceneOp(target_scene)
    obj = bpy.data.objects.new(name=name, object_data=object_data)
    target_scene.link_object(obj)
    target_scene.active_object = obj
    obj.select = True
    return obj

def makeSphere(segment=8, ring_count=5, radius=1.0, target_object=None):
    import bmesh
    if target_object is None:
        target_object = createObject(name='Sphere')

    mesh = target_object.data
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=segment,
        v_segments=ring_count,
        diameter=radius,
        )
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    return target_object

def makeBox(size=(1,1,1), target_object=None):
    import bmesh
    from mathutils import Matrix
    if target_object is None:
        target_object = createObject(name='Box')

    mesh = target_object.data
    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm,
        size=2,
        matrix=Matrix([[size[0],0,0,0], [0,size[1],0,0], [0,0,size[2],0], [0,0,0,1]]),
        )
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    return target_object

def makeCapsule(segment=8, ring_count=2, radius=1.0, height=1.0, target_object=None):
    import bmesh
    import math
    if target_object is None:
        target_object = createObject(name='Capsule')
    height = max(height, 1e-3)

    mesh = target_object.data
    bm = bmesh.new()
    verts = bm.verts
    top = (0, 0, height/2+radius)
    verts.new(top)

    #f = lambda i: radius*i/ring_count
    f = lambda i: radius*math.sin(0.5*math.pi*i/ring_count)
    for i in range(ring_count, 0, -1):
        z = f(i-1)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            verts.new((x,y,z+height/2))

    for i in range(ring_count):
        z = -f(i)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            verts.new((x,y,z-height/2))

    bottom = (0, 0, -(height/2+radius))
    verts.new(bottom)
    if hasattr(verts, 'ensure_lookup_table'):
        verts.ensure_lookup_table()

    faces = bm.faces
    for i in range(1, segment):
        faces.new([verts[x] for x in (0, i, i+1)])
    faces.new([verts[x] for x in (0, segment, 1)])
    offset = segment + 1
    for i in range(ring_count*2-1):
        for j in range(segment-1):
            t = offset + j
            faces.new([verts[x] for x in (t-segment, t, t+1, t-segment+1)])
        faces.new([verts[x] for x in (offset-1, offset+segment-1, offset, offset-segment)])
        offset += segment
    for i in range(segment-1):
        t = offset + i
        faces.new([verts[x] for x in (t-segment, offset, t-segment+1)])
    faces.new([verts[x] for x in (offset-1, offset, offset-segment)])

    for f in bm.faces:
        f.smooth = True
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return target_object


class ObjectOp:

    def __init__(self, obj):
        self.__obj = obj

    def __clean_drivers(self, key):
        for d in getattr(key.id_data.animation_data, 'drivers', ()):
            if d.data_path.startswith(key.path_from_id()):
                key.id_data.driver_remove(d.data_path, -1)

    def shape_key_remove(self, key):
        obj = self.__obj
        assert(key.id_data == obj.data.shape_keys)
        key_blocks = key.id_data.key_blocks
        last_index = obj.active_shape_key_index
        if last_index >= key_blocks.find(key.name):
            last_index = max(0, last_index-1)
        self.__clean_drivers(key)
        obj.shape_key_remove(key)
        obj.active_shape_key_index = min(last_index, len(key_blocks)-1)

class TransformConstraintOp:

    __MIN_MAX_MAP = {} if bpy.app.version < (2, 71, 0) else {'ROTATION':'_rot', 'SCALE':'_scale'}

    @staticmethod
    def create(constraints, name, map_type):
        c = constraints.get(name, None)
        if c and c.type != 'TRANSFORM':
            constraints.remove(c)
            c = None
        if c is None:
            c = constraints.new('TRANSFORM')
            c.name = name
        c.use_motion_extrapolate = True
        c.target_space = c.owner_space = 'LOCAL'
        c.map_from = c.map_to = map_type
        c.map_to_x_from = 'X'
        c.map_to_y_from = 'Y'
        c.map_to_z_from = 'Z'
        c.influence = 1
        return c

    @classmethod
    def min_max_attributes(cls, map_type, name_id=''):
        key = (map_type, name_id)
        ret = cls.__MIN_MAX_MAP.get(key, None)
        if ret is None:
            defaults = (i+j+k for i in ('from_', 'to_') for j in ('min_', 'max_') for k in 'xyz')
            extension = cls.__MIN_MAX_MAP.get(map_type, '')
            ret = cls.__MIN_MAX_MAP[key] = tuple(n+extension for n in defaults if name_id in n)
        return ret

    @classmethod
    def update_min_max(cls, constraint, value, influence=1):
        c = constraint
        if not c or c.type != 'TRANSFORM':
            return

        for attr in cls.min_max_attributes(c.map_from, 'from_min'):
            setattr(c, attr, -value)
        for attr in cls.min_max_attributes(c.map_from, 'from_max'):
            setattr(c, attr, value)

        if influence is None:
            return

        for attr in cls.min_max_attributes(c.map_to, 'to_min'):
            setattr(c, attr, -value*influence)
        for attr in cls.min_max_attributes(c.map_to, 'to_max'):
            setattr(c, attr, value*influence)

class SceneOp:
    def __init__(self, context):
        self.__context = context or bpy.context
        self.__collection = self.__context.collection
        self.__view_layer = self.__context.view_layer

    def select_object(self, obj):
        obj.hide = obj.hide_select = False
        obj.select = True

    def link_object(self, obj):
        self.__collection.objects.link(obj)

    @property
    def active_object(self):
        return self.__view_layer.objects.active

    @active_object.setter
    def active_object(self, obj):
        self.__view_layer.objects.active = obj

    @property
    def id_scene(self):
        return self.__view_layer

    @property
    def id_objects(self):
        return self.__view_layer.objects

