"""Live cache ownership/budget, world metrics and deep backface traversal."""
from mathutils import Matrix, Vector
import bpy
from test_make_live import fresh, cube, live


def test_cache_released_only_after_last_live_scene_releases_reference():
    scene = fresh()
    reference = cube()
    other = bpy.data.scenes.new('SharedLiveCache')
    other.collection.objects.link(reference)
    try:
        live.set_objects(scene, [reference])
        live.set_objects(other, [reference])
        bpy.context.view_layer.update()
        live.tree(bpy.context, reference)
        uid = reference.session_uid
        live.set_objects(scene, [])
        assert uid in live._trees
        live.set_objects(other, [])
        assert uid not in live._trees
    finally:
        bpy.data.scenes.remove(other)


def test_native_bvh_keeps_uniform_world_positions_and_mirrored_winding():
    scene = fresh()
    bpy.ops.mesh.primitive_plane_add(size=10, location=(2, 3, 4))
    reference = bpy.context.object
    reference.scale = (-2, 2, 2)
    reference.rotation_euler = (.3, .2, .6)
    live.set_objects(scene, [reference])
    bpy.context.view_layer.update()
    tree = live.tree(bpy.context, reference)
    assert tree.matrix is not None
    centre = reference.matrix_world.translation
    winding = -(reference.matrix_world.to_3x3().inverted().transposed() @ Vector((0, 0, 1))).normalized()
    point = centre+winding*5
    hit = live.ray_hit(bpy.context, point, -winding, backfaces=False)
    assert hit and (hit[0]-centre).length < 1e-5 and hit[1].dot(winding) > .9999
    assert live.ray_hit(bpy.context, centre-winding*5, winding, backfaces=False) is None
    assert (live.nearest(bpy.context, point)[0]-centre).length < 1e-5
    assert not live._similarity(Matrix(((1, .5, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))))


def test_cache_budget_evicts_least_recently_queried_surface():
    scene = fresh()
    refs = [cube('Budget'+str(i), (i*4, 0, 0)) for i in range(3)]
    live.set_objects(scene, refs)
    bpy.context.view_layer.update()
    live._trees.clear()
    before = live.CACHE_BUDGET
    try:
        live.tree(bpy.context, refs[0])
        cost = live._trees[refs[0].session_uid][3]
        live.CACHE_BUDGET = cost*2
        live.tree(bpy.context, refs[1])
        live.tree(bpy.context, refs[0])  # make ref 1 the oldest
        live.tree(bpy.context, refs[2])
        assert set(live._trees) == {refs[0].session_uid, refs[2].session_uid}
    finally:
        live.CACHE_BUDGET = before


def test_backface_traversal_finds_front_face_after_many_rejected_layers():
    scene = fresh()
    vertices, faces = [], []
    for z in range(81):
        i = len(vertices)
        vertices.extend(((-1, -1, z), (-1, 1, z), (1, 1, z), (1, -1, z)))
        faces.append((i, i+3, i+2, i+1) if z == 0 else (i, i+1, i+2, i+3))
    mesh = bpy.data.meshes.new('DeepLayers')
    mesh.from_pydata(vertices, [], faces)
    reference = bpy.data.objects.new('DeepLayers', mesh)
    scene.collection.objects.link(reference)
    live.set_objects(scene, [reference])
    bpy.context.view_layer.update()
    origin, direction = Vector((0, 0, 100)), Vector((0, 0, -1))
    hit = live.ray_hit(bpy.context, origin, direction, backfaces=False)
    assert hit and abs(hit[0].z) < 1e-6 and hit[1].z > .99
    assert abs(live.ray_hit(bpy.context, origin, direction, backfaces=True)[0].z-80) < 1e-6
    mesh.clear_geometry()
    mesh.from_pydata(vertices[4:], [], [tuple(i-4 for i in face) for face in faces[1:]])
    mesh.update()
    bpy.context.view_layer.update()
    assert live.ray_hit(bpy.context, origin, direction, backfaces=False) is None


def test_non_live_quad_draw_cache_survives_unrelated_scene_updates():
    scene = fresh()
    reference, mover = cube('Fallback'), cube('Mover', (4, 0, 0))
    bpy.context.view_layer.update()
    tree = live.tree(bpy.context, reference)
    mover.location.x = 6
    bpy.context.view_layer.update()
    assert live.tree(bpy.context, reference) is tree
