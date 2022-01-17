import shapefile
import math
import PIL
import os
from PIL import Image, ImageDraw
from Constants import *

"""
def get_map_resolution(image_width):    
    meters = 2 * math.pi * EARTH_RADIUS
    meters_per_pixel = meters / image_width
    return meters_per_pixel

    image_width = (2 * math.pi * EARTH_RADIUS) / meters_per_pixel
"""

def project(spherical_point):
    lat1 = 0
    lat0 = 0
    lon0 = 0

    lon = spherical_point[0]
    lat = spherical_point[1]
    x = EARTH_RADIUS * (lon - lon0) * math.cos(lat1)
    y = EARTH_RADIUS * (lat - lat0)
    return (x, y)

def get_path(relative_path):    
    return os.path.join("C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\", relative_path)

def get_map_resolution(image_width):    
    meters = 2 * math.pi * EARTH_RADIUS
    meters_per_pixel = meters / image_width
    return meters_per_pixel

def deg2rad(sp_p):
    return (math.radians(sp_p[0]), math.radians(sp_p[1]))    

class LandShapeRasterizer():
    def __init__(self, height):       
        self.image_width = int(height * 2)
        self.image_height = int(height)
        self.resolution = get_map_resolution(self.image_width)
        print(f"W: {self.image_width}, H: {self.image_height}, Res: {self.resolution}")
        self.image = Image.new('L', (self.image_width, self.image_height), color = 'black')
        self.drawer = ImageDraw.Draw(self.image )  
          

    def rasterize_part(self, sp_points):
        polygon_points = []
        for sp in sp_points:
            sp_rad = deg2rad(sp)
            x_proj, y_proj = project(sp_rad);
            x_pixel = x_proj / self.resolution + (self.image_width / 2)
            y_pixel = self.image_height / 2 - y_proj / self.resolution
            polygon_points.append((x_pixel, y_pixel))

        self.drawer.polygon(polygon_points, fill ="#FFFFFF")
        pass

    def rasterize_feature(self, points, parts):  

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
            
            self.rasterize_part(part_vertexes);

    def rasterize_shapefile(self):
        shape = shapefile.Reader(get_path(LAND_SHP))

        records = shape.shapeRecords();
        print("Total number of records: ", len(records));

        counter = 0
        for feature in shape.shapeRecords():
            name_en = "Land" + str(counter)
            counter += 1
            
            shape = feature.shape;
            parts = shape.parts;
            points = shape.points;
            print(name_en + ": " + str(len(points)) + " points, ", len(parts), " parts");
            self.rasterize_feature(points, parts)

    def show(self):
        self.image.show()

    def save(self, cols, rows):
        #self.image.save("land.png")
        segment_size = self.image.width / cols
        for x in range(0, cols):
            for y in range(0, rows):
                area = (segment_size * x, segment_size * y, segment_size * (x + 1), segment_size * (y + 1))
                cropped_img = self.image.crop(area)
                cropped_img.save(f"C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\TopographyMap\\land{x}{y}.png")

        pass

def create_png():
    rasterizer = LandShapeRasterizer(21600)
    rasterizer.rasterize_shapefile()
    rasterizer.save(4, 2)

if __name__ == "__main__":
    create_png()