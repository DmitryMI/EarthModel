# Convert SHP countries borders to Meshes
import shapefile
import bpy
import bmesh
import math
import re
from Common import *
import HeightMapUtils
from Constants import *

def create_tube(name, verts, edges, bevel_depth=0.1, resolution=1):
    curves = bpy.data.curves
    objects = bpy.data.objects
    scene = bpy.context.scene

    curve_name = name + 'TubeCurve'

    # if exists, pick up else generate a new one
    cu = curves.get(curve_name, curves.new(name=curve_name, type='CURVE'))
    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = bevel_depth
    cu.bevel_resolution = resolution
    cu_obj = objects.get(curve_name, objects.new(curve_name, cu))

    if cu.splines:
       cu.splines.clear()

    segment = cu.splines.new('POLY')
    
    # Treat the first point separately
    segment.points[0].co = verts[0] + (0,)
    
    for i in range(1, len(verts)):
        v1 = verts[i] + (0,)
        segment.points.add(1)
        segment.points[len(segment.points) - 1].co = v1   
        
    if not curve_name in scene.objects:
        try:
            collection = bpy.data.collections["Borders"]
        except:   
            collection = bpy.data.collections.new("Borders")
            bpy.context.scene.collection.children.link(collection)  
        collection.objects.link(cu_obj) 
        
def create_planes(name, verts, edges, collection, width):
    mesh_name = name + "PlaneMesh"
    curves = bpy.data.curves
    objects = bpy.data.objects
    scene = bpy.context.scene

    curve_name = name + 'PlaneCurve'

    # if exists, pick up else generate a new one
    cu = curves.get(curve_name, curves.new(name=curve_name, type='CURVE'))
    cu.dimensions = '3D'
    cu.fill_mode = 'FULL'
    cu.bevel_depth = 0
    cu.bevel_resolution = 1
    cu_obj = objects.get(curve_name, objects.new(curve_name, cu))

    if cu.splines:
       cu.splines.clear()

    segment = cu.splines.new('POLY')
    
    # Treat the first point separately
    segment.points[0].co = verts[0] + (0,)
    
    for i in range(1, len(verts)):
        v1 = verts[i] + (0,)
        segment.points.add(1)
        segment.points[len(segment.points) - 1].co = v1   
        
    if not curve_name in scene.objects:
        try:
            collection = bpy.data.collections["Borders"]
        except:   
            collection = bpy.data.collections.new("Borders")
            bpy.context.scene.collection.children.link(collection)  
        collection.objects.link(cu_obj) 
        
    height = BORDER_PLANE_LENGTH
    # Create plane segment 
    vertices = [(0, 0, 0), (0, width, 0), (height, width, 0), (height, 0, 0)]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    faces = [(0, 1, 2, 3)]
    plane_segment = bpy.data.meshes.new(mesh_name)
    plane_segment.from_pydata(vertices, edges, faces)
    plane_segment.update()
    plane_segment_object = bpy.data.objects.new(mesh_name + "Object", plane_segment)
    collection.objects.link(plane_segment_object)
    
    #bpy.context.scene.objects.active = plane_segment_object
    segment_length = segment.calc_length()
    
    """
    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["ARRAY"].count = int(segment_length // height)
    
    bpy.ops.object.modifier_add(type='CURVE')
    bpy.context.object.modifiers["CURVE"].curve_object = cu_obj
    """
    
    mod_array = plane_segment_object.modifiers.new(name='array', type='ARRAY')
    mod_array.count = int(segment_length / height)
    
    mod_curve = plane_segment_object.modifiers.new(name='curve', type='CURVE')
    #print(dir(mod_curve))
    mod_curve.object = cu_obj
    
    return
        
def create_polygon(points, name, collection, height_scale):
    mesh_name = name + "BordersEdgePolygon"
    mesh = bpy.data.meshes.new(mesh_name)
    vertices = []
    for p in points:
        sp_rad = deg2rad(p)
        height = HeightMapUtils.get_height_from_spherical(sp_rad, height_scale)
        vertex = sp2cart_rad(sp_rad, MODEL_RADIUS + height)
        vertices.append(vertex)
    
    edges = []
    for i in range(1, len(points)):
        edge = (i - 1, i)
        edges.append(edge)
        
    #create_tube(mesh_name, vertices, edges)
    create_planes(name, vertices, edges, collection, BORDER_PLANE_WIDTH)
    
    faces = []
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    return mesh

def create_country_borders(name, points, parts, collection, height_scale):  

    for part_index in range(0, len(parts)):
        part_vertexes = []
        #print("Part index: ", part_index)
        part_first_vertex = parts[part_index]
        #print("Part's first vertex: ", part_first_vertex)
        part_last_vertex = len(points) - 1
        if(part_index < len(parts) - 1):
            part_last_vertex = parts[part_index + 1] - 1
        #print("Part's last vertex: ", part_last_vertex)
        for i in range(part_first_vertex, part_last_vertex):
            part_vertexes.append(points[i])  
            
        #print("Part size: ", len(part_vertexes))
        
        mesh_name = name + str(part_index)
        mesh = create_polygon(part_vertexes, mesh_name, collection, height_scale)        
        object_name = name + "Borders" + str(part_index)
        object = bpy.data.objects.new(object_name, mesh)    
        collection.objects.link(object)    
        
def clear_countries():
    try:
        collection = bpy.data.collections["Borders"]
        for obj in collection.objects:
            bpy.data.objects.remove(obj)
    except:   
        print("Nothing to clear")        
        
        
def generate_countries(height_scale = 20, white_list = None):    
    shape = shapefile.Reader("C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\ne_10m_admin_0_countries\\ne_10m_admin_0_countries.shp")

    records = shape.shapeRecords();
    print("Total number of records: ", len(records));
    
    try:
        collection = bpy.data.collections["Borders"]
    except:   
        collection = bpy.data.collections.new('Borders')
        bpy.context.scene.collection.children.link(collection) 

    for feature in shape.shapeRecords():
        name_en = feature.record['NAME_EN'];
        name_en = re.sub('[^A-Za-z0-9]+', '', name_en)
        if not white_list is None:
            if not name_en in white_list:
                continue
        shape = feature.shape;
        parts = shape.parts;
        #print(parts)
        points = shape.points;
        print(name_en + ": " + str(len(points)) + " points, ", len(parts), " parts");
        
        create_country_borders(name_en, points, parts, collection, height_scale)
        
