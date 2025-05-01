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

 var names = { }

 function get_name(letter) {
    return names[letter] || letter
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
    if (urls.error) {
        report_error(urls.error)
        return
    }
    const iw = document.getElementById('image_wrap')
    const aspect_ratio = project_details.aspect_ratio ? parseFloat(project_details.aspect_ratio) : 1.0
    layoutImages(iw, urls, aspect_ratio, (i)=>respond({pick:`${i}`}), project_details.n_per_set, (iw.getBoundingClientRect().y+4))
    document.getElementById('button_wrap').childNodes.forEach((b)=>{b.disabled = false})
}

async function respond(response, image_unchanged) {
    if (!image_unchanged) {
        document.getElementById('button_wrap').childNodes.forEach((b)=>{b.disabled = true})
        document.getElementById('image_wrap').innerHTML = ''
    }
    const reply = await( api.post("response", response) )
    if (reply.info) document.getElementById('status_wrap').innerHTML = reply.info
    if (image_unchanged) return
    load_images()
    update_status()
}

async function restart() {
    await (api.get("reset",{}))
    build()
}

async function update_status() {
    project_status = await( api.get('status'))
    if (project_status.error) {
        report_error(project_status.error)
        return
    }
    document.getElementById('status_wrap').innerHTML = project_status.html
}

function keyPressed(e) {
    if ("zzxcvbnm".includes(e.key)) {
        respond({rating:e.key})
    }
}

async function update_buttons(just_reset) {
    const buttons = document.getElementById('button_wrap')
    buttons.innerHTML = ''
    const reset = createElement(buttons, "button", {type:'button', innerText:"reset"})
    reset.addEventListener("click", (e)=>{
        e.stopPropagation()
        restart()
    })
    if (just_reset) return
    if (project_details.mode=='sort') {
        if (project_details.labels) {
            names = project_details.labels
        }
        project_details.buttons.forEach((letter)=>{
            const button = createElement(buttons, "button", {type:'button', innerText:get_name(letter)})
            button.addEventListener("click", (e)=>{
                e.stopPropagation()
                respond({rating:letter})
            })
        })
    }
        
    const skip = createElement(buttons, "button", {type:'button', innerText:"skip"}, "last")
    skip.addEventListener("click", (e)=>{
        e.stopPropagation()
        respond({rating:' '})
    })
    skip.style.marginLeft = '30px'

    const undo = createElement(buttons, "button", {type:'button', innerText:"undo"}, "last")
    undo.addEventListener("click", (e)=>{
        e.stopPropagation()
        respond({rating:'__undo__'})
    })

    const more_info = createElement(buttons, "button", {type:'button', innerText:"info"}, "last")
    more_info.addEventListener("click", (e)=>{
        e.stopPropagation()
        respond({rating:'__info__'}, true)
    })

}

function report_error(error) {
    update_buttons(true)
    document.getElementById('image_wrap').innerHTML = ''
    document.getElementById('status_wrap').innerHTML = error
}

async function build() {
    project_details = await( api.get('project'))
    if (project_details.error) {
        report_error(project_details.error)
        return
    } 
    update_buttons()
    load_images()
    update_status()
}

document.addEventListener('DOMContentLoaded', build)
document.addEventListener('keypress', keyPressed)