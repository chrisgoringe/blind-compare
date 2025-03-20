from uvicorn import run
from fastapi import FastAPI
from server_modules.server_projects import Project, PickProject, SortProject, NoSuchProjectException, NoImagesException, NoMoreImagesException
from server_modules.utils import serve_file
import os
from typing import Optional

app = FastAPI()

root_dirs = [
    r"C:\Users\chris\Documents\GitHub\ComfyUI\output",
    r"A:\Images\candidates"
]

names = { 'bin':'z', 'flux':'x', 'done':'c', 'out':'v', 'pony':'b', 'bad':'1', 'ok':'2', 'priority':'3' }

b_pony = [names.get(x,x) for x in ['bin','pony','flux','done','out']]  
b_flux = [names.get(x,x) for x in ['bin','flux','pony','done','out']]
b_123  = [names.get(x,x) for x in ['bad','pony','flux', 'priority', 'done']]

PROJECTS = {
    k :(SortProject, { "directory" : os.path.join(root_dirs[n], dir), "buttons":b, **a }) 
            for k, n, dir, b, a in [
                            ("c", 0, "compare",  b_pony, {}), 
                            ("1", 0, "cyber1",   b_pony, {}), 
                            ("2", 0, "cyber2",   b_pony, {}), 
                            ("3", 0, "cyber3",   b_pony, {}), 
                            ("f", 0, "fluxllm3", b_flux, {}), 
                            ("r", 1, "resort",   b_123,  {}),
                            ]
}

def setup_project(n, m):
    if Project.current_project!=n: 
        Project.clear()
        if n in PROJECTS: Project.setup( *PROJECTS[n], n )
        else:             Project.setup( PickProject, { "directory":os.path.join(root_dirs[0],"compare"), "match":n, "move_chosen":m }, n)

def error_wrapping(function, *args, **kwargs):
    try: return function(*args, **kwargs)
    except NoMoreImagesException: 
        return {"error": "End of project"}
    except NoImagesException:     
        return {"error": "Project is empty"}    
    except Exception as e: 
        print(e)    
        return {}

def splash(n:str, m:Optional[str]):
    setup_project(n, m)
    return serve_file("index.html")

@app.get("/")
def root():
    return {}

@app.get("/splash")
def true_root(n:str, m:Optional[str]=None):
    return error_wrapping(splash, n, m)

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
    Project.clear()
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