const fs = require('fs');
const cg = require("../render/core/cg.js");
const { G2 } = require("../util/g2.js");
const { lcb, rcb } = require("../handle_scenes.js");
const { buttonState } = require("../render/core/controllerInput.js");

// 🎯 **Load Predictions**
function loadPredictions() {
    const data = fs.readFileSync("predictions.json");
    return JSON.parse(data);
}

// 🎯 **VR Rendering Setup**
module.exports.init = async model => {
    let points = [];
    let sceneFrames = loadPredictions();
    let frameIndex = 0;

    // 🎯 **Spawn Spheres in a 10×10×10 Cube**
    function spawnSpheres(initialPositions) {
        points = initialPositions.map(([x, y, z, label]) => {
            let sphere = model.add('sphere');
            sphere.position = [x, y, z];
            sphere.color(labelToColor(label));
            return sphere;
        });
    }

    // 🎯 **Color Mapping for Labels**
    function labelToColor(label) {
        const colors = { 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1] };
        return colors[label] || [1, 1, 1];
    }

    // 🎯 **Animate Scene Frame-by-Frame**
    model.animate(() => {
        if (sceneFrames.length === 0) return;

        let frameData = sceneFrames[frameIndex];

        frameData.forEach(([x, y, z, label], i) => {
            let sphere = points[i];
            sphere.identity().move(x, y, z).scale(0.1);
        });

        frameIndex = (frameIndex + 1) % sceneFrames.length;
    });

    // 🎯 **Spawn Initial Spheres**
    spawnSpheres(sceneFrames[0]);
};
