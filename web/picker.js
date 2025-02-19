import { layoutImages } from "./layout.js";

function createElement(parent, type, attributes, clss) {
    const elem = document.createElement(type);
    Object.assign(elem, attributes);
    if (parent) parent.appendChild(elem);
    if (clss) {
        clss.split(" ").forEach(element => {
            elem.classList.add(element)
        });
    }   
    return elem;
 }

 class API {
    constructor(root) {
        this.root = root;
    }

    apiURL(route) {
        return route;
    }

    fetchApi(route, options) {
        options.headers = options.headers ?? {};
		options.headers["Comfy-User"] = this.user;
        options.headers["Content-Type"] = "application/json";
		return fetch(this.apiURL(route), options);
	}

    async call(path, method, body) {
        try {
            const r = this.fetchApi(path, {
                method: method,
                body: body ? JSON.stringify(body) : undefined,
            });
            const response = await r
            return response.json()
        } catch (error) { console.error(error); }        
    }

    async post(path, body) { return this.call(path, "POST", body) }

    async get(path) { return this.call(path, "GET") }
}

const api = new API("https://127.0.0.1:9191/")
var project_details
var project_status

async function load_images() {
    const urls = await( api.get('urls') )
    const iw = document.getElementById('image_wrap')
    const aspect_ratio = project_details.aspect_ratio ? parseFloat(project_details.aspect_ratio) : 1.0
    layoutImages(iw, urls, aspect_ratio, (i)=>respond({pick:`${i}`}), project_details.n_per_set)
}

async function respond(response) {
    await( api.post("response", response) )
    load_images()
    update_status()
}

async function restart() {
    await (api.get("reset",{}))
    build()
}

async function update_status() {
    project_status = await( api.get('status'))
    document.getElementById('status_wrap').innerHTML = project_status.html
}

async function update_buttons() {
    const buttons = document.getElementById('button_wrap')
    buttons.innerHTML = ''
    const reset = createElement(buttons, "button", {type:'button', innerText:"reset"})
    reset.addEventListener("click", (e)=>{
        e.stopPropagation()
        restart()
    })
    if (project_details.mode=='sort') {
        const kill = createElement(buttons, "button", {type:'button', innerText:"kill"})
        kill.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:'z'})
        })
        const work = createElement(buttons, "button", {type:'button', innerText:"work"})
        work.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:'x'})
        })
        const done = createElement(buttons, "button", {type:'button', innerText:"done"})
        done.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:'c'})
        })
        const vv = createElement(buttons, "button", {type:'button', innerText:"v"})
        vv.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:'v'})
        })
        const bb = createElement(buttons, "button", {type:'button', innerText:"b"})
        bb.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:'b'})
        })
        const skip = createElement(buttons, "button", {type:'button', innerText:"skip"}, "last")
        skip.addEventListener("click", (e)=>{
            e.stopPropagation()
            respond({rating:' '})
        })
    }
}

async function build() {
    project_details = await( api.get('project'))
    update_buttons()
    load_images()
    update_status()
}

document.addEventListener('DOMContentLoaded', build)