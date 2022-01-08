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