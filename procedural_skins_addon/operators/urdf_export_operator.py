# Description: This script is used to export the selected skin unit to a URDF xacro file.

# Author: Carson Kohlbrenner
# Date: 10/30/2025

import bpy
import csv
import re
import bpy.props
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty
from bpy.types import Operator
from mathutils import Vector

############################################################

class URDFExportOperator(Operator, ExportHelper):
    """Exports the selected skin unit to a URDF xacro file"""
    bl_idname = "object.urdf_export_operator"
    bl_label = "Export URDF"

    filename_ext = ".xacro"
    filter_glob: StringProperty(
        default="*.xacro",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    def execute(self, context):
        print("URDFExportOperator.execute called\n")
        self.skin_group_name = context.scene.my_addon_properties.group_name_export
        if self.filepath:  # Check if filepath has been set
            self.export_urdf(context, self.filepath)
        else:
            self.report({'WARNING'}, "No file selected")  # Report a warning if no file was selected
            return {'CANCELLED'}
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)  # Open file explorer
        return {'RUNNING_MODAL'}
    
############################################################
##################### Helper Functions #####################
############################################################

    class VertexData:
        def __init__(self, index, pos, rpy, normal, obj_name):
            self.index = index
            self.obj_name = obj_name
            self.pos = pos
            self.rpy = rpy
            self.normal = normal

        def __str__(self):
            return f"Index: {self.index}, Obj Name: {self.obj_name}, Pos: {self.pos}, RPY: {self.rpy}, Normal: {self.normal}"

        def __repr__(self):
            return str(self)

    def export_urdf(self, context, file_path):
        # Get the object
        obj = context.object

        # Expand the ~ symbol into the path of the home directory
        #file_path = os.path.expanduser(file_path)

        if obj is None:
            print("No active object selected.")
            return

        # Collect all vertices on the object (and its children) flagged as sensors
        vertice_data = self.collect_sensor_vertices(obj)

        # Check if there are any sensor positions
        if len(vertice_data) == 0:
            print("No vertex positions found.")
            return

        # Save the attribute data to CSV
        # with open(file_path, 'w', newline='') as csvfile:
        #     csv_writer = csv.writer(csvfile)
        #     csv_writer.writerow(['Index', 'X', 'Y', 'Z', 'Object Name'])
            
        #     for i, element in enumerate(vertice_data):
        #         pos = element.pos
        #         csv_writer.writerow([element.index, pos.x, pos.y, pos.z, element.obj_name])

        # Save to a xacro file
        header = """
<?xml version="1.0"?>

<robot xmlns:xacro="http://ros.org/wiki/xacro">

<!-- Macro definition for skin unit -->
<xacro:macro name="REPLACE_ME_skin" params="parent namespace">
    <!-- Properties -->
    <xacro:property name="use_mesh_file" value="true" />
    <xacro:property name="mesh_file" value="REPLACE_ME" />
    <xacro:property name="mass" value="0.0" /> <!-- [kg] -->
    <xacro:property name="body_width" value="0.0" /> <!-- [m] -->
    <xacro:property name="body_height" value="0.0" /> <!-- [m] -->
    <xacro:property name="sensor_length" value="0.0" /> <!-- [m] -->
    <xacro:property name="sensor_radius" value="0.0" /> <!-- [m] -->

    <!-- Included URDF Files (NEEDED FOR BASE SKIN UNIT) -->
    <xacro:include filename="$(find gentact_descriptions)/robots/common/skin_unit_base.xacro" />

    <!-- Instantiate dermis once -->
    <xacro:dermis_base_macro
    robot_namespace="${namespace}"
    parent="${parent}"
    mass="${mass}"
    body_width="${body_width}"
    body_height="${body_height}"
    use_mesh_file="${use_mesh_file}"
    mesh_file="${mesh_file}">
    <origin xyz="0 0 0" rpy="0 0 0" />
    </xacro:dermis_base_macro>

        """
        body = self.sensor_xacro_template(vertice_data)
        footer = """
    </xacro:macro>

</robot>
        """
        with open(file_path, 'w') as file:
            file.write(header + body + footer)

        
        # print(f"\nAttribute {attribute_name} saved to {file_path}")
        print(f"Vertice count: {len(vertice_data)}")

    def sensor_xacro_template(self, vertice_data):
        instance_strings = []
        for i, vertex in enumerate(vertice_data):
            instance_string = f"""
    <xacro:self_cap_sensor
        robot_namespace="${{namespace}}"
        parent="${{namespace}}_skin"
        sensor_number="{i}"
        sensor_radius="${{sensor_radius}}"
        sensor_length="0.0"
        normal_x="{vertex.normal.x}"
        normal_y="{vertex.normal.y}"
        normal_z="{vertex.normal.z}">
        <origin xyz="{vertex.pos.x} {vertex.pos.y} {vertex.pos.z}" rpy="{vertex.rpy.x} {vertex.rpy.y} {vertex.rpy.z}" />
    </xacro:self_cap_sensor>
            """
            instance_strings.append(instance_string)
        return "\n".join(instance_strings)
        
    def collect_sensor_vertices(self, obj):
        sensor_vertices = []

        sensor_vertices.extend(self.extract_sensor_vertices(obj))

        for child in obj.children:
            sensor_vertices.extend(self.collect_sensor_vertices(child))

        return sensor_vertices

    def extract_sensor_vertices(self, obj):
        sensor_vertices = []

        if obj is None:
            return sensor_vertices

        if obj.type != 'MESH':
            return sensor_vertices

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

        try:
            attributes = mesh.attributes

            if "is_sensor" not in attributes:
                print(f"Object {obj.name} has no 'is_sensor' attribute.")
                return sensor_vertices

            sensor_attribute = attributes["is_sensor"]

            if sensor_attribute.domain != 'POINT':
                print(f"'is_sensor' attribute on {obj.name} is on {sensor_attribute.domain} domain; expected POINT.")
                return sensor_vertices

            sensor_attribute_data = sensor_attribute.data
            vertex_count = len(mesh.vertices)

            if len(sensor_attribute_data) != vertex_count:
                print(f"'is_sensor' attribute length mismatch on {obj.name}. Expected {vertex_count}, got {len(sensor_attribute_data)}.")
                return sensor_vertices

            attribute_names = {
                "sensor_pos": None,
                "sensor_rpy": None,
                "sensor_normal": None,
            }

            for attr_name in attribute_names.keys():
                attribute = attributes.get(attr_name)
                if attribute is None:
                    print(f"Object {obj.name} is missing required attribute '{attr_name}'.")
                    return sensor_vertices
                if attribute.domain != 'POINT':
                    print(f"Attribute '{attr_name}' on {obj.name} is on {attribute.domain} domain; expected POINT.")
                    return sensor_vertices
                if len(attribute.data) != vertex_count:
                    print(f"Attribute '{attr_name}' length mismatch on {obj.name}. Expected {vertex_count}, got {len(attribute.data)}.")
                    return sensor_vertices
                attribute_names[attr_name] = attribute

            for index, sensor_value in enumerate(sensor_attribute_data):
                value = getattr(sensor_value, "value", None)

                if value is None:
                    value = getattr(sensor_value, "boolean", None)

                if not value:
                    continue

                pos = self._get_vector_attribute_value(attribute_names["sensor_pos"], index)
                rpy = self._get_vector_attribute_value(attribute_names["sensor_rpy"], index)
                normal = self._get_vector_attribute_value(attribute_names["sensor_normal"], index)

                if pos is None or rpy is None or normal is None:
                    print(f"Skipping vertex {index} on {obj.name}: unable to read required attribute values.")
                    continue

                sensor_vertices.append(self.VertexData(index, pos, rpy, normal, obj.name))

            print(f"Found {len(sensor_vertices)} sensor vertices on object {obj.name}.")

        finally:
            eval_obj.to_mesh_clear()

        return sensor_vertices

    def _get_vector_attribute_value(self, attribute, index):
        element = attribute.data[index]

        if hasattr(element, "vector"):
            return element.vector.copy()

        if hasattr(element, "color"):
            color = element.color
            return Vector((color[0], color[1], color[2]))

        if hasattr(element, "value"):
            value = element.value
            try:
                # Attempt to coerce iterable values to Vector
                return Vector(value)
            except TypeError:
                return Vector((value, value, value))

        return None

