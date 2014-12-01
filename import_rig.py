# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Author: Adhi Hargo (cadmus.sw@gmail.com)

import bpy
import os
from bpy.types import Operator, Macro
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty,\
    FloatProperty, IntProperty, StringProperty, PointerProperty

bl_info = {
    "name": "Import Rig",
    "author": "Adhi Hargo",
    "version": (1, 0, 0),
    "blender": (2, 68, 0),
    "location": "Scene > Import Rig",
    "description": "Import a group, create rig proxy and append rig script.",
    "warning": "",
    "wiki_url": "https://github.com/adhihargo/import_rig",
    "tracker_url": "https://github.com/adhihargo/import_rig/issues",
    "category": "Object"}

def get_object_group(obj):
    group = None
    if not obj:
        pass
    elif obj.type == 'EMPTY' and obj.dupli_group:
        group = obj.dupli_group
    elif obj.data.library:
        for g in filter(lambda o: type(o) == bpy.types.Group,
                        obj.data.library.users_id):
            for o in g.objects:
                if o.data == obj.data:
                    group = g
                    break

    return group

class ADH_ImportRig(Macro):
    """Import a group, create rig proxy and append rig script."""
    bl_idname = 'object.adh_import_rig'
    bl_label = 'Import Rig (Complete)'
    bl_options = {'MACRO', 'REGISTER', 'UNDO'}

class ADH_LinkAppend(Operator):
    """Link/append data from another file."""
    bl_idname = 'wm.adh_link_append'
    bl_label = 'Import Rig'
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        obj = context.active_object

        if obj:
            if obj.type == 'EMPTY' and obj.dupli_group != None:
                return {'FINISHED'}
            else:
                return {'CANCELLED'}            

        return {'PASS_THROUGH'}

    def execute(self, context):
        context.scene.objects.active = None
        if bpy.app.version[0] == 2 and bpy.app.version[1] < 72:
            bpy.ops.wm.link_append('INVOKE_DEFAULT')
        else:
            bpy.ops.wm.link('INVOKE_DEFAULT')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class ADH_CreateRigProxy(Operator):
    "If active object is a group containing a rig, proxy the rig."
    bl_idname = 'object.adh_create_rig_proxy'
    bl_label = 'Create Rig Proxy'
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.dupli_group):
            return {'CANCELLED'}

        group = obj.dupli_group
        for o in group.objects:
            if o.type == 'ARMATURE':
                bpy.ops.object.proxy_make(object = o.name)
                context.active_object.name = group.name + "_rig"
                bpy.ops.object.posemode_toggle()
                break

        return {'FINISHED'}

class ADH_AppendRigScript(Operator):
    "Given active object's group, append every script from the group's file."
    bl_idname = 'object.adh_append_rig_script'
    bl_label = 'Append Rig Script'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'CANCELLED'}

        group = get_object_group(obj)
        if not group:
            return {'CANCELLED'}

        group_libpath = group.library.filepath
        script_list = None
        with bpy.data.libraries.load(group_libpath, link=True, relative=True)\
                as (data_from, data_to):
            script_list = [t for t in data_from.texts if
                           t.startswith('rig') and t.endswith('.py')]
            data_to.texts.extend(script_list)
        if not script_list:
            return {'FINISHED'}

        prev_type = context.area.type
        context.area.type = 'TEXT_EDITOR'
        prev_text = context.space_data.text
        for script in script_list:
            context.space_data.text = bpy.data.texts[script]
            try:
                bpy.ops.text.run_script()
            except:
                self.report({'WARNING'}, 'Unable to run script "%s".' % script)
        context.space_data.text = prev_text
        context.area.type = prev_type
        
        return {'FINISHED'}

class ADH_ReloadRig(Operator):
    "Reload selected armature."
    bl_idname = 'object.adh_reload_rig'
    bl_label = 'Reload Rig'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE' and obj.data.library != None

    def execute(self, context):
        rig_obj = context.active_object

        group = None
        for g in rig_obj.data.library.users_id:
            if type(g) != bpy.types.Group:
                continue
            for o in g.objects:
                if o.data == rig_obj.data:
                    group = g
                    break
        if group == None:
            self.report({'ERROR'}, "Rig's group not found.")
            return {'CANCELLED'}

        group_obj = None
        for o in context.scene.objects:
            if o.type == 'EMPTY' and o.dupli_group == group:
                group_obj = o
                break
        if group_obj == None:
            self.report({'ERROR'}, "Group's instance not found.")
            return {'CANCELLED'}

        rig_obj.name += "_old.000"
        bpy.ops.object.mode_set(mode='OBJECT')
        context.scene.objects.unlink(rig_obj)
        context.scene.objects.active = group_obj
        for o in group.objects:
            if o.type == 'ARMATURE':
                bpy.ops.object.proxy_make(object = o.name)
                context.active_object.name = group.name + "_rig"
                bpy.ops.object.posemode_toggle()
                break
            
        context.scene.update()
        return {'FINISHED'}

class ADH_AppendGroupObject(Operator):
    "If active object has a dupli group or belongs to a group, append object from that group."
    bl_idname = 'group.adh_append_object'
    bl_label = 'Append Group Object'
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        obj = context.active_object
        if not obj: return {'CANCELLED'}
        group = get_object_group(obj)
        if not group: return {'CANCELLED'}
        obj_base = context.active_base

        new_obj = group.objects[obj.adh_selected_object_index]
        context.scene.objects.link(new_obj)
        context.scene.update()

        prev_mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
            
        obj.select = False; new_obj.select = True
        bpy.ops.object.make_local('INVOKE_DEFAULT', type='SELECT_OBJECT')
        obj.select = True; new_obj.select = False
            
        context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode=prev_mode)

        return {'FINISHED'}

class SCENE_PT_adh_scene_panel(bpy.types.Panel):
    bl_label = 'Import Rig'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        row = column.row()
        row.operator("object.adh_import_rig")
        row = column.row(align=True)
        row.operator("object.adh_create_rig_proxy")
        row.operator("object.adh_append_rig_script")

        obj = context.active_object
        if not obj:
            return
        group = get_object_group(obj)
        if not group:
            return

        row = layout.row()
        column = row.column()
        column.template_list("SCENE_UL_adh_selected_group_objects", "",
                             group, "objects",
                             obj, "adh_selected_object_index", rows = 10)
        column = row.column()
        column.operator("group.adh_append_object", text = "", icon = "ZOOM_IN")

class SCENE_UL_adh_selected_group_objects(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname):
        obj = item
        if self.layout_type in ['DEFAULT', 'COMPACT']:
            row = layout.row(align = True)
            row.label(text = obj.name, translate = False,
                      icon_value = layout.icon(obj.data))
            prop_dict = dict(emboss=False, icon_only=True, text='', event=True,
                             expand=True)
            row.prop(obj, 'hide', **prop_dict)
            row.prop(obj, 'hide_render', **prop_dict)
        elif self.layout_type in ['GRID']:
            layout.alignment = 'CENTER'
            layout.label(text = "", icon_value = icon)

def menu_func_import(self, context):
    self.layout.operator("object.adh_import_rig")

def register():
    bpy.utils.register_module(__name__)
    ADH_ImportRig.define("WM_OT_adh_link_append")
    ADH_ImportRig.define("OBJECT_OT_adh_append_rig_script")    
    ADH_ImportRig.define("OBJECT_OT_adh_create_rig_proxy")
    bpy.types.INFO_MT_file_import.append(menu_func_import)

    # Ideally, this is (1) put in Group, (2) as custom property, but
    # (1) can't be done without being clunky to user, and (2) plain
    # impossible.
    bpy.types.Object.adh_selected_object_index = IntProperty(
        description = "For empty object with dupli group, the index to"\
            " selected object within the group.",
        options = {'SKIP_SAVE'})

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

    del bpy.types.Object.adh_selected_object_index
    
