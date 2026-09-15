"""Version-bound mesh selection, BMesh editing and topology diagnostics."""
import math

from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number, vector3


TOPOLOGY_VERSION_KEY = 'codex_blender_topology_version'


class MeshCommands:
    def __init__(self, bpy_module):
        self.bpy = bpy_module
        self.objects = ObjectResolver(bpy_module)
        self.context = OperationContext(bpy_module)

    def _object(self, arguments):
        return self.objects.resolve(arguments, required_type={'MESH'})

    @staticmethod
    def _version(mesh):
        return int(mesh.get(TOPOLOGY_VERSION_KEY, 0))

    @staticmethod
    def _indices(elements):
        return sorted(element.index for element in elements)

    def inspect(self, arguments):
        import bmesh
        obj = self._object(arguments)
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
            tolerance = finite_number(arguments.get('tolerance', 1e-6), 'tolerance', positive=True)
            buckets = {}
            for vert in bm.verts:
                key = tuple(round(float(value) / tolerance) for value in vert.co)
                buckets.setdefault(key, []).append(vert.index)
            duplicates = [indices for indices in buckets.values() if len(indices) > 1]
            degenerate_faces = [face.index for face in bm.faces if face.calc_area() <= tolerance * tolerance]
            non_manifold = [edge.index for edge in bm.edges if not edge.is_manifold]
            open_allowed = arguments.get('allowOpenSurface', False)
            if type(open_allowed) is not bool:
                raise HarnessError('INVALID_ARGUMENT', 'allowOpenSurface must be boolean')
            issues = []
            if duplicates: issues.append({'code': 'DUPLICATE_VERTICES', 'count': len(duplicates)})
            if degenerate_faces: issues.append({'code': 'DEGENERATE_FACES', 'count': len(degenerate_faces)})
            if non_manifold: issues.append({'code': 'OPEN_OR_NON_MANIFOLD_EDGES', 'count': len(non_manifold),
                                            'severity': 'info' if open_allowed else 'error'})
            scale = [float(value) for value in obj.scale]
            if any(abs(value) <= tolerance for value in scale):
                issues.append({'code': 'DEGENERATE_OBJECT_SCALE', 'severity': 'error'})
            elif any(abs(value - 1) > tolerance for value in scale):
                issues.append({'code': 'UNAPPLIED_OBJECT_SCALE', 'severity': 'warning'})
            return {'changedObjects': [], 'result': self.objects.receipt(obj) | {
                'topologyVersion': self._version(obj.data),
                'counts': {'vertices': len(bm.verts), 'edges': len(bm.edges), 'faces': len(bm.faces)},
                'duplicateVertexGroups': duplicates, 'degenerateFaces': degenerate_faces,
                'nonManifoldEdges': non_manifold, 'allowOpenSurface': open_allowed, 'issues': issues}}
        finally:
            bm.free()

    def select(self, arguments):
        import bmesh
        obj = self._object(arguments)
        method = str(arguments.get('method', '')).lower()
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
            verts, edges, faces = set(), set(), set()
            if method == 'indices':
                for field, source, target in (('vertices', bm.verts, verts), ('edges', bm.edges, edges), ('faces', bm.faces, faces)):
                    values = arguments.get(field, [])
                    if not isinstance(values, list) or any(type(index) is not int or index < 0 or index >= len(source) for index in values):
                        raise HarnessError('INVALID_ARGUMENT', f'{field} must contain valid element indices')
                    target.update(source[index] for index in values)
            elif method == 'spatial':
                lower, upper = vector3(arguments.get('min'), 'min'), vector3(arguments.get('max'), 'max')
                if any(a > b for a, b in zip(lower, upper)):
                    raise HarnessError('INVALID_ARGUMENT', 'min must not exceed max')
                verts.update(v for v in bm.verts if all(a <= value <= b for value, a, b in zip(v.co, lower, upper)))
            elif method == 'connected':
                seed = arguments.get('seedVertex')
                if type(seed) is not int or not 0 <= seed < len(bm.verts):
                    raise HarnessError('INVALID_ARGUMENT', 'seedVertex is outside the mesh')
                pending = [bm.verts[seed]]
                while pending:
                    vert = pending.pop()
                    if vert in verts: continue
                    verts.add(vert)
                    pending.extend(edge.other_vert(vert) for edge in vert.link_edges)
            elif method == 'normal':
                from mathutils import Vector
                direction = Vector(vector3(arguments.get('direction'), 'direction'))
                if direction.length == 0:
                    raise HarnessError('INVALID_ARGUMENT', 'direction must be non-zero')
                tolerance = finite_number(arguments.get('angleDegrees', 5), 'angleDegrees', minimum=0)
                if tolerance > 180:
                    raise HarnessError('INVALID_ARGUMENT', 'angleDegrees must not exceed 180')
                threshold = math.cos(math.radians(tolerance))
                direction.normalize()
                faces.update(face for face in bm.faces if face.normal.dot(direction) >= threshold)
            else:
                raise HarnessError('INVALID_ARGUMENT', 'method must be indices, spatial, connected or normal')
            for face in faces: verts.update(face.verts); edges.update(face.edges)
            for edge in edges: verts.update(edge.verts)
            return {'changedObjects': [], 'result': self.objects.receipt(obj) | {
                'topologyVersion': self._version(obj.data), 'vertices': self._indices(verts),
                'edges': self._indices(edges), 'faces': self._indices(faces)}}
        finally:
            bm.free()

    def _bound_selection(self, obj, selection, bm):
        if not isinstance(selection, dict) or selection.get('topologyVersion') != self._version(obj.data):
            raise HarnessError('STALE_TOPOLOGY_SELECTION', 'selection topology version no longer matches the mesh')
        if selection.get('objectId') != self.objects.ensure_id(obj):
            raise HarnessError('OBJECT_ID_MISMATCH', 'selection belongs to a different object')
        result = {}
        for field, source in (('vertices', bm.verts), ('edges', bm.edges), ('faces', bm.faces)):
            values = selection.get(field, [])
            if not isinstance(values, list) or any(type(index) is not int or not 0 <= index < len(source) for index in values):
                raise HarnessError('INVALID_ARGUMENT', f'selection {field} are invalid')
            result[field] = [source[index] for index in values]
        return result

    def edit(self, arguments):
        import bmesh
        from mathutils import Vector
        selection = arguments.get('selection')
        locator = {'objectId': selection.get('objectId')} if isinstance(selection, dict) else {}
        obj = self._object(locator)
        operation = str(arguments.get('operation', '')).lower()
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
            selected = self._bound_selection(obj, selection, bm)
            verts, edges, faces = selected['vertices'], selected['edges'], selected['faces']
            if operation == 'extrude':
                if not faces: raise HarnessError('INVALID_ARGUMENT', 'extrude requires selected faces')
                result = bmesh.ops.extrude_face_region(bm, geom=faces)
                new_verts = [item for item in result['geom'] if isinstance(item, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=new_verts, vec=Vector(vector3(arguments.get('offset'), 'offset')))
            elif operation == 'inset':
                if not faces: raise HarnessError('INVALID_ARGUMENT', 'inset requires selected faces')
                bmesh.ops.inset_region(bm, faces=faces,
                    thickness=finite_number(arguments.get('thickness'), 'thickness', minimum=0),
                    depth=finite_number(arguments.get('depth', 0), 'depth'), use_even_offset=True)
            elif operation == 'bevel':
                geom = list(dict.fromkeys([*edges, *verts]))
                if not geom: raise HarnessError('INVALID_ARGUMENT', 'bevel requires selected vertices or edges')
                segments = arguments.get('segments', 1)
                if type(segments) is not int or segments < 1: raise HarnessError('INVALID_ARGUMENT', 'segments must be positive')
                bmesh.ops.bevel(bm, geom=geom, offset=finite_number(arguments.get('width'), 'width', positive=True),
                                segments=segments, affect='EDGES')
            elif operation == 'subdivide':
                if not edges: raise HarnessError('INVALID_ARGUMENT', 'subdivide requires selected edges')
                cuts = arguments.get('cuts', 1)
                if type(cuts) is not int or cuts < 1: raise HarnessError('INVALID_ARGUMENT', 'cuts must be positive')
                bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
            elif operation == 'bridge':
                if len(edges) < 2: raise HarnessError('INVALID_ARGUMENT', 'bridge requires two selected edge loops')
                bmesh.ops.bridge_loops(bm, edges=edges)
            elif operation == 'weld':
                target = verts or list(bm.verts)
                bmesh.ops.remove_doubles(bm, verts=target,
                                         dist=finite_number(arguments.get('distance', 0.0001), 'distance', positive=True))
            elif operation == 'delete':
                geom = faces or edges or verts
                if not geom: raise HarnessError('INVALID_ARGUMENT', 'delete requires selected elements')
                context = 'FACES' if faces else 'EDGES' if edges else 'VERTS'
                bmesh.ops.delete(bm, geom=geom, context=context)
            elif operation == 'triangulate':
                if not faces: raise HarnessError('INVALID_ARGUMENT', 'triangulate requires selected faces')
                bmesh.ops.triangulate(bm, faces=faces)
            elif operation == 'recalculate_normals':
                target = faces or list(bm.faces)
                bmesh.ops.recalc_face_normals(bm, faces=target)
            else:
                raise HarnessError('INVALID_ARGUMENT', 'unsupported mesh edit operation')
            bm.normal_update()
            bm.to_mesh(obj.data)
            obj.data[TOPOLOGY_VERSION_KEY] = self._version(obj.data) + 1
            obj.data.update()
            return {'changedObjects': [obj.name], 'result': self.objects.receipt(obj) | {
                'topologyVersion': self._version(obj.data), 'operation': operation}}
        except HarnessError:
            raise
        except Exception as exc:
            raise HarnessError('OPERATION_FAILED', f'mesh {operation} failed') from exc
        finally:
            bm.free()
