const tf = require('@tensorflow/tfjs');
const fs = require('fs'); // To save & load data

// 🎯 **Optimal Hyperparameters for Each Activation**
const bestParams = {
    relu: { optimizer: "adam", loss: "meanSquaredError", lr: 0.05 },
    sigmoid: { optimizer: "adam", loss: "meanSquaredError", lr: 0.01 },
    tanh: { optimizer: "rmsprop", loss: "meanSquaredError", lr: 0.009 }
};

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
        let label = values[4]?.trim();

        if (features.length === 4 && features.every(v => !isNaN(v))) {
            data.push(features);
            labels.push(label);
        }
    }

    const labelMapping = { "setosa": 1, "versicolor": 2, "virginica": 3 };
    const numericLabels = labels.map(name => labelMapping[name.toLowerCase()] || 0);

    return { features: tf.tensor2d(data), labels: numericLabels };
}

// 🎯 **Define encoder**
function createEncoder(activation) {
    const encoder = tf.sequential();
    encoder.add(tf.layers.dense({ units: 8, activation: activation, inputShape: [4] }));
    encoder.add(tf.layers.dense({ units: 3, activation: 'linear' })); // Ensure stable encoding
    return encoder;
}

// 🎯 **Define autoencoder**
function createAutoencoder(encoder, activation, optimizer, loss, lr) {
    const autoencoder = tf.sequential();
    autoencoder.add(encoder);
    autoencoder.add(tf.layers.dense({ units: 8, activation: activation })); // Hidden layer
    autoencoder.add(tf.layers.dense({ units: 4, activation: 'linear' })); // Output layer

    let optimizerInstance = tf.train.adam(lr);

    autoencoder.compile({ optimizer: optimizerInstance, loss: loss });
    return autoencoder;
}

// 🎯 **Train model and store predictions**
async function trainModel(trainXs, testXs, testLabels, autoencoder, encoder, epochs = 100) {
    let scenes = [];

    for (let i = 0; i < epochs; i++) {
        await autoencoder.fit(trainXs, trainXs, { epochs: 1 });

        let latentSpacePredictions = encoder.predict(testXs);
        let predictionsArray = await latentSpacePredictions.array();

        let labeledScene = predictionsArray.map((point, index) =>
            [...point, testLabels[index]] // ✅ Labels stay intact
        );

        scenes.push(labeledScene);
    }

    return scenes;
}

// 🎯 **Min-Max Scaling Function Per Class**
function minMaxScale(scenes, newMin = 0, newMax = 3) {
    let classData = { 1: [], 2: [], 3: [] };

    // 🟢 Step 1: Separate points by class
    scenes.flat().forEach(point => {
        if (point[3] !== undefined) {
            classData[point[3]].push(point);
        } else {
            console.warn("🚨 Found undefined label in minMaxScale():", point);
        }
    });

    let scaledScenes = [];

    // 🟢 Step 2: Compute per-class Min-Max scaling
    for (let label of [1, 2, 3]) {
        let points = classData[label];

        if (points.length === 0) {
            console.warn(`⚠️ No data found for label ${label} in minMaxScale`);
            continue;
        }

        // Find per-class min/max values for X, Y, Z
        let mins = [Infinity, Infinity, Infinity];
        let maxs = [-Infinity, -Infinity, -Infinity];

        for (let p of points) {
            for (let i = 0; i < 3; i++) {
                mins[i] = Math.min(mins[i], p[i]);
                maxs[i] = Math.max(maxs[i], p[i]);
            }
        }

        // 🚨 Log min/max for each class
        console.log(`📊 Min/Max for class ${label}:`, { mins, maxs });

        // 🚨 Check for zero variance cases and scale
        let scaledPoints = points.map(p => {
            let scaled = [];

            for (let i = 0; i < 3; i++) {
                let range = maxs[i] - mins[i];
                let scaledValue = (range === 0) ? newMin : newMin + ((p[i] - mins[i]) / range) * (newMax - newMin);
                scaled.push(scaledValue);
            }

            // 🚨 Log problematic points
            if (scaled.some(v => isNaN(v) || v === undefined)) {
                console.warn("🚨 NaN/undefined detected in minMaxScale output:", { p, scaled });
            }

            return [...scaled, p[3]]; // ✅ Labels stay intact
        });

        scaledScenes.push(scaledPoints);
    }

    return scaledScenes;
}

// 🎯 **Final Rounding Function**
function roundScenes(scenes) {
    return scenes.map(frame =>
        frame.map(point => {
            if (point.some(v => v === undefined || isNaN(v))) {
                console.error("🚨 Undefined or NaN detected in roundScenes:", point);
            }
            return [roundTo(point[0], 5), roundTo(point[1], 5), roundTo(point[2], 5), point[3]];
        })
    );
}

// 🎯 **Rounding Helper Function**
function roundTo(value, decimals) {
    if (value === undefined || isNaN(value)) {
        console.warn(`🚨 roundTo received invalid value: ${value}`);
        return 0; // Defaulting to 0 instead of crashing
    }
    return Number(value.toFixed(decimals));
}

// 🎯 **Main Function (Training & Saving Data for 3 Activations)**
async function main() {
    const { features, labels } = await loadIrisDataset();

    const setosa_indices = [...Array(10).keys()];
    const versicolor_indices = [...Array(10).keys()].map(i => i + 50);
    const virginica_indices = [...Array(10).keys()].map(i => i + 100);
    const test_indices = [...setosa_indices, ...versicolor_indices, ...virginica_indices];
    const train_indices = [...Array(150).keys()].filter(i => !test_indices.includes(i));

    const trainXs = tf.gather(features, train_indices);
    const testXs = tf.gather(features, test_indices);
    const trainLabels = train_indices.map(i => labels[i]);
    const testLabels = test_indices.map(i => labels[i]);

    // 🎯 **Train 3 Different Networks (ReLU, Tanh, Sigmoid)**
    const activations = ["relu", "tanh", "sigmoid"];
    const filenames = ["predictions_relu.json", "predictions_tanh.json", "predictions_sigmoid.json"];

    for (let i = 0; i < activations.length; i++) {
        const activation = activations[i];
        const { optimizer, loss, lr } = bestParams[activation];

        console.log(`Training with activation: ${activation} | LR: ${lr}`);

        const encoder = createEncoder(activation);
        const autoencoder = createAutoencoder(encoder, activation, optimizer, loss, lr);

        const rawScenes = await trainModel(trainXs, testXs, testLabels, autoencoder, encoder, 100);
        const scaledScenes = minMaxScale(rawScenes);
        const finalScenes = roundScenes(scaledScenes);
    }
}

main();
