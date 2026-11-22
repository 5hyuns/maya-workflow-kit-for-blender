"""#466: Edit Edge Flow on an edge loop that runs from one border of a domed plane to the other keeps the whole loop on
the dome: the border vertices move like the inner ones (the curve continues along the border), and each vertex goes to
the middle of the curve between its ring neighbours, wherever it was between them."""
import bmesh
import bpy


def _dome(x, y):
    return 0.6 - 0.1 * (x * x + y * y)


def _plane(row_y=0.0, n=4, size=4.0):
    """An n x n plane of ``size`` with its vertices lifted onto the dome; the vertex row nearest y == 0 is moved to
    ``row_y`` (still on the dome). Returns the object and the indices of that row."""
    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("dome")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=size / 2)
    row = []
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        if abs(y) < 1e-6:
            y = row_y
            row.append(v.index)
        v.co = (x, y, _dome(x, y))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("dome", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob, row


def _edge_flow(ob, row, flow=1.0):
    me = ob.data
    rows = set(row)
    for e in me.edges:
        e.select = all(i in rows for i in e.vertices)
    for v in me.vertices:
        v.select = v.index in rows
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    r = bpy.ops.allset.edge_flow(flow=flow)
    bpy.ops.object.mode_set(mode='OBJECT')
    assert r == {'FINISHED'}, r
    return {i: me.vertices[i].co.copy() for i in row}


def test_border_vertices_follow_the_dome():
    ob, row = _plane()
    after = _edge_flow(ob, row)
    assert len(after) == 5, after
    lift = {}
    for i, co in after.items():
        assert abs(co.y) < 1e-6, (i, co)
        lift[i] = co.z - _dome(co.x, co.y)
        assert -1e-4 < lift[i] < 2e-3, ("vertex left the dome", i, co, lift[i])
    # the dome is the same curve across every column: border and inner vertices move alike
    assert max(lift.values()) - min(lift.values()) < 1e-6, lift


def test_position_between_neighbours_does_not_matter():
    results = []
    for row_y in (0.0, -0.25, 0.5):
        ob, row = _plane(row_y)
        after = _edge_flow(ob, row)
        results.append(sorted((round(co.x, 6), co.y, co.z) for co in after.values()))
    for other in results[1:]:
        for (x0, y0, z0), (x1, y1, z1) in zip(results[0], other):
            assert x0 == x1 and abs(y0 - y1) < 1e-6 and abs(z0 - z1) < 1e-6, (results[0], other)


def test_flow_zero_is_the_straight_line():
    ob, row = _plane(0.3)
    after = _edge_flow(ob, row, flow=0.0)
    for co in after.values():
        # the middle of the ring neighbours at y = -1 and y = 1
        assert abs(co.y) < 1e-6 and abs(co.z - _dome(co.x, 1.0)) < 1e-6, co
