bl_info = {
    "name": "Animation Curve Exporter",
    "author": "Yiwen Dai",
    "version": (0,0,1),
    "blender": (3,6,0),
    "location": "3D Viewport > Sidebar > Animation Curve Utils",
    "description": "Simple tool to export and load animation curve",
    "category": "Development",
}

import os 
from datetime import datetime
import json 
import mathutils
from mathutils import Vector

import bpy 


from bpy_extras.io_utils import ImportHelper,ExportHelper
from bpy.props import StringProperty, BoolProperty


def get_project_dir():
    """
    Get the current blender file's direcotry
    """
    try: 
        if bpy.data.is_saved:
            blender_file = bpy.data.filepath
            return os.path.dirname(blender_file)
        else:
            return ''
    except:
        return ''

def validate_selection(context):
    """
    Util function to validate current selection 
    """

    #TODO: Only support single object selection for now
    if not context: 
        context = bpy.context 

    selections = context.selected_objects
    if len(selections) == 1: 
        return selections[0]
    elif not selections or len(selections) == 0:
        print('Please select the object you wish to export animation curve!')
    else:
        print('Multiple object detected; This is not currently supported!')

    return None


def create_animation_data(target, name):
    """
    Create animation data
    """
    if target.animation_data == None:
        target.animation_data_create()
        target.animation_data.action = bpy.data.actions.new(name=name)    
    
def create_fcurve(target, data_path, id, group_name = ''):
    """
    Create animation curve (fcurve)
    """
    fcurve = target.animation_data.action.fcurves.find(
        data_path=data_path, index=id)
    
    if fcurve == None:
        fcurve = target.animation_data.action.fcurves.new(
            data_path=data_path, index=id, action_group=group_name)
        
    return fcurve

def load_animation_data_from_file(file):
    """
    Load animation data form file 

    Parms: 
        file: str, json file contains animation

    Return: 
        loaded_data: dict
    """
    loaded_data = None or {}
    if not os.path.exists(file):
        print('Error: Invalid data')
    else:
        with open(file, 'r') as fp:
            json_str = fp.read()
            loaded_data = json.loads(json_str)

    return loaded_data


def apply_animation_to_obj(target, loaded_data):
    """
    Apply animation to selected object

    Parms: 
        target (bpy.context.object): object to apply animation to 
        loaded_data (dict): parsed animation data from json file

    Return: 
        success (bool): if the operation succeeded
    """
    anim_data = target.animation_data
    is_override = True
    if anim_data:
        # TODO: give user a pop up choice whether they wish to override 
        # the exising animation 
        # For now, simply remove the animation 
        print('Found animation data on obj {} \n'
              'Do you wish to override it? '.format(target.name))
        if is_override:
            print('Removing exisitng animation')
            target.animation_data_clear() 

    else:
        print('creating new animation')
        

    anim_data_name = loaded_data.get('name', None)
    if not anim_data_name:
        print('Error: no animation found,abort!')
        raise RuntimeError('Error: no animation found,abort!')
    
    create_animation_data(target,anim_data_name)  
    curves = loaded_data.get('curves', {})
    if not curves: 
        print('Error: no animation curve found,abort!')
        raise RuntimeError('Error: no animation curve found,abort!')
    
    # TODO: add better error handling for dict.get
    try:
        for curve_data in curves:
            data_path = curve_data.get('data_path', None)
            channel = curve_data.get('channel', None)
            group = curve_data.get('group', None)
            keys = curve_data.get('keys', {})
            
            fcv = create_fcurve(target, data_path, channel, group)
            for key_data in keys:
                cox = key_data.get('co.x')
                coy = key_data.get('co.y')
                key = fcv.keyframe_points.insert(frame=cox,value=coy)
                key.co_ui = Vector((
                    key_data.get('co_ui.x'),
                    key_data.get('co_ui.y')
                ))
                key.easing = key_data.get('easing')
                key.handle_left = Vector((
                    key_data.get('handle_left.x'),
                    key_data.get('handle_left.y')
                ))
                key.handle_left_type = key_data.get('handle_left_type')
                key.handle_right = Vector((
                    key_data.get('handle_right.x'),
                    key_data.get('handle_right.y')
                ))
                key.handle_right_type = key_data.get('handle_right_type')
                key.interpolation = key_data.get('interpolation')
                key.period = key_data.get('period')              
                key.type = key_data.get('type')
    except Exception as e:
        raise RuntimeError(e)

    return True

def add_metadata(comment=None, version=0):
    """
    Create metadata to export to animation_curve.json
    """

    if not comment:
        comment = "Auto generated comment on export"

    metadata = {
        "author" : os.getlogin(),
        "export scene" : bpy.data.filepath,
        "export date" : str(datetime.now()),
        "comment" : comment,
        "version" : version 
    }
    return metadata
    
def parse_curve_data(target, meta_data):
    """
    Get the animation curve on selection obj and convert to json

    Parms: 
        target (bpy.context.object) : selected object
        meta_data (dict) : metadate for exported animation

    Return: 
        action_data (dict) : data for the animation action
    """
    if not target: 
        print('Please select an object!')
        return None 

    
    anim_data = target.animation_data
    if not anim_data: 
        print('No animation found on {}'.format(target.name))
        raise RuntimeError('No animation found on {}'.format(target.name))
    

    action = anim_data.action
    action_name = action.name
    curves = None or []
    try:
        for fcu in action.fcurves:
            all_key_data = None or []
            # location, scale ... counts as separate animation curves 
            # keyframe on each point 
            print("\t Parsing" + fcu.data_path + 
                " channel " + str(fcu.array_index) + 
                " group " + str(fcu.group))
            
            for keyframe in fcu.keyframe_points:
                key_data = {
                    'amplitude': keyframe.amplitude,
                    'back': keyframe.back,
                    'co.x': keyframe.co.x,
                    'co.y': keyframe.co.y,
                    'co_ui.x': keyframe.co_ui.x,
                    'co_ui.y': keyframe.co_ui.y,
                    'easing': keyframe.easing,
                    'handle_left.x': keyframe.handle_left.x,
                    'handle_left.y': keyframe.handle_left.y,
                    'handle_left_type': keyframe.handle_left_type,
                    'handle_right.x':keyframe.handle_right.x,
                    'handle_right.y':keyframe.handle_right.x,
                    'handle_right_type': keyframe.handle_right_type,
                    'interpolation': keyframe.interpolation,
                    'period': keyframe.period,
                    'type': keyframe.type
                }
                # ignored attibutes : related to editor status 
                # select_control_point, select_control_point, select_right_handle
                all_key_data.append(key_data)

            curve_data = {
                "data_path": fcu.data_path,
                "channel": fcu.array_index,
                "group": fcu.group.name,
                "keys": all_key_data
            }
            curves.append(curve_data)
    except Exception as e: 
        print(e)
        raise RuntimeError(e)

    # export all action data     
    action_data = {
        "name": action_name,
        "metadata": meta_data,
        "curves":curves
    }
    
    return action_data


class AC_OT_export_animation_curve(bpy.types.Operator, ExportHelper):
    """
    Operator for exporting animation curve
    """
    bl_idname = "ac.export_anim_curve"
    bl_label = "Export Animation Curve"
    

    filename_ext : StringProperty(
        default = ".json"
    )  # type: ignore 

    directory: StringProperty(
        default=get_project_dir(), 
        options={'HIDDEN'}
    ) # type: ignore 

    target = None

    check_existing: BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},
    ) # type: ignore


    def execute(self, context):

        target = self.target
        export_file = self.filepath

        if export_file:
            if self.check_existing: 
                print('TODO: Do you wish to override or version up?')


            metadata = add_metadata(version = 0)
            action_data = parse_curve_data(target, metadata)

            if not action_data:
                self.report({'ERROR'}, 
                            'Error parsing animation data on selected object,' 
                            'check log for details')
                return {"FINISHED"}
            # export to json file
            with open(export_file, 'w') as fp:
                json.dump(
                    action_data, 
                    fp,
                    sort_keys=False,
                    indent=4,
                    separators=(',', ': ')
                )
            
            self.report({'INFO'}, 'Successfully exported to {}'.format(self.filepath))


        return {"FINISHED"}
    
    def invoke(self, context, event):
        
        self.target = validate_selection(context)
        if not self.target:
            self.report({'ERROR'}, 
                        'Invalide selection, please select one object with animation')
            return {"CANCELLED"}
        ExportHelper.invoke(self, context, event)

        return {"RUNNING_MODAL"}
    
class AC_OT_load_animation_curve(bpy.types.Operator, ImportHelper): 
    """
    Operator for importing animation curve
    """
    bl_idname = "ac.load_anim_curve" 
    bl_label = "Load Animation Curve"     
    bl_options = {"REGISTER", "UNDO"}


    filter_glob: StringProperty(
        default='*.json', 
        options={'HIDDEN'}
        ) # type: ignore


    directory: StringProperty(
        default=get_project_dir(), 
        options={'HIDDEN'}
        ) # type: ignore

    def execute(self, context): 
        """ Load the animation data""" 
        target = self.target
        
        bpy.ops.ed.undo_push(message = 'Load animation curve: {}'.format(self.filepath))
        try:
            loaded_data = load_animation_data_from_file(self.filepath)
            apply_animation_to_obj(target, loaded_data)
        except RuntimeError as e:
            self.report({'ERROR'}, 'Error loading animation data \n {}'.format(e))
            # undo the loaded keys if any error occurs with corrupt data
            print('undo loaded animation ...')
            bpy.ops.ed.undo()
        else:
            self.report({'INFO'}, 'Success!')

        return {'FINISHED'}     

    def invoke(self, context, event):
        self.target = validate_selection(context)
        if not self.target:
            self.report({'ERROR'}, 
                        'Invalide selection, please select one object!')
            return {"CANCELLED"}
        ImportHelper.invoke(self, context, event)

        return {"RUNNING_MODAL"}

    


 
class VIEW3D_PT_animation_curve_export_panel(bpy.types.Panel):
    # pass 
    # where to add the panel to UI
    
    # space type and regieon type 
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    bl_category = "Animation Curve Utils"
    bl_label = "Export/Load Animation Curve"
    
    
    def draw(self, context):
        """ Define the layout of the panel """
      
        # UI 'Export' 
        row = self.layout.row()
        row.operator("ac.export_anim_curve", text = "Export")
        
        # UI 'Load' 
        row = self.layout.row()
        row.operator("ac.load_anim_curve", text = "Load")



        
        
def register():
    print('registering all classes ... ')
    bpy.utils.register_class(VIEW3D_PT_animation_curve_export_panel)
    bpy.utils.register_class(AC_OT_export_animation_curve)
    bpy.utils.register_class(AC_OT_load_animation_curve)
    
    

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_animation_curve_export_panel)
    bpy.utils.unregister_class(AC_OT_export_animation_curve)
    bpy.utils.unregister_class(AC_OT_load_animation_curve)
    


def main():
    # init panel 
    register()

if __name__ == "__main__":
    main()