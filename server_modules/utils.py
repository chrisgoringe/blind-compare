from fastapi.responses import Response
import os, time

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

class Timer:
    def __init__(self, label, s_fmt=None, e_fmt=None):
        self.label    = label
        self.s_fmt = s_fmt or "--- starting  '{:>30}'    "
        self.e_fmt = e_fmt or "--- completed '{:>30}' in {:>6.3}s"

    def __enter__(self):
        print(self.s_fmt.format(self.label)) 
        self.start_time = time.monotonic()

    def __exit__(self ,type, value, traceback):
        duration = time.monotonic() - self.start_time
        print (self.e_fmt.format(self.label, duration))