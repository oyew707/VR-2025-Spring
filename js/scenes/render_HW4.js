// import cg from "../render/core/cg.js";
// import { G2 } from "../util/g2.js";
// import { lcb, rcb } from "../handle_scenes.js";
// import { buttonState } from "../render/core/controllerInput.js";

// 🎯 **Load Predictions**
async function loadPredictions() {
    const data = await fetch('./predictions.json').then(response => response.text());
    return JSON.parse(data);
}

// 🎯 **VR Rendering Setup**
export const init = async model => {
    let points = [];
    let sceneFrames = await loadPredictions();
    let frameIndex = 0;

    // 🎯 **Spawn Spheres in a 10×10×10 Cube**
    function spawnSpheres(initialPositions) {
        points = initialPositions.map(([x, y, z, label]) => {
            let sphere = model.add('sphere');
            sphere.position = [x/10, y/10, z/10];
            sphere.color(labelToColor(label));
            return sphere;
        });
    }

    // 🎯 **Spawn Initial Spheres**
    spawnSpheres(sceneFrames[0]);
    console.log('points:', points.length);

    // 🎯 **Color Mapping for Labels**
    function labelToColor(label) {
        const colors = { 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1] };
        return colors[label] || [1, 1, 1];
    }

    // 🎯 **Animate Scene Frame-by-Frame**
    model.move(0,0.5,-1).animate(() => {
        if (sceneFrames.length === 0) return;

        let frameData = sceneFrames[frameIndex];
        console.log('frameData:', frameData.length, 'points:', points.length, 'frameIndex:', frameIndex);

        frameData.forEach(([x, y, z, label], i) => {

            let sphere = points[i];
            let color = labelToColor(label);
            sphere.identity().move(x/10, y/10, z/10).color(color).scale(0.01);
        });

        frameIndex = (frameIndex + 1) % sceneFrames.length;
    });


};
