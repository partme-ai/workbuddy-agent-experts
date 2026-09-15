"""Editable retopology: setup, projection, data transfer and validation."""
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .mesh import TOPOLOGY_VERSION_KEY
from .validation import finite_number, require_name


class RetopoCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.objects = ObjectResolver(bpy_module)
        self.context = OperationContext(bpy_module)

    def setup_surface(self, arguments):
        """Create an editable retopology surface from a source mesh.

        The result is ordinary mesh data — no modifier stack, no placeholders.
        If *symmetry* is requested the surface is mirrored and merged.
        """
        source = self.objects.resolve(arguments.get('sourceObjectId', {}), required_type={'MESH'})
        target_name = require_name(arguments.get('targetName', ''))
        symmetry = str(arguments.get('symmetry', 'none')).lower()
        if symmetry not in ('none', 'x', 'y', 'z'):
            raise HarnessError('INVALID_ARGUMENT', 'symmetry must be none, x, y, or z')
        offset = finite_number(arguments.get('offset', 0.01), 'offset', positive=True)

        import bmesh
        import mathutils

        verts = [v.co.copy() for v in source.data.vertices]
        if not verts:
            raise HarnessError('INVALID_ARGUMENT', 'source mesh has no vertices')
        min_co = mathutils.Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
        max_co = mathutils.Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
        center = (min_co + max_co) / 2
        size = max_co - min_co
        max_dim = max(size.x, size.y, size.z)
        if max_dim < 1e-8:
            max_dim = 1.0

        mesh_data = self.bpy.data.meshes.new(target_name + '_mesh')
        obj = self.bpy.data.objects.new(target_name, mesh_data)
        self.bpy.context.scene.collection.objects.link(obj)

        bm = bmesh.new()
        try:
            bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=max_dim / 2)
            for v in bm.verts:
                v.co.x += center.x
                v.co.y += center.y
                v.co.z = center.z + max_dim / 2 + offset
            bm.to_mesh(mesh_data)
            mesh_data.update()
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED', 'setup_surface failed') from exc
        finally:
            bm.free()

        # Apply symmetry if requested
        if symmetry != 'none':
            axis = {'x': 0, 'y': 1, 'z': 2}[symmetry]
            self._apply_mirror(obj, axis, center)

        obj.data[TOPOLOGY_VERSION_KEY] = 0
        self.objects.ensure_id(obj)
        return {'changedObjects': [obj.name], 'result': self.objects.receipt(obj) | {
            'topologyVersion': 0, 'symmetry': symmetry,
            'limitations': ['Grid surface is a starting point; manual editing expected for production retopology.']}}

    def _apply_mirror(self, obj, axis, center):
        """Mirror mesh about an axis through center, then merge."""
        import bmesh
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            for v in bm.verts:
                v.co[axis] = center[axis] - (v.co[axis] - center[axis])
            # Remove doubles at the seam
            bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-4)
            bm.normal_update()
            bm.to_mesh(obj.data)
            obj.data.update()
        finally:
            bm.free()

    def project(self, arguments):
        """Project retopo vertices onto the source mesh surface.

        Uses nearest-point projection. Result is real vertex data, no modifiers.
        """
        oid = arguments.get('objectId')
        target = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'MESH'})
        source = self.objects.resolve(arguments.get('sourceObjectId', {}), required_type={'MESH'})
        method = str(arguments.get('method', 'nearest')).lower()
        if method not in ('nearest', 'normal'):
            raise HarnessError('INVALID_ARGUMENT', 'method must be nearest or normal')
        max_distance = finite_number(arguments.get('maxDistance', 0.1), 'maxDistance', positive=True)

        import bmesh
        import mathutils

        # Build BVH tree for source
        source_bm = bmesh.new()
        target_bm = bmesh.new()
        try:
            source_bm.from_mesh(source.data)
            source_bm.faces.ensure_lookup_table()
            if len(source_bm.faces) == 0:
                raise HarnessError('INVALID_ARGUMENT', 'source mesh has no faces for projection')

            # Build kd-tree from source vertices for nearest-point
            source_verts = [v.co.copy() for v in source.data.vertices]
            kd = mathutils.kdtree.KDTree(len(source_verts))
            for i, v in enumerate(source_verts):
                kd.insert(v, i)
            kd.balance()

            target_bm.from_mesh(target.data)
            target_bm.verts.ensure_lookup_table()

            projected = 0
            clamped = 0
            for vert in target_bm.verts:
                co = vert.co.copy()
                # Find nearest point on source
                nearest_loc, nearest_idx, nearest_dist = kd.find(co)
                if nearest_loc is None:
                    continue
                if nearest_dist <= max_distance:
                    vert.co = nearest_loc
                    projected += 1
                else:
                    # Clamp to max_distance along the direction to nearest
                    direction = (nearest_loc - co)
                    if direction.length > 1e-8:
                        direction.normalize()
                        vert.co = co + direction * max_distance
                    clamped += 1

            target_bm.normal_update()
            target_bm.to_mesh(target.data)
            target.data.update()
            target.data[TOPOLOGY_VERSION_KEY] = int(target.data.get(TOPOLOGY_VERSION_KEY, 0)) + 1
        except HarnessError:
            raise
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED', 'projection failed') from exc
        finally:
            source_bm.free()
            target_bm.free()

        return {'changedObjects': [target.name], 'result': self.objects.receipt(target) | {
            'topologyVersion': int(target.data.get(TOPOLOGY_VERSION_KEY, 0)),
            'projected': projected, 'clamped': clamped, 'method': method,
            'maxDistance': max_distance,
            'limitations': ['Projection result is automatic; manual review and editing required for production retopology.']}}

    def transfer_layers(self, arguments):
        """Transfer data layers (vertex groups, color attributes) from source to target.

        Uses nearest-vertex mapping. Layers are written to the target mesh data directly.
        """
        source = self.objects.resolve(arguments.get('sourceObjectId', {}), required_type={'MESH'})
        target = self.objects.resolve(arguments.get('targetObjectId', {}), required_type={'MESH'})
        layers = arguments.get('layers', [])
        if not isinstance(layers, list) or not layers:
            raise HarnessError('INVALID_ARGUMENT', 'layers must be a non-empty list of layer names')
        if any(not isinstance(name, str) or not name.strip() for name in layers):
            raise HarnessError('INVALID_ARGUMENT', 'each layer name must be a non-empty string')

        import mathutils
        source_verts = [v.co.copy() for v in source.data.vertices]
        if not source_verts:
            raise HarnessError('INVALID_ARGUMENT', 'source mesh has no vertices')
        kd = mathutils.kdtree.KDTree(len(source_verts))
        for i, v in enumerate(source_verts):
            kd.insert(v, i)
        kd.balance()

        transferred = []
        for layer_name in layers:
            # Try vertex groups first
            vg = source.vertex_groups.get(layer_name)
            if vg is not None:
                # Create or get target vertex group
                target_vg = target.vertex_groups.get(layer_name)
                if target_vg is None:
                    target_vg = target.vertex_groups.new(name=layer_name)
                # Transfer weights by nearest vertex
                for t_idx, t_vert in enumerate(target.data.vertices):
                    _, nearest_idx, _ = kd.find(t_vert.co)
                    if nearest_idx is None:
                        continue
                    try:
                        weight = vg.weight(nearest_idx)
                    except RuntimeError:
                        weight = 0.0
                    target_vg.add([t_idx], weight, 'REPLACE')
                transferred.append({'name': layer_name, 'type': 'vertex_group'})
                continue

            # Try color attributes
            color_attr = source.data.color_attributes.get(layer_name)
            if color_attr is not None:
                target_attr = target.data.color_attributes.get(layer_name)
                if target_attr is None:
                    target_attr = target.data.color_attributes.new(
                        name=layer_name, type=color_attr.data_type, domain=color_attr.domain)
                if target_attr.domain == 'POINT':
                    for t_idx, t_vert in enumerate(target.data.vertices):
                        _, nearest_idx, _ = kd.find(t_vert.co)
                        if nearest_idx is None:
                            continue
                        target_attr.data[t_idx].color = list(color_attr.data[nearest_idx].color)
                    transferred.append({'name': layer_name, 'type': 'color_attribute'})
                    continue

            raise HarnessError('LAYER_NOT_FOUND', f'layer {layer_name!r} not found on source mesh')

        target.data.update()
        return {'changedObjects': [target.name], 'result': self.objects.receipt(target) | {
            'transferred': transferred,
            'transferMethod': 'nearest_vertex',
            'limitations': ['Nearest-vertex mapping is coarse; no barycentric interpolation. Weights may be discontinuous on sparse target meshes.']}}


    def validate(self, arguments):
        """Validate retopo topology quality.

        Returns explicit pass/handover status.  When maxDeviation or
        maxPoleValence is exceeded the result enters 'handover' state,
        indicating human intervention is needed.
        """
        oid = arguments.get('objectId')
        obj = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'MESH'})
        source = self.objects.resolve(arguments.get('sourceObjectId', {}), required_type={'MESH'})
        max_deviation = finite_number(arguments.get('maxDeviation', 0.01), 'maxDeviation', positive=True)
        max_pole_valence = arguments.get('maxPoleValence', 5)
        if type(max_pole_valence) is not int or max_pole_valence < 3:
            raise HarnessError('INVALID_ARGUMENT', 'maxPoleValence must be an integer >= 3')

        import bmesh

        # Measure deviation: max distance from target vertex to nearest source vertex
        source_verts = [v.co.copy() for v in source.data.vertices]
        if not source_verts:
            raise HarnessError('INVALID_ARGUMENT', 'source mesh has no vertices for validation')
        import mathutils
        kd = mathutils.kdtree.KDTree(len(source_verts))
        for i, v in enumerate(source_verts):
            kd.insert(v, i)
        kd.balance()

        max_dist = 0.0
        total_dist = 0.0
        count = 0
        for vert in obj.data.vertices:
            _, _, dist = kd.find(vert.co)
            if dist is not None:
                total_dist += dist
                count += 1
                if dist > max_dist:
                    max_dist = dist
        avg_dist = total_dist / count if count > 0 else 0.0

        # Analyze pole valence (vertices with != 4 edges)
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            poles = []
            for vert in bm.verts:
                valence = len(vert.link_edges)
                if valence != 4:
                    if valence > max_pole_valence:
                        poles.append({'vertex': vert.index, 'valence': valence})
        finally:
            bm.free()

        # Determine status
        deviation_exceeded = max_dist > max_deviation
        poles_exceeded = len(poles) > 0

        if deviation_exceeded or poles_exceeded:
            status = 'handover'
            issues = []
            if deviation_exceeded:
                issues.append({'code': 'DEVIATION_EXCEEDED',
                               'maxDeviation': round(max_deviation, 6),
                               'measured': round(max_dist, 6)})
            if poles_exceeded:
                issues.append({'code': 'POLE_VALENCE_EXCEEDED',
                               'maxPoleValence': max_pole_valence,
                               'count': len(poles), 'poles': poles[:20]})
            return {'changedObjects': [], 'result': self.objects.receipt(obj) | {
                'status': status,
                'meanDeviation': round(avg_dist, 6),
                'maxDeviation': round(max_dist, 6),
                'poleCount': len(poles),
                'issues': issues,
                'handover': True,
                'handoverReason': 'Automatic retopology result does not meet quality thresholds; human editing required.'}}
        else:
            return {'changedObjects': [], 'result': self.objects.receipt(obj) | {
                'status': 'pass',
                'meanDeviation': round(avg_dist, 6),
                'maxDeviation': round(max_dist, 6),
                'poleCount': 0,
                'issues': [],
                'handover': False}}
