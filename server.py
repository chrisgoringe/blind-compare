from uvicorn import run
from fastapi import FastAPI
from server_modules.server_projects import Project, PickProject, SortProject
from server_modules.utils import serve_file, serve_image

app = FastAPI()
if True:
    Project.setup(SortProject, {
        "directory" : r"C:\Users\chris\Documents\GitHub\ComfyUI\output\temp",#candidates",
    })
else:
    Project.setup(PickProject, {
        "directory" : r"C:\Users\chris\Documents\GitHub\ComfyUI\output\compare",
        "match"     : "crow"
    })

@app.get("/")
def root(): return {}

@app.get("/splash")
def true_root(): return serve_file("index.html")

@app.get("/project")
def project(): return Project.get_project().project()

@app.get("/urls")
def urls(): return Project.get_project().next_image_set()

@app.get("/status")
def status(): return Project.get_project().status()

@app.get("/reset")
def reset(): 
    Project.current_project = None
    return {}

@app.post("/response")
def response(response:dict): return Project.get_project().response(response)

@app.get("/image/{file}")
def get_image(file:str): return serve_image(file)

@app.get("/{file}")
def get_file(file:str): return serve_file(file)

if __name__=='__main__': run("server:app", port=9191, host='0.0.0.0', ssl_keyfile="key.pem", ssl_certfile="cert.pem")