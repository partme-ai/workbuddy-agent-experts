"""Versioned recipes composed exclusively from registered structured commands."""
from ..errors import HarnessError
from .validation import finite_number, require_name, vector3


class RecipeCommands:
    VERSION = '1.0.0'

    def __init__(self, bpy_module, dispatch):
        self.bpy = bpy_module; self.dispatch = dispatch

    def _ensure_names_free(self, names):
        collisions = [name for name in names if self.bpy.data.objects.get(name)]
        if collisions: raise HarnessError('NAME_COLLISION', f'recipe object names already exist: {collisions}')

    def hard_surface_shell(self, arguments):
        name=require_name(arguments.get('name')); dimensions=vector3(arguments.get('dimensions'),'dimensions')
        if any(value<=0 for value in dimensions): raise HarnessError('INVALID_ARGUMENT','dimensions must be positive')
        wall=finite_number(arguments.get('wallThickness'),'wallThickness',positive=True)
        bevel=finite_number(arguments.get('bevelWidth',min(dimensions)*.02),'bevelWidth',minimum=0)
        if wall*2>=min(dimensions): raise HarnessError('INVALID_ARGUMENT','wallThickness is too large')
        helper=name+'__Cutout'; self._ensure_names_free([name,helper])
        changed=[]
        try:
            outer=self.dispatch('object.create_mesh',{'name':name,'primitive':'cube','scale':[v/2 for v in dimensions]})['result']; changed.append(name)
            self.dispatch('object.apply_transform',{'objectId':outer['objectId'],'scale':True})
            inner_size=[dimensions[0]-2*wall,dimensions[1]-2*wall,dimensions[2]]
            inner=self.dispatch('object.create_mesh',{'name':helper,'primitive':'cube','location':[0,0,wall],
                'scale':[v/2 for v in inner_size]})['result']; changed.append(helper)
            self.dispatch('object.apply_transform',{'objectId':inner['objectId'],'scale':True})
            boolean=self.dispatch('modifier.add',{'objectId':outer['objectId'],'modifier':'BOOLEAN',
                'modifierName':'Shell Cutout','settings':{'operation':'DIFFERENCE','solver':'EXACT','object':{'objectId':inner['objectId']}}})['result']
            bevel_result=None
            if bevel>0:
                bevel_result=self.dispatch('modifier.add',{'objectId':outer['objectId'],'modifier':'BEVEL',
                    'modifierName':'Edge Bevel','settings':{'width':bevel,'segments':3}})['result']
            self.dispatch('object.set_visibility',{'objectId':inner['objectId'],'render':False,'viewport':True})
            self.dispatch('object.set_display',{'objectId':inner['objectId'],'displayType':'WIRE','showInFront':False})
            return {'changedObjects':changed,'result':{'recipe':'hard_surface_shell','recipeVersion':self.VERSION,
                'shell':outer,'helper':inner,'dimensions':dimensions,'wallThickness':wall,
                'modifiers':[boolean, *([bevel_result] if bevel_result else [])],
                'editable':True,'validation':self.dispatch('mesh.inspect',{'objectId':outer['objectId']})['result']}}
        except Exception:
            for object_name in reversed(changed):
                obj=self.bpy.data.objects.get(object_name)
                if obj is not None: self.bpy.data.objects.remove(obj,do_unlink=True)
            raise

    def spear(self, arguments):
        name=require_name(arguments.get('name')); length=finite_number(arguments.get('length'),'length',positive=True)
        radius=finite_number(arguments.get('shaftRadius'),'shaftRadius',positive=True)
        head_length=finite_number(arguments.get('headLength'),'headLength',positive=True)
        head_radius=finite_number(arguments.get('headRadius'),'headRadius',positive=True)
        if head_length>=length: raise HarnessError('INVALID_ARGUMENT','headLength must be shorter than length')
        shaft_name,head_name=name+'__Shaft',name+'__Head'; self._ensure_names_free([name,shaft_name,head_name])
        changed=[]
        try:
            shaft_length=length-head_length
            shaft=self.dispatch('object.create_mesh',{'name':shaft_name,'primitive':'cylinder',
                'location':[0,0,-head_length/2],'scale':[radius,radius,shaft_length/2]})['result']; changed.append(shaft_name)
            head=self.dispatch('object.create_mesh',{'name':head_name,'primitive':'cone',
                'location':[0,0,length/2-head_length/2],'scale':[head_radius,head_radius,head_length/2]})['result']; changed.append(head_name)
            for item in (shaft,head): self.dispatch('object.apply_transform',{'objectId':item['objectId'],'scale':True})
            spear=self.dispatch('object.join',{'objects':[{'objectId':shaft['objectId']},{'objectId':head['objectId']}],
                                               'newName':name})['result']
            bevel=self.dispatch('modifier.add',{'objectId':spear['objectId'],'modifier':'BEVEL',
                'modifierName':'Spear Edge Bevel','settings':{'width':min(radius*.25,.01),'segments':2}})['result']
            return {'changedObjects':[shaft_name,head_name,name],'result':{'recipe':'spear','recipeVersion':self.VERSION,
                'spear':spear,'length':length,'shaftRadius':radius,'headLength':head_length,'headRadius':head_radius,
                'modifiers':[bevel],'singleObject':True,
                'validation':self.dispatch('mesh.inspect',{'objectId':spear['objectId']})['result']}}
        except Exception:
            for object_name in (name,head_name,shaft_name):
                obj=self.bpy.data.objects.get(object_name)
                if obj is not None: self.bpy.data.objects.remove(obj,do_unlink=True)
            raise

    def desktop_speaker(self,arguments):
        name=require_name(arguments.get('name')); dims=vector3(arguments.get('dimensions'),'dimensions')
        if any(v<=0 for v in dims): raise HarnessError('INVALID_ARGUMENT','dimensions must be positive')
        bevel=finite_number(arguments.get('bevelWidth',.015),'bevelWidth',minimum=0)
        wall=finite_number(arguments.get('wallThickness',.018),'wallThickness',positive=True)
        w,d,h=dims
        if wall*2>=min(dims):raise HarnessError('INVALID_ARGUMENT','wallThickness is too large')
        definitions=[
          ('Housing','cube',[0,0,h/2],[w/2,d/2,h/2]),
          ('Grille','cube',[0,-d/2-.012,h*.53],[w*.39,.012,h*.31]),
          ('Knob','cylinder',[w*.3,-d/2-.035,h*.82],[w*.045,.025,w*.045]),
          ('Interface','cylinder',[-w*.3,d/2+.025,h*.25],[w*.035,.02,w*.035]),
          ('Base','cube',[0,0,.025],[w*.42,d*.42,.025]),
        ]
        names=[name+'_'+suffix for suffix,*_ in definitions];cavity_name=name+'_HousingCavity';self._ensure_names_free([*names,cavity_name])
        materials={'Housing':([.12,.14,.18,1],.25,.28),'Grille':([.025,.03,.035,1],.05,.6),
                   'Knob':([.55,.58,.62,1],.75,.2),'Interface':([.015,.015,.018,1],.1,.45),
                   'Base':([.06,.065,.075,1],.1,.55)}
        created=[]
        try:
            parts={}
            for suffix,primitive,location,scale in definitions:
                part=self.dispatch('object.create_mesh',{'name':name+'_'+suffix,'primitive':primitive,
                    'location':location,'scale':scale,
                    **({'rotation':[1.5707963267948966,0,0]} if primitive=='cylinder' else {})})['result']
                created.append(part['name']); parts[suffix]=part
                self.dispatch('object.apply_transform',{'objectId':part['objectId'],'scale':True})
            cavity=self.dispatch('object.create_mesh',{'name':cavity_name,'primitive':'cube','location':[0,0,h/2],
                'scale':[w/2-wall,d/2-wall,h/2-wall]})['result'];created.append(cavity['name'])
            self.dispatch('object.apply_transform',{'objectId':cavity['objectId'],'scale':True})
            self.dispatch('modifier.add',{'objectId':parts['Housing']['objectId'],'modifier':'BOOLEAN','modifierName':'Internal Cavity',
                'settings':{'operation':'DIFFERENCE','solver':'EXACT','object':{'objectId':cavity['objectId']}}})
            self.dispatch('object.set_visibility',{'objectId':cavity['objectId'],'render':False,'viewport':True})
            self.dispatch('object.set_display',{'objectId':cavity['objectId'],'displayType':'WIRE'})
            for suffix,primitive,location,scale in definitions:
                part=parts[suffix]
                self.dispatch('modifier.add',{'objectId':part['objectId'],'modifier':'BEVEL',
                    'modifierName':'Manufactured Bevel','settings':{'width':min(bevel,min(scale)*.4),'segments':3}})
            self.dispatch('modifier.add',{'objectId':parts['Housing']['objectId'],'modifier':'SUBDIVISION',
                'modifierName':'Surface Subdivision','settings':{'levels':1,'render_levels':1}})
            for suffix,(color,metallic,roughness) in materials.items():
                material_name=name+'_'+suffix+'_Mat'
                self.dispatch('material.create_pbr',{'name':material_name,'baseColor':color,'metallic':metallic,'roughness':roughness})
                self.dispatch('material.assign',{'object':parts[suffix]['name'],'material':material_name})
            for suffix in ('Housing','Grille'):
                info=self.dispatch('mesh.inspect',{'objectId':parts[suffix]['objectId']})['result']
                selection=self.dispatch('mesh.select',{'objectId':parts[suffix]['objectId'],'method':'indices',
                    'edges':[0,1,2,3],'faces':list(range(info['counts']['faces']))})['result']
                self.dispatch('uv.mark_seams',{'selection':selection,'seam':True})
                self.dispatch('uv.unwrap',{'selection':selection,'method':'ANGLE_BASED','margin':.01})
                self.dispatch('uv.pack',{'selection':selection,'margin':.01})
            return {'changedObjects':created,'result':{'recipe':'desktop_speaker','recipeVersion':self.VERSION,
                'name':name,'dimensions':dims,'wallThickness':wall,'parts':parts,'helper':cavity,'editable':True,
                'modifierOrder':{'Housing':['BOOLEAN','BEVEL','SUBSURF']},
                'uv':{suffix:self.dispatch('uv.inspect',{'objectId':parts[suffix]['objectId']})['result'] for suffix in ('Housing','Grille')}}}
        except Exception:
            for object_name in reversed(created):
                obj=self.bpy.data.objects.get(object_name)
                if obj is not None:self.bpy.data.objects.remove(obj,do_unlink=True)
            raise

    def rigged_spear_character(self,arguments):
        name=require_name(arguments.get('name')); height=finite_number(arguments.get('height',2.2),'height',positive=True)
        release=arguments.get('releaseFrame',61); apex=arguments.get('apexFrame',75); catch=arguments.get('catchFrame',90)
        if any(type(v) is not int for v in (release,apex,catch)) or not 1<release<apex<catch:
            raise HarnessError('INVALID_ARGUMENT','throw frames must be increasing integers')
        scale=height/2.2; body_name=name+'_Body'; rig_name=name+'_Rig'; spear_name=name+'_Spear'
        segments=[
          ('Torso','cube',[0,0,1.42],[.29,.16,.38],[0,0,0],'spine'),
          ('Head','sphere',[0,0,2.02],[.18,.18,.21],[0,0,0],'head'),
          ('UpperArmR','cylinder',[.42,0,1.64],[.10,.10,.25],[0,1.57079632679,0],'upper_arm.R'),
          ('LowerArmR','cylinder',[.82,0,1.47],[.085,.085,.23],[0,1.57079632679,0],'lower_arm.R'),
          ('HandR','sphere',[1.05,0,1.36],[.105,.09,.11],[0,0,0],'hand.R'),
          ('UpperArmL','cylinder',[-.42,0,1.64],[.10,.10,.25],[0,1.57079632679,0],'upper_arm.L'),
          ('LowerArmL','cylinder',[-.82,0,1.47],[.085,.085,.23],[0,1.57079632679,0],'lower_arm.L'),
          ('HandL','sphere',[-1.05,0,1.36],[.105,.09,.11],[0,0,0],'hand.L'),
          ('ThighR','cylinder',[.16,0,.78],[.13,.13,.30],[0,0,0],'upper_leg.R'),
          ('ShinR','cylinder',[.16,0,.29],[.105,.105,.25],[0,0,0],'lower_leg.R'),
          ('FootR','cube',[.16,-.13,.065],[.13,.25,.065],[0,0,0],'foot.R'),
          ('ThighL','cylinder',[-.16,0,.78],[.13,.13,.30],[0,0,0],'upper_leg.L'),
          ('ShinL','cylinder',[-.16,0,.29],[.105,.105,.25],[0,0,0],'lower_leg.L'),
          ('FootL','cube',[-.16,-.13,.065],[.13,.25,.065],[0,0,0],'foot.L'),
        ]
        segment_names=[name+'__'+item[0] for item in segments]
        controls=['Hand.R_CTRL','Hand.L_CTRL','Elbow.R_POLE','Elbow.L_POLE','Foot.R_CTRL','Foot.L_CTRL','Knee.R_POLE','Knee.L_POLE']
        self._ensure_names_free([body_name,rig_name,spear_name,*segment_names,*[name+'_'+c for c in controls]])
        created=[]
        try:
            part_receipts=[]
            for suffix,primitive,location,part_scale,rotation,_bone in segments:
                part=self.dispatch('object.create_mesh',{'name':name+'__'+suffix,'primitive':primitive,
                    'location':[v*scale for v in location],'scale':[v*scale for v in part_scale],'rotation':rotation})['result']
                created.append(part['name']); part_receipts.append(part)
                self.dispatch('object.apply_transform',{'objectId':part['objectId'],'location':True,'rotation':True,'scale':True})
            body=self.dispatch('object.join',{'objects':[{'objectId':part['objectId']} for part in part_receipts],
                                              'newName':body_name})['result']; created.append(body_name)
            def p(values): return [v*scale for v in values]
            bones=[
             {'name':'root','head':p([0,0,0]),'tail':p([0,0,.25]),'deform':False},
             {'name':'pelvis','head':p([0,0,.9]),'tail':p([0,0,1.15]),'parent':'root'},
             {'name':'spine','head':p([0,0,1.15]),'tail':p([0,0,1.72]),'parent':'pelvis'},
             {'name':'head','head':p([0,0,1.72]),'tail':p([0,0,2.18]),'parent':'spine'},
             {'name':'upper_arm.R','head':p([.22,0,1.68]),'tail':p([.62,0,1.55]),'parent':'spine'},
             {'name':'lower_arm.R','head':p([.62,0,1.55]),'tail':p([.96,0,1.39]),'parent':'upper_arm.R','connected':True},
             {'name':'hand.R','head':p([.96,0,1.39]),'tail':p([1.15,0,1.34]),'parent':'lower_arm.R','connected':True},
             {'name':'upper_arm.L','head':p([-.22,0,1.68]),'tail':p([-.62,0,1.55]),'parent':'spine'},
             {'name':'lower_arm.L','head':p([-.62,0,1.55]),'tail':p([-.96,0,1.39]),'parent':'upper_arm.L','connected':True},
             {'name':'hand.L','head':p([-.96,0,1.39]),'tail':p([-1.15,0,1.34]),'parent':'lower_arm.L','connected':True},
             {'name':'upper_leg.R','head':p([.16,0,1.0]),'tail':p([.16,0,.56]),'parent':'pelvis'},
             {'name':'lower_leg.R','head':p([.16,0,.56]),'tail':p([.16,0,.12]),'parent':'upper_leg.R','connected':True},
             {'name':'foot.R','head':p([.16,0,.12]),'tail':p([.16,-.28,.08]),'parent':'lower_leg.R'},
             {'name':'upper_leg.L','head':p([-.16,0,1.0]),'tail':p([-.16,0,.56]),'parent':'pelvis'},
             {'name':'lower_leg.L','head':p([-.16,0,.56]),'tail':p([-.16,0,.12]),'parent':'upper_leg.L','connected':True},
             {'name':'foot.L','head':p([-.16,0,.12]),'tail':p([-.16,-.28,.08]),'parent':'lower_leg.L'},
            ]
            rig=self.dispatch('rig.create_armature',{'name':rig_name,'bones':bones})['result']; created.append(rig_name)
            self.dispatch('rig.bind',{'mesh':{'objectId':body['objectId']},'armature':{'objectId':rig['objectId']}})
            # Each disconnected proxy segment receives a bone group through spatial bounds.
            for suffix,_primitive,location,part_scale,rotation,bone in segments:
                extent=([part_scale[2],part_scale[1],part_scale[0]]
                        if abs(rotation[1])>1 else part_scale)
                lower=[(location[i]-extent[i]*1.15)*scale for i in range(3)]
                upper=[(location[i]+extent[i]*1.15)*scale for i in range(3)]
                selection=self.dispatch('mesh.select',{'objectId':body['objectId'],'method':'spatial','min':lower,'max':upper})['result']
                if selection['vertices']:
                    self.dispatch('rig.assign_weights',{'mesh':{'objectId':body['objectId']},'selection':selection,'bone':bone,'weight':1})
            control_data={
             'Hand.R_CTRL':([1.15,0,1.34],'CUBE'),'Hand.L_CTRL':([-1.15,0,1.34],'CUBE'),
             'Elbow.R_POLE':([.6,-.7,1.55],'SPHERE'),'Elbow.L_POLE':([-.6,-.7,1.55],'SPHERE'),
             'Foot.R_CTRL':([.16,-.28,.08],'CUBE'),'Foot.L_CTRL':([-.16,-.28,.08],'CUBE'),
             'Knee.R_POLE':([.16,-.65,.55],'SPHERE'),'Knee.L_POLE':([-.16,-.65,.55],'SPHERE')}
            control_receipts={}
            for suffix,(location,shape) in control_data.items():
                receipt=self.dispatch('rig.create_control',{'name':name+'_'+suffix,'location':p(location),'shape':shape,'size':.1*scale})['result']
                created.append(receipt['name']); control_receipts[suffix]=receipt
            for side in ('R','L'):
                self.dispatch('constraint.add_bone',{'armatureId':rig['objectId'],'bone':f'lower_arm.{side}',
                 'type':'IK','name':f'Arm IK.{side}','targetObjectId':control_receipts[f'Hand.{side}_CTRL']['objectId'],
                 'poleObjectId':control_receipts[f'Elbow.{side}_POLE']['objectId'],'chainLength':2})
                self.dispatch('constraint.add_bone',{'armatureId':rig['objectId'],'bone':f'lower_leg.{side}',
                 'type':'IK','name':f'Leg IK.{side}','targetObjectId':control_receipts[f'Foot.{side}_CTRL']['objectId'],
                 'poleObjectId':control_receipts[f'Knee.{side}_POLE']['objectId'],'chainLength':2})
                self.dispatch('constraint.add_bone',{'armatureId':rig['objectId'],'bone':f'lower_arm.{side}',
                 'type':'LIMIT_ROTATION','name':f'Elbow Limit.{side}','minRotation':[-2.8,-.2,-.2],'maxRotation':[.2,.2,.2]})
            spear=self.dispatch('recipe.spear',{'name':spear_name,'length':3.2*scale,'shaftRadius':.025*scale,
                'headLength':.32*scale,'headRadius':.09*scale})['result']['spear']; created.append(spear_name)
            hand=p([1.15,0,1.34]); rotation=[0,1.57079632679,0]
            self.dispatch('object.transform',{'objectId':spear['objectId'],'location':hand,'rotation':rotation})
            self.dispatch('constraint.add_object',{'owner':{'objectId':spear['objectId']},'target':{'objectId':rig['objectId']},
                'bone':'hand.R','type':'CHILD_OF','name':'Right Hand Grip','influence':1})
            self.dispatch('animation.set_frame_range',{'start':1,'end':max(catch+30,120)})
            for frame,influence in ((1,1),(release-1,1),(release,0),(catch,0),(catch+1,1)):
                self.dispatch('constraint.keyframe_influence',{'owner':{'objectId':spear['objectId']},
                    'constraintName':'Right Hand Grip','frame':frame,'influence':influence})
            poses=[(release,hand,rotation),(apex,p([1.55,0,2.05]),[0,2.4,0]),(catch,hand,rotation)]
            for frame,location,rot in poses:
                self.dispatch('object.transform',{'objectId':spear['objectId'],'location':location,'rotation':rot})
                self.dispatch('animation.insert_keyframe',{'object':spear_name,'dataPath':'location','frame':frame})
                self.dispatch('animation.insert_keyframe',{'object':spear_name,'dataPath':'rotation_euler','frame':frame})
            return {'changedObjects':created,'result':{'recipe':'rigged_spear_character','recipeVersion':self.VERSION,
                'body':body,'armature':rig,'controls':control_receipts,'spear':spear,
                'throwFrames':{'release':release,'apex':apex,'catch':catch},'height':height,
                'rig':self.dispatch('rig.inspect',{'objectId':rig['objectId']})['result']}}
        except Exception:
            for object_name in reversed(created):
                obj=self.bpy.data.objects.get(object_name)
                if obj is not None:self.bpy.data.objects.remove(obj,do_unlink=True)
            raise

    def procedural_courtyard(self,arguments):
        name=require_name(arguments.get('name'));dims=vector3(arguments.get('dimensions'),'dimensions');arches=arguments.get('archCount')
        if dims[0]<=0 or dims[1]<=0 or dims[2]<=0 or type(arches) is not int or arches<1:raise HarnessError('INVALID_ARGUMENT','dimensions/archCount are invalid')
        density=finite_number(arguments.get('rubbleDensity',2.0),'rubbleDensity',minimum=0)
        names={key:name+'_'+key for key in ('Ground','Arches','Steps','Slabs')};self._ensure_names_free(names.values())
        created=[]
        try:
            ground=self.dispatch('object.create_mesh',{'name':names['Ground'],'primitive':'plane','scale':[dims[0]/2,dims[1]/2,1]})['result'];created.append(ground['name'])
            self.dispatch('object.apply_transform',{'objectId':ground['objectId'],'scale':True})
            arch=self.dispatch('object.create_mesh',{'name':names['Arches'],'primitive':'torus','location':[-dims[0]*.3,dims[1]*.32,dims[2]*.06],
                'rotation':[1.57079632679,0,0],'scale':[dims[0]*.10,dims[2]*.45,dims[2]*.06]})['result'];created.append(arch['name'])
            self.dispatch('object.apply_transform',{'objectId':arch['objectId'],'rotation':True,'scale':True})
            self.dispatch('modifier.add',{'objectId':arch['objectId'],'modifier':'ARRAY','modifierName':'Arch Array',
                'settings':{'count':arches,'use_relative_offset':False,'use_constant_offset':True,
                            'constant_offset_displace':[dims[0]*.6/max(arches-1,1),0,0]}})
            steps=self.dispatch('object.create_mesh',{'name':names['Steps'],'primitive':'cube','location':[0,dims[1]*.34,dims[2]*.04],
                'scale':[dims[0]*.18,dims[1]*.08,dims[2]*.04]})['result'];created.append(steps['name'])
            self.dispatch('object.apply_transform',{'objectId':steps['objectId'],'scale':True})
            self.dispatch('modifier.add',{'objectId':steps['objectId'],'modifier':'ARRAY','modifierName':'Step Array',
                'settings':{'count':3,'relative_offset_displace':[0,-1.05,1.0]}})
            slabs=self.dispatch('object.create_mesh',{'name':names['Slabs'],'primitive':'cube','location':[-dims[0]*.35,0,dims[2]*.015],
                'scale':[dims[0]*.07,dims[1]*.08,dims[2]*.015]})['result'];created.append(slabs['name'])
            self.dispatch('object.apply_transform',{'objectId':slabs['objectId'],'scale':True})
            self.dispatch('modifier.add',{'objectId':slabs['objectId'],'modifier':'ARRAY','modifierName':'Slab Array',
                'settings':{'count':7,'relative_offset_displace':[1.15,0,0]}})
            group=name+'_RubbleNodes';modifier='Procedural Rubble'
            group_result=self.dispatch('geometry_nodes.create_group',{'object':{'objectId':ground['objectId']},'groupName':group,
                'modifierName':modifier,'inputs':[{'name':'Rubble Density','type':'FLOAT','default':density}]})['result']
            for node_type,node_name in [('GeometryNodeDistributePointsOnFaces','Distribute'),('GeometryNodeMeshIcoSphere','Rubble Mesh'),
                ('GeometryNodeInstanceOnPoints','Instance'),('GeometryNodeRealizeInstances','Realize'),('GeometryNodeJoinGeometry','Join')]:
                self.dispatch('geometry_nodes.add_node',{'groupName':group,'nodeType':node_type,'name':node_name})
            for source,socket,target,target_socket in [('Group Input','Geometry','Distribute','Mesh'),('Group Input','Rubble Density','Distribute','Density'),
                ('Distribute','Points','Instance','Points'),('Rubble Mesh','Mesh','Instance','Instance'),('Instance','Instances','Realize','Geometry'),
                ('Group Input','Geometry','Join','Geometry'),('Realize','Geometry','Join','Geometry'),('Join','Geometry','Group Output','Geometry')]:
                self.dispatch('geometry_nodes.connect',{'groupName':group,'fromNode':source,'fromSocket':socket,'toNode':target,'toSocket':target_socket})
            self.dispatch('geometry_nodes.set_node_input',{'groupName':group,'node':'Rubble Mesh','socket':'Radius','value':dims[2]*.025})
            self.dispatch('geometry_nodes.set_node_input',{'groupName':group,'node':'Rubble Mesh','socket':'Subdivisions','value':1})
            self.dispatch('geometry_nodes.set_modifier_input',{'object':{'objectId':ground['objectId']},'modifierName':modifier,'socket':'Rubble Density','value':density})
            ground_obj=self.bpy.data.objects[ground['name']];ground_obj['codex_courtyard_dimensions']=dims;ground_obj['codex_courtyard_arches']=arches
            return {'changedObjects':created,'result':{'recipe':'procedural_courtyard','recipeVersion':self.VERSION,'name':name,
                'objects':{'ground':ground,'arches':arch,'steps':steps,'slabs':slabs},'nodeGroup':group_result,'dimensions':dims,
                'archCount':arches,'rubbleDensity':density}}
        except Exception:
            for object_name in reversed(created):
                obj=self.bpy.data.objects.get(object_name)
                if obj is not None:self.bpy.data.objects.remove(obj,do_unlink=True)
            raise

    def update_procedural_courtyard(self,arguments):
        name=require_name(arguments.get('name'));ground=self.bpy.data.objects.get(name+'_Ground');arches=self.bpy.data.objects.get(name+'_Arches')
        if ground is None or arches is None:raise HarnessError('OBJECT_NOT_FOUND','courtyard recipe objects were not found')
        old=list(ground.get('codex_courtyard_dimensions',[]))
        if len(old)!=3:raise HarnessError('INVALID_ARGUMENT','courtyard recipe metadata is missing')
        dims=vector3(arguments.get('dimensions',old),'dimensions')
        if any(v<=0 for v in dims):raise HarnessError('INVALID_ARGUMENT','dimensions must be positive')
        count=arguments.get('archCount',int(ground.get('codex_courtyard_arches',1)))
        if type(count) is not int or count<1:raise HarnessError('INVALID_ARGUMENT','archCount must be positive')
        density=finite_number(arguments.get('rubbleDensity',2.0),'rubbleDensity',minimum=0)
        self.dispatch('object.transform',{'name':ground.name,'scale':[dims[0]/old[0],dims[1]/old[1],1]})
        self.dispatch('modifier.configure',{'name':arches.name,'modifierName':'Arch Array','settings':{'count':count,
            'constant_offset_displace':[dims[0]*.6/max(count-1,1),0,0]}})
        self.dispatch('geometry_nodes.set_modifier_input',{'object':{'name':ground.name},'modifierName':'Procedural Rubble','socket':'Rubble Density','value':density})
        ground['codex_courtyard_dimensions']=dims;ground['codex_courtyard_arches']=count
        return {'changedObjects':[ground.name,arches.name],'result':{'name':name,'dimensions':dims,'archCount':count,
            'rubbleDensity':density,'stableObjects':[name+'_'+key for key in ('Ground','Arches','Steps','Slabs')]}}
