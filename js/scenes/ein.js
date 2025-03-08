// import { G2 } from "../util/g2.js";
// import { lcb, rcb } from "../handle_scenes.js"; // Left and right controller beams
// import * as cg from "../render/core/cg.js";
// import { buttonState } from "../render/core/controllerInput.js";
// import { Gltf2Node } from "../render/nodes/gltf2.js";
// import * as global from "../global.js";
// import * as tf from '@tensorflow/tfjs';

const tf = require('@tensorflow/tfjs');
const cg = require("../render/core/cg.js");
const { G2 } = require("../util/g2.js");
const { lcb, rcb } = require("../handle_scenes.js");
const { buttonState } = require("../render/core/controllerInput.js");
const { Gltf2Node } = require("../render/nodes/gltf2.js");
const global = require("../global.js");

// 🎯 **Load and preprocess the Iris dataset**
async function loadIrisDataset() {
    const response = await fetch('https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv');
    const text = await response.text();
    const rows = text.split('\n').slice(1);

    let data = [];
    let labels = [];

    for (let row of rows) {
        let values = row.split(',');
        let features = values.slice(0, 4).map(parseFloat);
        let label = values[4]?.trim();  // Extract label (species name)

        if (features.length === 4 && features.every(v => !isNaN(v))) {
            data.push(features);
            labels.push(label);
        }
    }

    // Convert labels to numerical values: {Setosa: 1, Versicolor: 2, Virginica: 3}
    const labelMapping = { "setosa": 1, "versicolor": 2, "virginica": 3 };
    const numericLabels = labels.map(name => labelMapping[name.toLowerCase()] || 0);

    return { features: tf.tensor2d(data), labels: numericLabels };
}

// 🎯 **Define encoder**
function createEncoder() {
    const encoder = tf.sequential();
    encoder.add(tf.layers.dense({ units: 8, activation: 'relu', inputShape: [4] }));
    encoder.add(tf.layers.dense({ units: 3, activation: 'linear' })); // Latent representation
    return encoder;
}

// 🎯 **Define autoencoder with encoder passed in**
function createAutoencoder(encoder) {
    const autoencoder = tf.sequential();
    autoencoder.add(encoder); // Use encoder inside autoencoder
    autoencoder.add(tf.layers.dense({ units: 8, activation: 'relu' }));
    autoencoder.add(tf.layers.dense({ units: 4, activation: 'linear' }));

    autoencoder.compile({ optimizer: 'adam', loss: tf.losses.meanSquaredError });
    return autoencoder;
}

// 🎯 **Train model and store 3D latent representation with labels & scaling**
async function trainModel(trainXs, testXs, testLabels, autoencoder, encoder, epochs = 50) {
    let scenes = [];

    for (let i = 0; i < epochs; i++) {
        await autoencoder.fit(trainXs, trainXs, { epochs: 1 });

        // Extract 3D latent representation using updated encoder
        let latentSpacePredictions = encoder.predict(testXs);
        let predictionsArray = await latentSpacePredictions.array();

        // Apply Min-Max Scaling (scale between 0 and 10)
        let scaledPredictions = minMaxScale(predictionsArray, 0, 10);

        // Round all numbers to 3 decimal places & add labels
        let labeledScene = scaledPredictions.map((point, index) => 
            [...point.map(num => roundTo(num, 3)), testLabels[index]]);

        console.log(`Epoch ${i + 1} - Latent Representations with Labels:`, labeledScene.slice(0, dis));
        scenes.push(labeledScene);
    }

    return scenes;
}

// 🎯 **Min-Max Scaling Function**
function minMaxScale(data, minVal, maxVal) {
    let flattened = data.flat();
    let dataMin = Math.min(...flattened);
    let dataMax = Math.max(...flattened);

    return data.map(point =>
        point.map(value => ((value - dataMin) / (dataMax - dataMin)) * (maxVal - minVal) + minVal)
    );
}

// 🎯 **Rounding Function (rounds to 3 decimal places)**
function roundTo(value, decimals) {
    return Number(value.toFixed(decimals));
}

// 🎯 **Main Function (Training & Scene Preparation)**
async function main() {
    dis = 30;
    const { features, labels } = await loadIrisDataset();

    // **Select 10 samples per class (total: 30 test samples)**
    const setosa_indices = [...Array(10).keys()];          // Rows 0-9
    const versicolor_indices = [...Array(10).keys()].map(i => i + 50); // Rows 50-59
    const virginica_indices = [...Array(10).keys()].map(i => i + 100); // Rows 100-109
    const test_indices = [...setosa_indices, ...versicolor_indices, ...virginica_indices];
    const train_indices = [...Array(150).keys()].filter(i => !test_indices.includes(i));

    const trainXs = tf.gather(features, train_indices);
    const testXs = tf.gather(features, test_indices);

    const trainLabels = train_indices.map(i => labels[i]);
    const testLabels = test_indices.map(i => labels[i]);

    const encoder = createEncoder();
    const autoencoder = createAutoencoder(encoder);

    console.log("Training Autoencoder and Generating Scenes...");
    const rawScenes = await trainModel(trainXs, testXs, testLabels, autoencoder, encoder, 50);

    // 🎯 Generate 2700 smoothed frames
    return smoothFrames(rawScenes);
}

// 🎯 **VR Rendering Setup**
export const init = async model => {
    let points = [];
    let sceneFrames = await main();
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

// 🎯 **Smooth Frame Interpolation Function**
function smoothFrames(scenes) {
    let smoothedScenes = [];

    for (let i = 0; i < scenes.length - 1; i++) {
        let currentScene = scenes[i];
        let nextScene = scenes[i + 1];

        let delta = nextScene.map((point, index) => {
            return [
                (point[0] - currentScene[index][0]) / 54,
                (point[1] - currentScene[index][1]) / 54,
                (point[2] - currentScene[index][2]) / 54,
                point[3]
            ];
        });

        for (let j = 0; j < 54; j++) {
            let interpolatedFrame = currentScene.map((point, index) => {
                return [
                    point[0] + delta[index][0] * j,
                    point[1] + delta[index][1] * j,
                    point[2] + delta[index][2] * j,
                    point[3]
                ];
            });
            smoothedScenes.push(interpolatedFrame);
        }
    }
    return smoothedScenes;
}