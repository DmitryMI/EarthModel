import math
import os
import bpy
from importlib import reload, import_module    

def get_path(relative_path):
    return os.path.join(bpy.path.abspath("//"), relative_path)

def vector3_transform(vector3, delta):
    return (vector3[0] + delta[0], vector3[1] + delta[1], vector3[2] + delta[2])

def get_center(verts):
    sumx = 0
    sumy = 0
    sumz = 0
    
    for vertex in verts:
        sumx += vertex[0]
        sumy += vertex[1]
        sumz += vertex[2]
    
    x = sumx / len(verts)
    y = sumy / len(verts)
    z = sumz / len(verts)
    
    return (x, y, z)

def import_all():    
    modules = []
    #for module_name in os.listdir("C:\\Users\\DmitryBigPC\\Documents\\GitHub\\EarthModel\\PythonScripts\\PythonScripts"):
    scripts_dir = os.path.join(bpy.path.abspath("//"), "PythonScripts\\PythonScripts")
    print("Searching for code in", scripts_dir)
    for module_name in os.listdir(scripts_dir):
        if module_name == '__init__.py' or module_name[-3:] != '.py':
            continue
        print("Importing", module_name[:-3])
        #module = __import__(module_name[:-3], locals(), globals())
        module = import_module(module_name[:-3]) 
        modules.append(module)
        print("Reloading", module_name[:-3])
        reload(module)
    del module_name
    return modules

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

def deg2rad(sp_p):
    return (math.radians(sp_p[0]), math.radians(sp_p[1]))    

def sp2cart_rad(sphere_point, radius):  
    lon = sphere_point[0]
    lat = sphere_point[1]
    x = radius * math.cos(lat) * math.cos(lon)
    y = radius * math.cos(lat) * math.sin(lon)
    z = radius * math.sin(lat)
    #print("From " + str(sphere_point) + " to " + str((x, y, z)))
    return (x, y, z)
    
def removeMeshFromMemory (mesh):
    
    try:
        mesh.user_clear()
        can_continue = True
    except:
        can_continue = False
    
    if can_continue == True:
        try:
            bpy.data.meshes.remove(mesh)
            result = True
        except:
            result = False
    else:
        result = False
        
    return result

    
def delete_all_meshes():
    for mesh in bpy.data.meshes:
        # This check is essential to preventing crashes. (never remove without a user count check for zero) 
        if mesh.users == 0:     
            r = removeMeshFromMemory(mesh)