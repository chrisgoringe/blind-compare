from fastapi.responses import Response
import os

class ProjectException(Exception): pass
class FileServeException(ProjectException):
    def __init__(self, filepath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath=filepath
class UnknownExtensionException(FileServeException): pass

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
        raise UnknownExtensionException(filepath, os.path.splitext(filepath)[1].lower())
    except Exception as e:
        raise FileServeException(filepath, f"{e}")

