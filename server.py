from uvicorn import run
from fastapi import FastAPI
from server_modules.server_projects import Project, PickProject, SortProject, NoImagesException, NoMoreImagesException, button_labels
from server_modules.utils import serve_file, FileServeException
import os
from utilities.directories import OUTPUT, POSTFACE, RC, FINAL

app = FastAPI()

BUTTONS = button_labels(['bin','flux','pony','sdxl','done'])
_B = lambda k : BUTTONS + (button_labels(['AAA',]) if k=='d' else [])

DEFINITIONS = [ ("p", (POSTFACE, "unsorted")), ("d", RC),  ("c", (OUTPUT,"chroma")), ("cr", (OUTPUT,"chroma_rnd")), ("f", (OUTPUT,"fluxllm")), ] +\
              [ (f"{i}", (OUTPUT,f"cyber{i}")) for i in range(10) ]

DIRECTORIES = { k: d if isinstance(d,str) else os.path.join(*d) for k, d in DEFINITIONS }
PROJECTS = { k :(SortProject, { "directory" : DIRECTORIES[k], "buttons":_B(k) }) for k in DIRECTORIES }

PROJECTS['aaa'] = (SortProject, { "directory" : os.path.join(FINAL,'AAA'), "buttons":[] })
for sub in 'bxv':
    PROJECTS[ f'p{sub}'] = (SortProject, { "directory" : os.path.join(POSTFACE,sub), "buttons":button_labels(['bin','keep','priority']) })

def setup_project(n):
    if Project.current_project!=n: 
        Project.clear()
        if n in PROJECTS: Project.setup( PROJECTS[n][0], { **PROJECTS[n][1] }, n )
        
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

def splash(n:str):
    setup_project(n)
    return serve_file("index.html")

@app.get("/")
def root():
    return {}

@app.get("/list")
def list():
    def image_count(d):
        if not os.path.exists(d): return 0
        return len([f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in [".jpg", ".jpeg", ".png"]])
    l = { k:image_count(DIRECTORIES[k]) for k in DIRECTORIES }
    return { k:l[k] for k in l if l[k]}

@app.get("/splash")
def true_root(n:str):
    return error_wrapping(splash, n=n)

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