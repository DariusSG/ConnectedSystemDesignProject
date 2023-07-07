const projectIMGCanvas = document.getElementById('project-model');
const projectIMGContext = projectIMGCanvas.getContext('2d');

function loadImage(href, dx, dy, scale=1) {
    const image = new Image(60,45);
    image.src = href;
    image.onload = function drawImage() {
        projectIMGCanvas.width = this.naturalWidth * scale;
        projectIMGCanvas.height = this.naturalHeight * scale;

        projectIMGContext.drawImage(this, dx, dy, projectIMGCanvas.width, projectIMGCanvas.height);




    }
    return image;
}

loadImage("/static/images/projectModels/main_box.png", 0, 0, 0.8)


projectIMGCanvas.addEventListener('click', function(e) {
    function isIntersecting(e, rect_x, rect_y, rect_w, rect_h) {
        function between(val, min, max) {
            return val >= min && val <= max;
        }

        const rect = projectIMGCanvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        return !!(between(x, rect_x, rect_x + rect_w) && between(y, rect_y, rect_y + rect_h));
    }

    if (isIntersecting(e, 40, 295, 162, 115)) {
        projectIMGContext.fillRect(40, 295, 162, 115);
        console.log("Box 1 is clicked");
    }
    if (isIntersecting(e, 205, 295, 162, 115)) {
        projectIMGContext.fillRect(205, 295, 162, 115);
        console.log("Box 2 is clicked");
    }
    if (isIntersecting(e, 375, 295, 162, 115)) {
        projectIMGContext.fillRect(375, 295, 162, 115);
        console.log("Box 3 is clicked");
    }
    if (isIntersecting(e, 38, 415, 495, 108)) {
        projectIMGContext.fillRect(38, 415, 495, 108);
        console.log("Box 4 is clicked");
    }
})