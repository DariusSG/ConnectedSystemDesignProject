const projectIMGCanvas = document.getElementById('project-model');
const projectIMGContext = projectIMGCanvas.getContext('2d');

function loadImage(href, dx, dy, scale=1) {
    const image = new Image(60,45);
    image.src = href;
    image.onload = function drawImage() {
        projectIMGCanvas.width = this.naturalWidth * scale;
        projectIMGCanvas.height = this.naturalHeight * scale;

        projectIMGContext.drawImage(this, dx, dy, projectIMGCanvas.width, projectIMGCanvas.height);
        projectIMGContext.fillRect(40, 295, 162, 115);
        projectIMGContext.fillRect(205, 295, 162, 115);
        projectIMGContext.fillRect(375, 295, 162, 115);
        projectIMGContext.fillRect(38, 415, 495, 108);
    }
    return image;
}

loadImage("/static/images/projectModels/main_box.png", 0, 0, 0.8)


function getCursorPosition(canvas, event) {
    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    console.log("x: " + x + " y: " + y)
}

projectIMGCanvas.addEventListener('mousedown', function(e) {
    getCursorPosition(projectIMGCanvas, e)
})