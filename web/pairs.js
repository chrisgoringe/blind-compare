

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
    fetchApi(route, options) {
        options.headers = options.headers ?? {};
        options.headers["Content-Type"] = "application/json";
		return fetch(route, options);
	}

    async call(method, path, body) {
        try {
            const r = this.fetchApi(path, {
                method: method,
                body: body ? JSON.stringify(body) : undefined,
            });
            const response = await r
            return response.json()
        } catch (error) { console.error(error); }        
    }

    async get(path, body) { return this.call("GET", path, body) }
}

const api = new API()

async function load_images() {
    const response = await( api.get('pair') )
    const status = response[0]
    
    if (status=="DONE" || status=="WAITING") {
        document.getElementById('status').innerText = `${status}`
        document.getElementById('images').style.display = 'none'
        if (status=="WAITING") setTimeout(load_images, 5000)
    } else {
        document.getElementById('status').innerText = `similarity = ${status}`
        document.getElementById('images').style.display = "flex"  
        document.getElementById('image1').src = `img?i=0&r=${Math.random()}`
        document.getElementById('image1title').innerText = response[1]
        document.getElementById('image2').src = `img?i=1&r=${Math.random()}`
        document.getElementById('image2title').innerText = response[2]
    }
}


async function delete_left() {
    await api.get('del?x=0')
    await load_images()
}
async function delete_right() {
    await api.get('del?x=1')
    await load_images()
}
async function delete_both() {
    await api.get('del?x=0')
    await api.get('del?x=1')
    await load_images()
}



async function build() {
    const buttons = createElement(document.body,'div',{id:'buttons'})
    const imgs = createElement(document.body, 'div', {id:'images'})
    
    const i1 = createElement(imgs,'span',{},'frame')
    createElement(i1, 'img', {id:"image1"}).addEventListener('click', delete_left)
    createElement(i1,'span',{id:"image1title"})
    const i2 = createElement(imgs,'span',{},'frame')
    createElement(i2, 'img', {id:"image2"}).addEventListener('click', delete_right)
    createElement(i2,'span',{id:"image2title"})

    createElement(buttons, 'span', {innerText:"Click image to delete"})
    createElement(buttons, 'button', {innerText:"Next"}).addEventListener('click', load_images)
    createElement(buttons, 'button', {innerText:"Delete Both"}).addEventListener('click', delete_both)
    createElement(buttons,'span', {id:"status"})

    await load_images()
}

document.addEventListener('DOMContentLoaded', build)
