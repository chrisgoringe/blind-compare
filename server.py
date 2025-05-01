from uvicorn import run
from fastapi import FastAPI
from server_modules.server_projects import Project, PickProject, SortProject, NoSuchProjectException, NoImagesException, NoMoreImagesException, SortingNames
from server_modules.utils import serve_file, FileServeException
import os
from typing import Optional

app = FastAPI()

root_dirs = [
    r"C:\Users\chris\Documents\GitHub\ComfyUI\output",
    r"A:\Images\candidates",
    r"A:\Images\done",
]



b_pony = [SortingNames.get(x,x) for x in ['bin','pony','flux','sdxl','keep','done','out']]  
b_flux = [SortingNames.get(x,x) for x in ['bin','flux','pony','sdxl','keep','done','out']]
b_123  = [SortingNames.get(x,x) for x in ['bad','pony','flux', 'priority', 'done']]
b_done = [SortingNames.get(x,x) for x in ['bin','done','pony', 'flux', 'sdxl',]]
b_resort = [SortingNames.get(x,x) for x in ['bin','pony','flux','sdxl','done', ]]

dir_nd = lambda n,d : os.path.join(root_dirs[n], d)
dir_i = lambda i : dir_nd(0,"cyber"+i)

PROJECTS = {}

PROJECTS = PROJECTS | {
    k :(SortProject, { "directory" : dir_nd(n,d), "buttons":b }) 
            for k, n, d, b in [ ("c", 0, "compare", b_pony), 
                                ("f", 0, "fluxllm", b_flux), 
                                ("r", 1, "resort",  b_resort),
                              ]
}

PROJECTS = PROJECTS | { i:(SortProject, { "directory" : dir_i(i), "buttons":b_pony }) for i in "1234567" }

PROJECTS = PROJECTS | { "d":(SortProject, { "directory" : root_dirs[2], "buttons":b_done }) }

def setup_project(n, m, u):
    tag = f"{n}.{m}.{u}"
    if Project.current_project!=tag: 
        Project.clear()
        if n in PROJECTS: Project.setup( PROJECTS[n][0], { **PROJECTS[n][1], "match":m }, tag )
        else:             Project.setup( PickProject, { "directory":os.path.join(root_dirs[0],"compare"), "match":n, "move_chosen":m, "move_unchosen":u }, tag)

def error_wrapping(function, *args, **kwargs):
    clear_on_error = kwargs.pop('clear_on_error', False)
    r = {}
    try: 
        return function(*args, **kwargs)
    except NoMoreImagesException: r = {"error": "End of project"}
    except NoImagesException:     r = {"error": "Project is empty"}
    except FileServeException as e:
        if os.path.splitext(e.filepath)[1]=='.ico': r = {}
        else:                     r = {"FileServeException": f"{e.filepath}"}
    except Exception as e:        r = {"exception":f"{e}"}
    if clear_on_error: Project.clear()
    if r: print(r)
    return r

def splash(n:str, m:Optional[str], u:Optional[str]):
    setup_project(n, m, u)
    return serve_file("index.html")

@app.get("/")
def root():
    return {}

@app.get("/splash")
def true_root(n:str, m:Optional[str]=None, u:Optional[str]=None):
    return error_wrapping(splash, n=n, m=m, u=u)

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

last_status = None
@app.get("/status")
def status():
    try:
        p = Project.get_project()
        status = p.status()
        return status
    except: 
        pass

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