"""Native Blender Hair Curves creation, grooming, inspection and validation."""
import math

from ..errors import HarnessError
from ..identity import ObjectResolver
from ..operation_context import OperationContext
from .validation import finite_number,require_name,vector3

_GROOM_OPS = {'COMB', 'CUT', 'LENGTH', 'CLUMP', 'NOISE', 'SMOOTH'}


class HairCommands:
    def __init__(self,bpy_module):self.bpy=bpy_module;self.objects=ObjectResolver(bpy_module);self.context=OperationContext(bpy_module)
    def create_curves(self,args):
        surface=self.objects.resolve(args.get('surface'),required_type={'MESH'});name=require_name(args.get('name'));strands=args.get('strands')
        if self.bpy.data.objects.get(name):raise HarnessError('NAME_COLLISION',f'object already exists: {name}')
        if not isinstance(strands,list) or not strands:raise HarnessError('INVALID_ARGUMENT','strands must be a non-empty list')
        parsed=[]
        for strand in strands:
            if not isinstance(strand,list) or len(strand)<2:raise HarnessError('INVALID_ARGUMENT','each strand requires at least two points')
            parsed.append([vector3(point,'strand point') for point in strand])
        radius=finite_number(args.get('radius',.005),'radius',positive=True)
        with self.context.active_object(surface):
            result=self.bpy.ops.object.curves_empty_hair_add()
            if result!={'FINISHED'}:raise HarnessError('OPERATION_FAILED','hair creation did not finish')
            hair=self.bpy.context.object;hair.name=name
            hair.data.add_curves([len(strand) for strand in parsed])
            flattened=[value for strand in parsed for point in strand for value in point]
            hair.data.attributes['position'].data.foreach_set('vector',flattened)
            radius_attr=hair.data.attributes.get('radius') or hair.data.attributes.new('radius','FLOAT','POINT')
            for item in radius_attr.data:item.value=radius
            hair.data.surface=surface
        return {'changedObjects':[name],'result':self.objects.receipt(hair)|{'surface':self.objects.receipt(surface),'strands':len(parsed),'points':sum(map(len,parsed))}}

    def groom(self, args):
        """Groom hair curves by applying a styling operation.

        Parameters
        ----------
        objectId : str
            Object locator for the hair curves object (type CURVES).
        operation : str
            One of: COMB, CUT, LENGTH, CLUMP, NOISE, SMOOTH.
        strength : float
            Intensity of the operation (finite number; meaning varies per op).
        selection : dict, optional
            Object specifying which strands are affected.  Must contain
            ``curves`` -- a list of integer curve indices (0-based) into the
            curves object.  When absent, all strands are affected.

            Example::

                {"curves": [0, 2, 5]}

        Operation semantics (all edit ``position`` attribute in-place):

        * COMB  -- move each point toward the direction vector scaled by
          ``strength``.  The direction is computed from the tangent at the
          strand root.
        * CUT   -- for each selected strand, if the strand length exceeds
          ``strength`` units, truncate it to that length by removing the
          farthest points.  The strand must retain at least 2 points.
        * LENGTH -- scale each point's position along the strand direction
          by ``1 + strength`` (positive = grow, negative = shrink).
        * CLUMP -- move every non-root point toward the strand's root
          position by ``strength`` fraction of the current distance.
        * NOISE  -- add a deterministic pseudo-random offset (seeded by
          curve index) of amplitude ``strength`` to each point.
        * SMOOTH -- Laplacian smooth: each interior point is moved toward
          the average of its neighbours by ``strength`` fraction.
        """
        oid = args.get('objectId')
        obj = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'CURVES'})
        operation = str(args.get('operation', '')).upper()
        if operation not in _GROOM_OPS:
            raise HarnessError('INVALID_ARGUMENT', f'operation must be one of {sorted(_GROOM_OPS)}')
        strength = finite_number(args.get('strength', 0.1), 'strength')

        # Parse selection
        selection_arg = args.get('selection')
        curves_data = obj.data
        total_curves = len(curves_data.curves)
        if selection_arg is not None:
            if not isinstance(selection_arg, dict):
                raise HarnessError('INVALID_ARGUMENT', 'selection must be an object with a "curves" list')
            curve_indices = selection_arg.get('curves')
            if not isinstance(curve_indices, list):
                raise HarnessError('INVALID_ARGUMENT', 'selection.curves must be a list of integer indices')
            for idx in curve_indices:
                if not isinstance(idx, int) or idx < 0 or idx >= total_curves:
                    raise HarnessError('INVALID_ARGUMENT', f'selection curve index {idx} is out of range [0, {total_curves})')
            selected = set(curve_indices)
        else:
            selected = None  # all

        # Read positions
        positions = curves_data.attributes['position']
        import mathutils
        changed = 0
        for curve_idx, curve in enumerate(curves_data.curves):
            if selected is not None and curve_idx not in selected:
                continue
            first = curve.first_point_index
            npts = curve.points_length
            pts = []
            for i in range(npts):
                v = positions.data[first + i].vector
                pts.append(mathutils.Vector(v))

            if operation == 'COMB':
                # Direction: tangent at root = normalize(point[1] - point[0])
                if npts >= 2:
                    direction = (pts[1] - pts[0]).normalized()
                    for i in range(npts):
                        pts[i] += direction * strength
            elif operation == 'CUT':
                # Truncate strand to length <= abs(strength)
                target_len = abs(strength)
                cumulative = 0.0
                keep = 1
                for i in range(1, npts):
                    seg = (pts[i] - pts[i - 1]).length
                    cumulative += seg
                    if cumulative > target_len:
                        break
                    keep = i + 1
                if keep < 2:
                    keep = 2
                if keep < npts:
                    # Resize curve -- Blender doesn't easily support per-curve
                    # resize without recreating; we move extra points onto last kept
                    for i in range(keep, npts):
                        positions.data[first + i].vector = pts[keep - 1]
                changed += 1
                continue  # skip writing back below
            elif operation == 'LENGTH':
                # Scale each point's offset from root by (1 + strength)
                if npts >= 2:
                    root = pts[0]
                    factor = 1.0 + strength
                    for i in range(1, npts):
                        offset = pts[i] - root
                        pts[i] = root + offset * factor
            elif operation == 'CLUMP':
                root = pts[0]
                for i in range(1, npts):
                    toward = root - pts[i]
                    pts[i] += toward * strength
            elif operation == 'NOISE':
                import random
                rng = random.Random(curve_idx * 31337)
                for i in range(npts):
                    dx = rng.uniform(-1, 1) * strength
                    dy = rng.uniform(-1, 1) * strength
                    dz = rng.uniform(-1, 1) * strength
                    pts[i] += mathutils.Vector((dx, dy, dz))
            elif operation == 'SMOOTH':
                if npts >= 3:
                    orig = [p.copy() for p in pts]
                    for i in range(1, npts - 1):
                        avg = (orig[i - 1] + orig[i + 1]) / 2.0
                        pts[i] += (avg - pts[i]) * strength

            # Write positions back
            for i in range(npts):
                positions.data[first + i].vector = pts[i]
            changed += 1

        return {'changedObjects': [obj.name], 'result': self.objects.receipt(obj) | {
            'operation': operation, 'strength': strength, 'affectedCurves': changed}}

    def validate(self, args):
        """Validate hair curves: surface binding, NaN coordinates, strand length.

        Parameters
        ----------
        objectId : str
            Object locator for the curves object.
        surfaceObjectId : str
            Object locator for the expected surface mesh.
        limits : dict, optional
            Thresholds for the check.  Keys:
            * ``maxStrandLength`` (float, default 10.0) -- strands longer
              than this are reported as absurd.

        Returns
        -------
        dict with keys:
            * ``passed`` (bool) -- True only when every check passes.
            * ``totalStrands`` (int)
            * ``totalPoints`` (int)
            * ``unboundStrands`` (int) -- strands whose curves-object surface
              is not set or differs from the expected surface.
            * ``nanPoints`` (int) -- points with any NaN coordinate.
            * ``infiniteLengths`` (int) -- strands with any infinite or NaN
              segment length.
            * ``absurdLengths`` (int) -- strands whose total arc length
              exceeds ``limits.maxStrandLength``.
            * ``limits`` (dict) -- the thresholds actually applied, named
              explicitly so no value is implied.
            * ``details`` (list) -- per-strand report for failing strands,
              each entry: ``{curveIndex, issues: [str]}``.
        """
        import mathutils as _mu

        oid = args.get('objectId')
        obj = self.objects.resolve(oid if isinstance(oid, dict) else {'objectId': oid}, required_type={'CURVES'})
        sid = args.get('surfaceObjectId')
        surface = self.objects.resolve(sid if isinstance(sid, dict) else {'objectId': sid}, required_type={'MESH'})
        limits_arg = args.get('limits') or {}
        max_strand_length = finite_number(limits_arg.get('maxStrandLength', 10.0), 'limits.maxStrandLength', positive=True)

        curves_data = obj.data
        total_curves = len(curves_data.curves)
        total_points = len(curves_data.points)

        # 1. Surface binding
        actual_surface = curves_data.surface
        unbound = 0
        if actual_surface is None or actual_surface.name != surface.name:
            unbound = total_curves

        # 2. NaN / infinite / absurd
        positions = curves_data.attributes['position']
        nan_points = 0
        infinite_lengths = 0
        absurd_lengths = 0
        details = []

        for curve_idx, curve in enumerate(curves_data.curves):
            first = curve.first_point_index
            npts = curve.points_length
            issues = []
            strand_length = 0.0
            has_nan = False
            has_inf = False

            prev = None
            for i in range(npts):
                v = positions.data[first + i].vector
                if any(math.isnan(c) for c in v):
                    nan_points += 1
                    has_nan = True
                if prev is not None:
                    seg = (_mu.Vector(v) - prev).length
                    if math.isnan(seg) or math.isinf(seg):
                        infinite_lengths += 1
                        has_inf = True
                    else:
                        strand_length += seg
                prev = _mu.Vector(v)

            if has_nan:
                issues.append('NaN_COORDINATE')
            if has_inf:
                issues.append('INFINITE_SEGMENT')
            if strand_length > max_strand_length:
                absurd_lengths += 1
                issues.append('ABSURD_LENGTH')

            if issues:
                details.append({'curveIndex': curve_idx, 'issues': issues})

        passed = (unbound == 0 and nan_points == 0 and infinite_lengths == 0 and absurd_lengths == 0)
        applied_limits = {'maxStrandLength': max_strand_length}
        return {'changedObjects': [], 'result': self.objects.receipt(obj) | {
            'passed': passed,
            'totalStrands': total_curves,
            'totalPoints': total_points,
            'unboundStrands': unbound,
            'nanPoints': nan_points,
            'infiniteLengths': infinite_lengths,
            'absurdLengths': absurd_lengths,
            'limits': applied_limits,
            'details': details,
        }}

    def inspect(self,args):
        obj=self.objects.resolve(args,required_type={'CURVES'});data=obj.data
        return {'changedObjects':[],'result':self.objects.receipt(obj)|{'strands':len(data.curves),'points':len(data.points),
          'surface':self.objects.receipt(data.surface) if data.surface else None}}
