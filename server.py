from uvicorn import run
from fastapi import FastAPI
from server_modules.server_projects import Project, PickProject, SortProject, NoSuchProjectException, NoImagesException, NoMoreImagesException
from server_modules.utils import serve_file
import os

app = FastAPI()
current_project = None

root_dir = r"C:\Users\chris\Documents\GitHub\ComfyUI\output"

PROJECTS = [
    #(PickProject, { "directory":r"C:\Users\chris\Documents\GitHub\ComfyUI\output\compare", "match":"" }),
    (SortProject, { "directory":r"A:\Images\candidates\resort", "buttons":['z', 'x', 'c', 'v', 'b'] }),
] + [
    (SortProject, { "directory" : os.path.join(root_dir, dir), "buttons":b or ['z', 'x', 'c', 'v', 'b', 'n'] }) 
            for dir, b in [("cyber1", ['z','x']), 
                           ("cyber2", ['z','x']), 
                           ("cyber3", None), 
                           ("cyber4", None), 
                           ("cyber5", None), 
                           ("fluxllm3", None), 
                           ("compare", None)]
]

def setup_project(n):
    global current_project
    if current_project!=n: 
        Project.current_project = None
        try: Project.setup( *PROJECTS[int(n)] )
        except (TypeError, IndexError): raise NoSuchProjectException(n)
    current_project = n

def error_wrapping(function, *args, **kwargs):
    try: return function(*args, **kwargs)
    except NoMoreImagesException: 
        return {"error": "End of project"}
    except NoImagesException:     
        return {"error": "Project is empty"}    
    except Exception as e: 
        print(e)    
        return {}

def splash(n):
    setup_project(n)
    return serve_file("index.html")

@app.get("/")
def root():
    return {}

@app.get("/splash")
def true_root(n:str):
    return error_wrapping(splash, n)

@app.get("/project")
def project():
    p = error_wrapping(Project.get_project)
    if isinstance(p,Project): return error_wrapping(p.project)
    else: return p

@app.get("/urls")
def urls():
    p = error_wrapping(Project.get_project)
    if isinstance(p,Project): return error_wrapping(p.next_image_set)
    else: return p

@app.get("/status")
def status():
    p = error_wrapping(Project.get_project)
    if isinstance(p,Project): return error_wrapping(p.status)
    else: return p

@app.get("/reset")
def reset():
    Project.current_project = None
    return {}

@app.post("/response")
def response(response:dict): 
    p = error_wrapping(Project.get_project)
    if isinstance(p,Project): return error_wrapping(p.response,response)
    else: return p

@app.get("/image/{file}")
def get_image(file:str): 
    p = error_wrapping(Project.get_project)
    if isinstance(p,Project): return error_wrapping(serve_file, file, p.directory)
    else: return p

@app.get("/{file}")
def get_file(file:str):
    return error_wrapping(serve_file, file)

if __name__=='__main__': run("server:app", port=9191, host='0.0.0.0', ssl_keyfile="key.pem", ssl_certfile="cert.pem")