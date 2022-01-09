from PIL import Image, ImageDraw
from Common import *
from Constants import *
import math
import sys
import bpy


# Forward
# x = EARTH_RADIUS(lon - lon0) * cos(lat1)
# y = EARTH_RADIUS(lat - lat0)

# Reverse
# lon = x / (EARTH_RADIUS * cos(lat1)) + lon0
# lat = y / EARTH_RADIUS + lat0

# lat1 - standard parallels (north and south of the equator)
# where the scale of the projection is true

# lat0 - central parallel of the map
# lon0 - central meridian of the map

IMAGE_DIR = "C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\TopographyMap\\"

lat1 = 0
lat0 = 0
lon0 = 0
HEIGHT_MIN = 0
HEIGHT_MAX = 6400
SEGMENT_SIZE = 10800
SEGMENTS_NUM_W = 4
SEGMENTS_NUM_H = 2

loaded_images = []

def project(spherical_point):
    lon = spherical_point[0]
    lat = spherical_point[1]
    x = EARTH_RADIUS * (lon - lon0) * math.cos(lat1)
    y = EARTH_RADIUS * (lat - lat0)
    return (x, y)

def deproject(cartesian_point):
    x = cartesian_point[0]
    y = cartesian_point[1]
    lon = x / (EARTH_RADIUS * math.cos(lat1)) + lon0
    lat = y / EARTH_RADIUS + lat0
    return (lon, lat)

def get_map_resolution(image_width):    
    meters = 2 * math.pi * EARTH_RADIUS
    meters_per_pixel = meters / image_width
    return meters_per_pixel

def get_pixel_coordinate(spherical_point, image_resolution):
    (x, y) = project(spherical_point)
    #print("Projected: ", x, y)
    x_pixel = x / image_resolution
    y_pixel = y / image_resolution
    #print("On image: ", x_pixel, y_pixel)
    return (x_pixel, y_pixel)

def get_image_and_pixel_coordinate(pixel_point):
    width = (SEGMENT_SIZE * SEGMENTS_NUM_W)
    height = (SEGMENT_SIZE * SEGMENTS_NUM_H)
    x = pixel_point[0] + width / 2
    y = pixel_point[1] + height / 2
    x_index = int(x // SEGMENT_SIZE)
    y_index = int(y // SEGMENT_SIZE)
    x_trans = x - x_index * SEGMENT_SIZE
    y_trans = SEGMENT_SIZE - (y - y_index * SEGMENT_SIZE)

    return (x_index, SEGMENTS_NUM_H - y_index - 1, x_trans, y_trans)

def get_image_name(x_index, y_index):
    letter = ['A', 'B', 'C', 'D'][x_index]
    digit = y_index + 1
    path = IMAGE_DIR + f"gebco_08_rev_elev_{letter}{digit}_grey_geo.tif"
    return path

def load_images():
    for x in range(0, 4):
        loaded_images.append([])
        for y in range(0, 2):
            image_name = get_image_name(x, y)
            print("Image ", image_name, f"loaded into {x}, {y}\n")
            loaded_images[x].append(Image.open(image_name))

def get_pixel(sp_p, image_resolution):
    pixel_coordinate = get_pixel_coordinate(sp_p, image_resolution)
    (i, j, x, y) = get_image_and_pixel_coordinate(pixel_coordinate)
    #print(i, j, x, y)
    
    if len(loaded_images) <= i:
        return 0
    if len(loaded_images[i]) <= j:
        return 0
    
    im = loaded_images[i][j]
    if im.size[0] <= x or im.size[1] <= y or x < 0 or y < 0:
        return 0
    pixel = im.getpixel((x, y))
    return pixel


def lerp(a, b, alpha):
    return (b - a) * alpha + a

def get_height(pixel):    
    return lerp(HEIGHT_MIN, HEIGHT_MAX, pixel / 255)
    
def get_height_from_spherical(sp_p, height_scale):
    if loaded_images is None or len(loaded_images) == 0:
        load_images()

    resolution = get_map_resolution(SEGMENT_SIZE*SEGMENTS_NUM_W)
    pixel = get_pixel(sp_p, resolution)
    height = get_height(pixel)
    scaled_height = height_scale * height  * (MODEL_RADIUS) / EARTH_RADIUS
    return scaled_height
        
def generate_globe(lat_segments = 600, lon_segments = 600, height_scale = 20):    
    load_images()

    resolution = get_map_resolution(SEGMENT_SIZE*SEGMENTS_NUM_W)
    print("Map resolution: ", resolution)

    try:
        collection = bpy.data.collections["Elevation"]
    except:   
        collection = bpy.data.collections.new("Elevation")
        bpy.context.scene.collection.children.link(collection)

    mesh_name = "ElevationMesh"
    mesh = bpy.data.meshes.new(mesh_name)     

    vertices = []
    edges = []
    faces = []

    
    lat = -math.pi / 2
    lon = -math.pi
    lat_step = math.pi / lat_segments
    lon_step = 2 * math.pi / lon_segments
    lat_start = 1
    lat += lat_step * lat_start
    for lat_i in range(lat_start, lat_segments):
        for lon_i in range(0, lon_segments + 1):
            
            if(lon_i == lon_segments):
                last_vertex = len(vertices) - 1         
                first_vertex = len(vertices) - lon_segments            
                
                edge = (last_vertex, first_vertex)
                edges.append(edge)
                
                if lat_i > lat_start:
                    upper_right_vertex = first_vertex - lon_segments
                    upper_left_vertex = last_vertex - lon_segments
                    face = (first_vertex, last_vertex, upper_left_vertex, upper_right_vertex)
                    #print(face)
                    faces.append(face)
                continue
            
            pixel = get_pixel((lon, lat), resolution)
            height = get_height(pixel)
            scaled_height = height_scale * height  * (MODEL_RADIUS) / EARTH_RADIUS
            cartesian_point = sp2cart_rad((lon, lat), MODEL_RADIUS + scaled_height)
            vertices.append(cartesian_point)
            last = len(vertices) - 1
            left_vertex = last - 1
            upper_vertex = last - lon_segments
            upper_left_vertex = upper_vertex - 1
            
            if lon_i > 0:
                edge = (last, last - 1)
                edges.append(edge)
            if lat_i > lat_start:
                edge = (last, upper_vertex)
                edges.append(edge)
                
            if lon_i > 0 and lat_i > lat_start:
                face = (last, left_vertex, upper_left_vertex, upper_vertex)
                faces.append(face)
            
            lon += lon_step       
           
        
        lat += lat_step
        lon = -math.pi
           
            
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    object_name = "ElevationMesh"
    object = bpy.data.objects.new(object_name, mesh)    
    collection.objects.link(object)