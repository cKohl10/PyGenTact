bl_info = {
    "name": "GenTact",
    "author": "Carson Kohlbrenner",
    "version": (2, 0),
    "blender": (4, 5, 0),
    "location": "Object > Skin Import/Export",
    "description": "GenTact Toolbox: A Computational Design Pipeline to Procedurally Generate Context-Driven 3D Printed Whole-Body Artificial Skins",
    "warning": "",
    "doc_url": "https://github.com/HIRO-group/GenTact",
    "category": "GenTact",
}

import bpy
import bpy.props

from .operators.isaac_save_operator import IsaacSaveOperator
from .operators.alligator_save_operator import AlligatorSaveOperator
from .operators.skin_vertice_save_operator import SkinVerticeSaveOperator
from .operators.import_heatmap_operator import ImportHeatmapOperator
from .operators.urdf_export_operator import URDFExportOperator

class MyAddonProperties(bpy.types.PropertyGroup):
    unit_scale: bpy.props.FloatProperty(
        name="Unit Scale",
        description="Scale of the units",
        default=1.0,
        min=0.001,
        max=1000000.0
    )

    group_name_import: bpy.props.StringProperty(
        name="",
        description="Name of the skin vertex group",
        default="Group"
    )

    group_name_export: bpy.props.StringProperty(
        name="",
        description="Name of the skin vertex group",
        default="Group"
    )

class SensorPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "GenTact Export"
    bl_idname = "OBJECT_PT_GENTACT_EXPORT"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        unit_prop = scene.my_addon_properties
        obj = context.object

        row = layout.row()
        row.label(text="Save sensors as CSV", icon='FILE_TICK')

        # row = layout.row()
        # row.label(text="Select root prim for faster processing")

        row = layout.row()
        row.label(text="Selected root prim: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")

        # String field for identifying the skin vertex group
        row = layout.row()
        row.label(text="Sensor Vertex Group")
        row.prop(unit_prop, "group_name_export")

        # Isaac Save Button 
        # row = layout.row()
        # row.operator("object.isaac_save_operator")

        # Skin Vertice Save Button
        row = layout.row()
        row.operator("object.skin_vertice_save_operator")

        row = layout.row()
        row.label(text="Export Meshes as STLs", icon='EXPORT')

        # Unit Scale Slider
        row = layout.row()
        row.label(text="Unit Scale")
        row.prop(unit_prop, "unit_scale")

        # Spacer before URDF export
        layout.separator()
        layout.separator()

        # URDF Export Button 
        row = layout.row()
        row.operator("object.urdf_export_operator")

class ImportPanel(bpy.types.Panel):
    bl_label = "GenTact Import"
    bl_idname = "OBJECT_PT_GENTACT_IMPORT"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        unit_prop = scene.my_addon_properties

        # Panel Icon
        row = layout.row()
        row.label(text="Apply Heatmaps to Objects", icon='IMPORT')

        # String field for identifying the node placement vertex group
        row = layout.row()
        row.label(text="Sensor Vertex Group")
        row.prop(unit_prop, "group_name_import")

        # Apply Heatmap Button
        row = layout.row()
        row.operator("object.import_heatmap_operator", text="Import Heatmap")


def register():
    bpy.utils.register_class(MyAddonProperties)
    bpy.types.Scene.my_addon_properties = bpy.props.PointerProperty(type=MyAddonProperties)
    bpy.utils.register_class(IsaacSaveOperator)
    bpy.utils.register_class(AlligatorSaveOperator)
    bpy.utils.register_class(SkinVerticeSaveOperator)
    bpy.utils.register_class(URDFExportOperator)
    bpy.utils.register_class(ImportHeatmapOperator)
    bpy.utils.register_class(SensorPanel)
    bpy.utils.register_class(ImportPanel)

def unregister():
    bpy.utils.unregister_class(IsaacSaveOperator)
    bpy.utils.unregister_class(AlligatorSaveOperator)
    bpy.utils.unregister_class(SkinVerticeSaveOperator)
    bpy.utils.unregister_class(ImportHeatmapOperator)
    bpy.utils.unregister_class(URDFExportOperator)
    bpy.utils.unregister_class(MyAddonProperties)
    del bpy.types.Scene.my_addon_properties
    bpy.utils.unregister_class(SensorPanel)
    bpy.utils.unregister_class(ImportPanel)
    

if __name__ == "__main__":
    register()
