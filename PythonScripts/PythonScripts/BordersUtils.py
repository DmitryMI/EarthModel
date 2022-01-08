# Convert SHP countries borders to Meshes

import shapefile
import bpy
import bmesh
import math
import re
RADIUS = 1000

def sp2cart(sphere_point, radius):  
    lon = sphere_point[0]
    lat = sphere_point[1]
    lon_rad = math.radians(lon)
    lat_rad = math.radians(lat)
    x = radius * math.cos(lat_rad) * math.cos(lon_rad)
    y = radius * math.cos(lat_rad) * math.sin(lon_rad)
    z = radius * math.sin(lat_rad)
    #print("From " + str(sphere_point) + " to " + str((x, y, z)))
    return (x, y, z)
    
def create_polygon(points, mesh_name):
    mesh = bpy.data.meshes.new(mesh_name)
    vertices = []
    for p in points:
        vertex = sp2cart(p, RADIUS)
        vertices.append(vertex)
    
    edges = []
    for i in range(1, len(points)):
        edge = (i - 1, i)
        edges.append(edge)
    
    faces = []
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    return mesh

def create_country_borders(name, points, parts):     
    try:
        collection = bpy.data.collections["Borders"]
    except:   
        collection = bpy.data.collections.new('Borders')
        bpy.context.scene.collection.children.link(collection)    
    

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
        
        mesh_name = name + "BordersMesh" + str(part_index)
        mesh = create_polygon(part_vertexes, mesh_name)        
        object_name = name + "Borders" + str(part_index)
        object = bpy.data.objects.new(object_name, mesh)    
        collection.objects.link(object)    

def generate_countries():
    shape = shapefile.Reader("C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\ne_10m_admin_0_countries\\ne_10m_admin_0_countries.shp")

    records = shape.shapeRecords();
    print("Total number of records: ", len(records));

    for feature in shape.shapeRecords():
        name_en = feature.record['NAME_EN'];
        name_en = re.sub('[^A-Za-z0-9]+', '', name_en)
        #if(not name_en.startswith("Japan")):
            #print("Skipping " + name_en)
            #continue;
        shape = feature.shape;
        parts = shape.parts;
        print(parts)
        points = shape.points;
        print(name_en + ": " + str(len(points)) + " points, ", len(parts), " parts");
        
        create_country_borders(name_en, points, parts)
        
