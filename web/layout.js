export function layoutImages(container, imageUrls, aspectRatio, imgClick, columns, used_vertical_space) {
    container.innerHTML = ''
    const image_count = imageUrls.length
    if (!columns) {
        const screenAspectRatio = window.innerWidth / window.innerHeight
        const ideal_columns_per_row = screenAspectRatio/aspectRatio
        const ideal_number_of_rows = Math.sqrt(image_count/ideal_columns_per_row)
        columns = Math.round(image_count / ideal_number_of_rows)
    }
    const rows = Math.ceil(image_count/columns)

    // Create and append images to the container
    imageUrls.forEach((url, i) => {
        const imgContainer = document.createElement('div');
        imgContainer.style.maxWidth = `${100/columns}%`;
        imgContainer.style.maxHeight = `${(window.innerHeight-used_vertical_space)/rows}px`

        const img = document.createElement('img');
        img.src = url;


        img.addEventListener("click", (e)=>{imgClick(i)})

        imgContainer.appendChild(img);
        container.appendChild(imgContainer);
    });

}