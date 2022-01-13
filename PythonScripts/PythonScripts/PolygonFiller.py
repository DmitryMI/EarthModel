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
    
def create_vertex(sp_rad, vertices):
    #print(f"create_vertex({sp_rad})")
    height = HeightMapUtils.get_height_from_spherical(sp_rad, HEIGHT_SCALE)            
    #print(f"Height({sp_rad}, {height_scale}):", height)
    vertex = sp2cart_rad(sp_rad, MODEL_RADIUS + height)
    vertices.append(vertex)
    


def normalize_angle_positive(angle):
    """
    Wrap the angle between 0 and 2 * pi.

    Args:
        angle (float): angle to wrap.

    Returns:
         The wrapped angle.

    """
    pi_2 = 2. * math.pi

    return fmod(fmod(angle, pi_2) + pi_2, pi_2) 



def normalize_angle(angle):
    """
    Wrap the angle between -pi and pi.

    Args:
        angle (float): angle to wrap.

    Returns:
         The wrapped angle.

    """
    a = normalize_angle_positive(angle)
    if a > np.pi:
        a -= 2. * math.pi

    return a 

def angle_diff(x, y):
    return math.atan2(math.sin(x-y), math.cos(x-y))

def create_grid(sp_points):
    vertices = []
    edges = []
    faces = []

    points_indexed = []
    points = []    
    
    first_point = deg2rad(sp_points[0])
    lon_base = first_point[0]
    lon_min = 0
    lon_max = 0
    for i in range(0, len(sp_points)):
        point = deg2rad(sp_points[i])
        point_translated = (angle_diff(point[0], lon_base), point[1])
        if point_translated[0] > lon_max:
            lon_max = point_translated[0]
        if point_translated[0] < lon_min:
            lon_min = point_translated[0]
        point_indexed = (point_translated, i)
        points_indexed.append(point_indexed)
        points.append(point_translated)
        
    lon_size = lon_max - lon_min
    row_segments_num = int(lon_size / GRID_LON_STEP) + 2
    #print(f"lon_min: {lon_min}, lon_max: {lon_max}, lon_size: {lon_size}, lon_segments: {row_segments_num}") 
    
    row_segments = [None] * row_segments_num
    
    # Sort by LAT
    points_indexed = sorted(points_indexed, key=lambda pi: pi[0][1])
    lat_min = points_indexed[0][0][1]
    length = len(points_indexed)
    lat_max = points_indexed[length - 1][0][1]
    lat = lat_min
    
    while lat < lat_max:
        intersected_edges = get_intersected_edges(points_indexed, points, lat)

        if len(intersected_edges) == 0:
            lat += GRID_LAT_STEP
            continue

        if len(intersected_edges) % 2 != 0:
            lat += GRID_LAT_STEP
            continue
            
        next_row_segments = [None] * row_segments_num
                
        for edge_index in range(0, len(intersected_edges), 2):
            starting_edge = intersected_edges[edge_index]
            finishing_edge = intersected_edges[edge_index + 1]
            lon0 = starting_edge[2]
            lon1 = finishing_edge[2]
            row_start_index = int((lon0 - lon_min) / GRID_LON_STEP)
            row_end_index = int((lon1 - lon_min) / GRID_LON_STEP)
            
            #while lon < lon1:
            prev_vertex = None
            for row_index in range(row_start_index, row_end_index + 1):
                lon_snapped = row_index * GRID_LON_STEP + lon_min
                if lon_snapped < lon0:
                    lon_snapped = lon0
                elif lon_snapped > lon1:
                    lon_snapped = lon1
                
                #print(f"len(row_segments): {len(row_segments)}, row_index: {row_index}")
                next_row_segments[row_index] = len(vertices)
                    
                create_vertex((lon_snapped + lon_base, lat), vertices)
                if prev_vertex is not None:                    
                    edge = (len(vertices) - 1, prev_vertex)
                    edges.append(edge)
                if row_segments[row_index] is not None:
                    edge = (len(vertices) - 1, row_segments[row_index])
                    edges.append(edge)
                    
                prev_vertex = len(vertices) - 1
            
            if prev_vertex is not None:
                create_vertex((lon1 + lon_base, lat), vertices) 
                edge = (len(vertices) - 1, prev_vertex)
                edges.append(edge)
                next_row_segments[row_end_index + 1] = len(vertices) - 1
                if row_segments[row_end_index + 1] is not None:
                    edge = (len(vertices) - 1, row_segments[row_end_index + 1])
                    #edges.append(edge)

        lat += GRID_LAT_STEP
        
        row_segments = next_row_segments
        
    return (vertices, edges, faces)

    
def generate_country_elevation(name, points, parts, collection):  

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

        vertices, edges, faces = create_grid(part_vertexes)

        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        
        object_name = name + "Elevation" + str(part_index)
        object = bpy.data.objects.new(object_name, mesh)    
        collection.objects.link(object)    

        #break

def generate_countries_elevation(white_list = None):    
    shape = shapefile.Reader("C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\ne_10m_admin_0_countries\\ne_10m_admin_0_countries.shp")

    records = shape.shapeRecords();
    print("Total number of records: ", len(records));
    
    try:
        collection = bpy.data.collections["ElevationGrids"]
    except:   
        collection = bpy.data.collections.new('ElevationGrids')
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
        generate_country_elevation(name_en, points, parts, collection)
        