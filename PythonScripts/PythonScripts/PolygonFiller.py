import shapefile
import bpy
import bmesh
import math
import re
import HeightMapUtils
from Common import *
from Constants import *

# sp_point == [lon, lat]
def get_heighest_lowest_indexes(sp_points):
    heighest_point_index = 0
    lowest_point_index = 0 
    for i in range(0, len(sp_points)):
        point = sp_point[i]
        if(point[1] < sp_points[heighest_point_index]):
            heighest_point_index = i
        if(point[1] > sp_points[lowest_point_index]):
            lowest_point_index = i
    return (heighest_point_index, lowest_point_index)

def get_intersection_lon(point0, point1, lat):
    if(point0[1] == point1[1] == lat):
        # I don't know what to do here
        return point0[0]

    # Sort points for increasing LAT
    if point0[1] > point1[1]:
        point0, point1 = point1, point0     

    if(point0[1] == lat):
        return point0[0]
    if(point1[1] == lat):
        return point1[0]

    lon0 = point0[0]
    lon1 = point1[0]
    lat0 = point0[1]
    lat1 = point1[1]

    if lat0 > lat or lat1 < lat:
        return None

    dLon = lon1 - lon0 
    dLat = lat1 - lat0 

    lon = dLon/dLat * (lat - lat0) + lon0

    return lon

def get_by_index(points_indexed, index):
    for point_indexed in points_indexed:
        if point_indexed[1] == index:
           return point_indexed
    return None

def get_intersected_edges(points_indexed, points, lat):
    result = []
    for i in range(0, len(points_indexed)):
        point_indexed0 = points_indexed[i]
        #print(f"point_indexed0: {point_indexed0}")
        point0 = point_indexed0[0]
        index0 = point_indexed0[1]

        index1 = index0 + 1
        if index0 == len(points_indexed) - 1:
            #print("Wrapping")
            index1 = 0

        #print(index0, "Looks for", index1, "Len:", len(points_indexed))
        #point_indexed1 = get_by_index(points_indexed, index1)
        #print(f"point_indexed1: {point_indexed1}")
        #point1 = point_indexed1[0]
        point1 = points[index1]

        intersection_lon = get_intersection_lon(point0, point1, lat)
        #print(f"get_intersection_lon(point0: {point0} point1: {point1} lat: {lat}): {intersection_lon}")
        if(intersection_lon is None):
            continue

        result.append((index0, index1, intersection_lon))

    # Sort by intersection_lon
    sorted_result = sorted(result, key=lambda edge: edge[2])
    return sorted_result

def create_grid(sp_points, lon_step, lat_step, ops):

    create_vertex = ops[0]
    create_edge = ops[1]
    create_face = ops[2]

    points_indexed = []
    points = []
    for i in range(0, len(sp_points)):
        point = deg2rad(sp_points[i])
        point_indexed = (point, i)
        points_indexed.append(point_indexed)
        points.append(point)

    # Sort by LAT
    points_indexed = sorted(points_indexed, key=lambda pi: pi[0][1])
    #print(points_indexed)
    lat_min = points_indexed[0][0][1]
    length = len(points_indexed)
    lat_max = points_indexed[length - 1][0][1]
    #print(f"lat_min: {lat_min}, lat_max: {lat_max}, lat_step: {lat_step}")
    lat = lat_min
    while lat < lat_max:
        #print("LOOP LAT", lat)
        intersected_edges = get_intersected_edges(points_indexed, points, lat)
        #print("lat:", lat, "len(intersected_edges):", len(intersected_edges))
        if len(intersected_edges) == 0:
            #print("lat:", lat, "len(intersected_edges) is 0, skipping this Lat")
            lat += lat_step
            continue

        if len(intersected_edges) % 2 != 0:
            #print("lat:", lat, "len(intersected_edges) % 2 is not 0, skipping this Lat?!")
            lat += lat_step
            continue
        
        for edge_index in range(0, len(intersected_edges), 2):            
            starting_edge = intersected_edges[edge_index]
            finishing_edge = intersected_edges[edge_index + 1]
            #print(f"starting_edge: {starting_edge}, finishing_edge: {finishing_edge}")
            lon0 = starting_edge[2]
            lon1 = finishing_edge[2]
            #print(f"lon0: {lon0}, lon1: {lon1}")
            lon = lon0
            while lon < lon1:
                create_vertex((lon, lat))
                lon += lon_step

        lat += lat_step

    
def generate_country_elevation(name, points, parts, collection, height_scale):  

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
        
        mesh_name = name + "ElevationMesh" + str(part_index)
        mesh = bpy.data.meshes.new(mesh_name)
        vertices = []
        edges = []
        faces = []

        def create_vertex(sp_rad):
            #print(f"create_vertex({sp_rad})")
            height = HeightMapUtils.get_height_from_spherical(sp_rad, height_scale)            
            #print(f"Height({sp_rad}, {height_scale}):", height)
            vertex = sp2cart_rad(sp_rad, MODEL_RADIUS + height)
            vertices.append(vertex)

        ops = [create_vertex, None, None]
        create_grid(part_vertexes, GRID_LON_STEP, GRID_LAT_STEP, ops)

        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        
        object_name = name + "Elevation" + str(part_index)
        object = bpy.data.objects.new(object_name, mesh)    
        collection.objects.link(object)    

        #break

def generate_countries_elevation(height_scale = 20, white_list = None):    
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
        generate_country_elevation(name_en, points, parts, collection, height_scale)
        