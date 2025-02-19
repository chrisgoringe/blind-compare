from fastapi import HTTPException
from fastapi.responses import Response
from .server_projects import Project
import os

MEDIA = {
    ".js": ("text/javascript",'r'),
    ".css": ("text/css",'r'),
    ".html": ("text/html",'r'),
    ".png": ("image/png",'rb'),
    ".jpg": ("image/jpg",'rb'),
    ".jpeg": ("image/jpg",'rb'),
    ".ico": ("image/x-icon", 'rb'),
}

def serve_file(filepath, directory="web"):
    try:
        media_type, read_mode = MEDIA.get(os.path.splitext(filepath)[1].lower())
        with open(os.path.join(directory, filepath),read_mode) as f:
            return Response(content=f.read(), media_type=media_type )
    except TypeError:
        print(f"file {filepath} extension not recognised")
        return {}
    except Exception as e:
        print(f"{e}") 
        return {}
    
def serve_image(filename):
    return serve_file(filename, directory=Project.get_project().directory)