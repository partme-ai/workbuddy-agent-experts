"""Topology-bound UV seams, unwrap, packing and diagnostics."""
import math
from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .mesh import TOPOLOGY_VERSION_KEY
from .validation import finite_number


class UVCommands:
    def __init__(self,bpy_module):
        self.bpy=bpy_module; self.objects=ObjectResolver(bpy_module); self.context=OperationContext(bpy_module)

    def _selection(self,arguments):
        selection=arguments.get('selection')
        if not isinstance(selection,dict): raise HarnessError('INVALID_ARGUMENT','selection receipt is required')
        obj=self.objects.resolve({'objectId':selection.get('objectId')},required_type={'MESH'})
        if selection.get('topologyVersion') != int(obj.data.get(TOPOLOGY_VERSION_KEY,0)):
            raise HarnessError('STALE_TOPOLOGY_SELECTION','selection topology version no longer matches the mesh')
        return obj,selection

    def mark_seams(self,arguments):
        obj,selection=self._selection(arguments); edges=selection.get('edges',[])
        if not isinstance(edges,list) or not edges or any(type(i) is not int or not 0<=i<len(obj.data.edges) for i in edges):
            raise HarnessError('INVALID_ARGUMENT','selection must contain valid edges')
        seam=arguments.get('seam',True)
        if type(seam) is not bool: raise HarnessError('INVALID_ARGUMENT','seam must be boolean')
        for index in edges: obj.data.edges[index].use_seam=seam
        obj.data.update()
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'edges':edges,'seam':seam}}

    def _select_faces(self,obj,selection):
        import bmesh
        faces=selection.get('faces',[])
        if not isinstance(faces,list) or not faces or any(type(i) is not int for i in faces):
            raise HarnessError('INVALID_ARGUMENT','selection must contain faces')
        bm=bmesh.from_edit_mesh(obj.data); bm.faces.ensure_lookup_table()
        if any(not 0<=i<len(bm.faces) for i in faces): raise HarnessError('INVALID_ARGUMENT','face index is outside mesh')
        for face in bm.faces: face.select=False
        for index in faces: bm.faces[index].select=True
        bmesh.update_edit_mesh(obj.data,loop_triangles=False,destructive=False)

    def unwrap(self,arguments):
        obj,selection=self._selection(arguments); method=str(arguments.get('method','ANGLE_BASED')).upper()
        if method not in {'ANGLE_BASED','CONFORMAL'}: raise HarnessError('INVALID_ARGUMENT','unsupported unwrap method')
        margin=finite_number(arguments.get('margin',.001),'margin',minimum=0)
        with self.context.active_object(obj,mode='EDIT'):
            self._select_faces(obj,selection)
            result=self.bpy.ops.uv.unwrap(method=method,margin=margin)
            if result != {'FINISHED'}: raise HarnessError('OPERATION_FAILED','UV unwrap did not finish')
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'method':method}}

    def pack(self,arguments):
        obj,selection=self._selection(arguments); margin=finite_number(arguments.get('margin',.001),'margin',minimum=0)
        with self.context.active_object(obj,mode='EDIT'):
            self._select_faces(obj,selection)
            result=self.bpy.ops.uv.pack_islands(margin=margin)
            if result != {'FINISHED'}: raise HarnessError('OPERATION_FAILED','UV pack did not finish')
        return {'changedObjects':[obj.name],'result':self.objects.receipt(obj)|{'margin':margin}}

    def inspect(self,arguments):
        obj=self.objects.resolve(arguments,required_type={'MESH'}); layer=obj.data.uv_layers.active
        if layer is None:
            return {'changedObjects':[],'result':self.objects.receipt(obj)|{'hasUV':False,'issues':[{'code':'UV_MISSING'}]}}
        outside=[]; degenerate=[]
        for polygon in obj.data.polygons:
            uvs=[layer.data[index].uv for index in polygon.loop_indices]
            if any(value<0 or value>1 for uv in uvs for value in uv): outside.append(polygon.index)
            area=abs(sum(uvs[i].x*uvs[(i+1)%len(uvs)].y-uvs[(i+1)%len(uvs)].x*uvs[i].y for i in range(len(uvs)))/2)
            if area<=1e-12: degenerate.append(polygon.index)
        issues=[]
        if outside: issues.append({'code':'UV_OUT_OF_BOUNDS','faces':outside})
        if degenerate: issues.append({'code':'UV_DEGENERATE','faces':degenerate})
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'hasUV':True,'layer':layer.name,
            'outOfBoundsFaces':outside,'degenerateFaces':degenerate,'issues':issues,
            'limitations':['UV island overlap detection is available via uv.detect_overlap']}}

    # -- helpers for detect_overlap / measure_texel_density ------------------

    def _resolve_uv_layer(self, obj, arguments):
        """Return the UV layer to use: active when uvLayer is absent, named
        layer when present, or raise UV_LAYER_NOT_FOUND if the name is given
        but does not exist on the mesh."""
        layer_name = arguments.get('uvLayer')
        if layer_name is None:
            layer = obj.data.uv_layers.active
        else:
            layer = obj.data.uv_layers.get(layer_name)
            if layer is None:
                raise HarnessError('UV_LAYER_NOT_FOUND',
                                   f'UV layer {layer_name!r} not found on mesh')
        return layer

    @staticmethod
    def _uv_polygon_area(points):
        """Shoelace formula; returns absolute area."""
        n = len(points)
        if n < 3:
            return 0.0
        return abs(sum(points[i][0]*points[(i+1)%n][1]-points[(i+1)%n][0]*points[i][1]
                       for i in range(n)))/2

    @staticmethod
    def _cross2(ax, ay, bx, by):
        return ax*by - ay*bx

    @classmethod
    def _clip_polygon(cls, polygon, edge_start, edge_end):
        """Sutherland-Hodgman clip *polygon* against the half-plane defined
        by the directed edge from *edge_start* to *edge_end*.  Returns the
        clipped polygon (list of (x,y) tuples)."""
        ex = edge_end[0]-edge_start[0]
        ey = edge_end[1]-edge_start[1]
        result = []
        prev = polygon[-1]
        prev_inside = cls._cross2(ex, ey, prev[0]-edge_start[0], prev[1]-edge_start[1]) >= 0
        for pt in polygon:
            cur_inside = cls._cross2(ex, ey, pt[0]-edge_start[0], pt[1]-edge_start[1]) >= 0
            if cur_inside:
                if not prev_inside:
                    inter = cls._line_intersect(prev, pt, edge_start, edge_end)
                    if inter is not None:
                        result.append(inter)
                result.append(pt)
            elif prev_inside:
                inter = cls._line_intersect(prev, pt, edge_start, edge_end)
                if inter is not None:
                    result.append(inter)
            prev = pt
            prev_inside = cur_inside
        return result

    @staticmethod
    def _line_intersect(p1, p2, p3, p4):
        """Intersection of lines p1-p2 and p3-p4, or None if parallel."""
        d1x = p2[0]-p1[0]; d1y = p2[1]-p1[1]
        d2x = p4[0]-p3[0]; d2y = p4[1]-p3[1]
        denom = d1x*d2y - d1y*d2x
        if abs(denom) < 1e-15:
            return None
        t = ((p3[0]-p1[0])*d2y - (p3[1]-p1[1])*d2x)/denom
        return (p1[0]+t*d1x, p1[1]+t*d1y)

    @classmethod
    def _intersection_area(cls, poly_a, poly_b):
        """Area of intersection of two convex polygons (Sutherland-Hodgman)."""
        clipped = list(poly_a)
        n = len(poly_b)
        for i in range(n):
            clipped = cls._clip_polygon(clipped, poly_b[i], poly_b[(i+1)%n])
            if len(clipped) < 3:
                return 0.0
        return cls._uv_polygon_area(clipped)

    # -- detect_overlap ------------------------------------------------------

    def detect_overlap(self, arguments):
        """Detect UV island overlaps, reporting overlapping face pairs.

        UDIM handling: each face's tile is derived by flooring its mean UV
        coordinate.  Only faces on the same tile are compared.  A face that
        straddles a tile boundary is assigned to the tile of its centroid;
        this is a deliberate simplification consistent with most DCC tools.

        *tolerance* is the minimum intersection area for a pair to be
        reported; it guards against float-noise phantom overlaps.
        """
        obj = self.objects.resolve(arguments, required_type={'MESH'})
        layer = self._resolve_uv_layer(obj, arguments)
        if layer is None:
            return {'changedObjects':[], 'result':self.objects.receipt(obj)|{
                'hasUV':False, 'issues':[{'code':'UV_MISSING'}]}}
        tol = finite_number(arguments.get('tolerance', 1e-9), 'tolerance', minimum=0)

        # Collect per-face UV polygons and tile assignment.
        faces = []  # (index, uv_points, tile_key)
        degenerate = []
        for polygon in obj.data.polygons:
            uvs = [layer.data[i].uv for i in polygon.loop_indices]
            pts = [(uv.x, uv.y) for uv in uvs]
            area = self._uv_polygon_area(pts)
            if area <= 1e-12:
                degenerate.append(polygon.index)
                continue
            # Tile from centroid: floor of mean UV.
            cx = sum(p[0] for p in pts)/len(pts)
            cy = sum(p[1] for p in pts)/len(pts)
            tile = (math.floor(cx), math.floor(cy))
            faces.append((polygon.index, pts, tile))

        # Group by tile.
        tiles = {}
        for idx, pts, tile in faces:
            tiles.setdefault(tile, []).append((idx, pts))

        # Pairwise intersection within each tile.
        overlaps = []
        for tile_key, group in tiles.items():
            n = len(group)
            for a in range(n):
                for b in range(a+1, n):
                    ia, pa = group[a]
                    ib, pb = group[b]
                    inter = self._intersection_area(pa, pb)
                    if inter > tol:
                        area_a = self._uv_polygon_area(pa)
                        area_b = self._uv_polygon_area(pb)
                        min_area = min(area_a, area_b)
                        ratio = inter/min_area if min_area > 1e-15 else 0.0
                        overlaps.append({
                            'faceA': ia, 'faceB': ib,
                            'area': round(inter, 12), 'ratio': round(ratio, 12),
                        })

        overlaps.sort(key=lambda o: o['area'], reverse=True)
        limitations = ['Intersection area assumes convex UV polygons; '
                       'concave n-gons may produce incorrect results']
        return {'changedObjects':[], 'result':self.objects.receipt(obj)|{
            'hasUV':True, 'layer':layer.name,
            'hasOverlaps':len(overlaps)>0, 'overlaps':overlaps,
            'degenerateFaces':degenerate,
            'issues':([{'code':'UV_DEGENERATE','faces':degenerate}] if degenerate else []),
            'limitations':limitations}}

    # -- measure_texel_density ------------------------------------------------

    def measure_texel_density(self, arguments):
        """Measure per-face texel density.

        Definition: texelDensity = sqrt(W * H * uvArea / threeDArea)
        where W, H are the texture pixel dimensions.  This gives the
        geometric-mean pixels-per-unit-3D-distance, which is the standard
        metric used in game production.
        """
        obj = self.objects.resolve(arguments, required_type={'MESH'})
        layer = self._resolve_uv_layer(obj, arguments)
        if layer is None:
            return {'changedObjects':[], 'result':self.objects.receipt(obj)|{
                'hasUV':False, 'issues':[{'code':'UV_MISSING'}]}}
        tw = finite_number(arguments.get('textureWidth'), 'textureWidth', positive=True)
        th = finite_number(arguments.get('textureHeight'), 'textureHeight', positive=True)
        tw = int(tw); th = int(th)

        faces = []
        for polygon in obj.data.polygons:
            # UV area
            uvs = [layer.data[i].uv for i in polygon.loop_indices]
            uv_pts = [(uv.x, uv.y) for uv in uvs]
            uv_area = self._uv_polygon_area(uv_pts)
            # 3D area (cross-product method)
            verts = [obj.data.vertices[i].co for i in polygon.vertices]
            three_d = self._polygon_area_3d(verts)
            td = math.sqrt(tw*th*uv_area/three_d) if three_d > 1e-15 else None
            faces.append({'face':polygon.index, 'texelDensity':round(td,6) if td is not None else None,
                          'uvArea':round(uv_area,12), 'threeDArea':round(three_d,12)})

        td_val = arguments.get('targetDensity')
        target = finite_number(td_val, 'targetDensity', positive=True) if td_val is not None else None
        result = self.objects.receipt(obj)|{'hasUV':True,'layer':layer.name,
            'textureWidth':tw,'textureHeight':th,'faces':faces}
        if target is not None:
            result['targetDensity'] = target
        return {'changedObjects':[], 'result':result}

    @staticmethod
    def _polygon_area_3d(verts):
        """Area of a polygon in 3D via cross-product summation."""
        n = len(verts)
        if n < 3:
            return 0.0
        ax, ay, az = verts[0]
        total = 0.0
        for i in range(1, n-1):
            bx, by, bz = verts[i]
            cx, cy, cz = verts[i+1]
            ex1, ey1, ez1 = bx-ax, by-ay, bz-az
            ex2, ey2, ez2 = cx-ax, cy-ay, cz-az
            total += math.sqrt((ey1*ez2-ez1*ey2)**2+(ez1*ex2-ex1*ez2)**2+(ex1*ey2-ey1*ex2)**2)
        return total/2
