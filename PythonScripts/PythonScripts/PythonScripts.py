from PIL import Image, ImageDraw
import math

# Forward
# x = R(lon - lon0) * cos(lat1)
# y = R(lat - lat0)

# Reverse
# lon = x / (R * cos(lat1)) + lon0
# lat = y / R + lat0

# lat1 - standard parallels (north and south of the equator)
# where the scale of the projection is true

# lat0 - central parallel of the map
# lon0 - central meridian of the map

IMAGE_DIR = "C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\TopographyMap\\"

MODEL_RADIUS = 1000
R = 6378137
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
    x = R * (lon - lon0) * math.cos(lat1)
    y = R * (lat - lat0)
    return (x, y)

def deproject(cartesian_point):
    x = cartesian_point[0]
    y = cartesian_point[1]
    lon = x / (R * math.cos(lat1)) + lon0
    lat = y / R + lat0
    return (lon, lat)

def deg2rad(sp_p):
    return (math.radians(sp_p[0]), math.radians(sp_p[1]))

def get_map_resolution(image_width):    
    meters = 2 * math.pi * R
    meters_per_pixel = meters / image_width
    return meters_per_pixel

def get_pixel_coordinate(spherical_point, image_resolution):
    (x, y) = project(spherical_point)
    print("Projected: ", x, y)
    x_pixel = x / image_resolution
    y_pixel = y / image_resolution
    print("On image: ", x_pixel, y_pixel)
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
    print(i, j, x, y)
    #im = loaded_images[i][j]
    #pixel = im.get_pixel(x, y)
    pixel = (0, 0, 0)
    return pixel


def lerp(a, b, alpha):
    return (b - a) * alpha + a

def get_height(pixel):
    R,G,B = pixel 
    brightness = sum([R,G,B])/3
    return lerp(HEIGHT_MIN, HEIGHT_MAX, brightness)

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

load_images()

resolution = get_map_resolution(SEGMENT_SIZE*SEGMENTS_NUM_W)
print("Map resolution: ", resolution)

vertices = []
edges = []
faces = []

lat_segments = 10
lon_segments = 10
for lat_i in range(1, lat_segments - 1):
    for lon_i in range(1, lon_segments - 1):
        lat = lerp(-math.pi / 2, math.pi / 2, lat_i / lat_segments)
        lon = lerp(-math.pi, math.pi, lon_i / lon_segments)
        print("lon: ", math.degrees(lon), "lat: ", math.degrees(lat))
        pixel = get_pixel((lon, lat), resolution)
        height = get_height(pixel)
        scaled_height = height  * (MODEL_RADIUS) / R
        cartesian_point = sp2cart((lon, lat), MODEL_RADIUS + scaled_height)
        vertices.append(cartesian_point)
