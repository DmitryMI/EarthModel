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

class ImageMap():

    HEIGHT_MIN = 0
    HEIGHT_MAX = 6400

    @staticmethod
    def lerp(a, b, alpha):
        return (b - a) * alpha + a

    @staticmethod
    def get_height(pixel):    
        return lerp(HEIGHT_MIN, HEIGHT_MAX, pixel / 255)

    def get_map_resolution(self):    
        meters = 2 * math.pi * EARTH_RADIUS
        meters_per_pixel = meters / self.image_width
        return meters_per_pixel


    def get_pixel_coordinate(self, spherical_point):
        (x, y) = project(spherical_point)
        x_pixel = x / self.image_resolution
        y_pixel = y / self.image_resolution
        return (x_pixel, y_pixel)


    def get_image_and_pixel_coordinate(self, pixel_point):
        width = (self.segment_size * self.segments_num_w)
        height = (self.segment_size * self.segments_num_h)
        x = pixel_point[0] + width / 2
        y = pixel_point[1] + height / 2
        x_index = int(x // self.segment_size)
        y_index = int(y // self.segment_size)
        x_trans = x - x_index * self.segment_size
        y_trans = self.segment_size - (y - y_index * self.segment_size)
        return (x_index, self.segments_num_h - y_index - 1, x_trans, y_trans)

    def get_height_from_spherical(sp_p, height_scale):        
        pixel = self.get_pixel(sp_p, resolution)
        height = self.get_height(pixel)
        scaled_height = height_scale * height  * (MODEL_RADIUS) / EARTH_RADIUS
        return scaled_height


    def get_pixel(self, sp_p):
        pixel_coordinate = self.get_pixel_coordinate(sp_p)
        (i, j, x, y) = self.get_image_and_pixel_coordinate(pixel_coordinate)

        if len(self.loaded_images) <= i:
            return 0
        if len(self.loaded_images[i]) <= j:
            return 0
    
        im = self.loaded_images[i][j]
        if im.size[0] <= x or im.size[1] <= y or x < 0 or y < 0:
            return 0
        pixel = im.getpixel((x, y))
        return pixel

        
    def load_images(self, cols, rows, get_image_name):
        for x in range(0, cols):
            self.loaded_images.append([])
            for y in range(0, rows):
                image_name = get_image_name(x, y)
                print("Image ", image_name, f"loaded into {x}, {y}\n")
                self.loaded_images[x].append(Image.open(image_name))

    def __init__(self, cols, rows, path_constructor):
        self.loaded_images = []
        self.load_images(cols, rows, path_constructor)
        self.segment_size = self.loaded_images[0][0].width
        self.image_width = self.segment_size * cols
        self.image_resolution = self.get_map_resolution()
        self.segments_num_w = cols
        self.segments_num_h = rows        



IMAGE_DIR = "C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\TopographyMap\\"

def get_image_name(x_index, y_index):
    letter = ['A', 'B', 'C', 'D'][x_index]
    digit = y_index + 1
    path = IMAGE_DIR + f"gebco_08_rev_elev_{letter}{digit}_grey_geo.tif"
    return path

def get_land_raster(x_index, y_index):
    path = IMAGE_DIR + f"land{x_index}{y_index}.png"
    return path
        
def generate_globe(lat_segments = 600, lon_segments = 600, height_scale = 20):    

    elevationMap = ImageMap(4, 2, get_image_name)    
    landRaster = ImageMap(4, 2, get_land_raster)

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
            
            pixel = elevationMap.get_pixel((lon, lat))
            height = elevationMap.get_height(pixel)

            land_pixel = landRaster.get_pixel((lon, lat))
            if land_pixel == 0:
                height = -1000

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