import gc
import HydrusExceptions
import HydrusGlobals as HG
import os

def GetAllPaths( raw_paths ):
    
    file_paths = []
    
    paths_to_process = raw_paths
    
    while len( paths_to_process ) > 0:
        
        next_paths_to_process = []
        
        for path in paths_to_process:
            
            if HG.view_shutdown:
                
                raise HydrusExceptions.ShutdownException()
                
            
            if os.path.isdir( path ):
                
                subpaths = [ os.path.join( path, filename ) for filename in os.listdir( path ) ]
                
                next_paths_to_process.extend( subpaths )
                
            else:
                
                file_paths.append( path )
                
            
        
        paths_to_process = next_paths_to_process
        
    
    return file_paths
    
