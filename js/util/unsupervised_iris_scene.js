const tf = require('@tensorflow/tfjs');
const fs = require('fs'); // To save & load data

// 🎯 **Optimal Hyperparameters for Each Activation**
const bestParams = {
    relu: { optimizer: "adam", loss: "meanAbsoluteError", lr: 0.08 },
    sigmoid: { optimizer: "adam", loss: "meanSquaredError", lr: 0.7 },
    tanh: { optimizer: "rmsprop", loss: "meanAbsoluteError", lr: 0.065 }
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

    let optimizerInstance;
    if (optimizer === "adam") optimizerInstance = tf.train.adam(lr);
    else if (optimizer === "rmsprop") optimizerInstance = tf.train.rmsprop(lr);
    else optimizerInstance = tf.train.sgd(lr); // Default fallback

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

// 🎯 **Min-Max Scaling Function (Now Applied Once at the End)**
function minMaxScale(scenes, newMin = 0, newMax = 3) {
    let allPoints = scenes.flat(); // Flatten all frames into one array

    // Find min & max for each dimension (X, Y, Z)
    let mins = [
        Math.min(...allPoints.map(p => p[0])),
        Math.min(...allPoints.map(p => p[1])),
        Math.min(...allPoints.map(p => p[2]))
    ];
    let maxs = [
        Math.max(...allPoints.map(p => p[0])),
        Math.max(...allPoints.map(p => p[1])),
        Math.max(...allPoints.map(p => p[2]))
    ];

    return scenes.map(frame =>
        frame.map(point => [
            newMin + ((point[0] - mins[0]) / (maxs[0] - mins[0])) * (newMax - newMin),
            newMin + ((point[1] - mins[1]) / (maxs[1] - mins[1])) * (newMax - newMin),
            newMin + ((point[2] - mins[2]) / (maxs[2] - mins[2])) * (newMax - newMin),
            point[3] // ✅ Labels stay intact
        ])
    );
}

// 🎯 **Final Rounding Function**
function roundScenes(scenes) {
    return scenes.map(frame =>
        frame.map(point =>
            [roundTo(point[0], 5), roundTo(point[1], 5), roundTo(point[2], 5), point[3]] // ✅ Labels stay intact
        )
    );
}

// 🎯 **Rounding Helper Function**
function roundTo(value, decimals) {
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

        console.log(`Training model with activation: ${activation} | Optimizer: ${optimizer} | Loss: ${loss} | LR: ${lr}`);

        const encoder = createEncoder(activation);
        const autoencoder = createAutoencoder(encoder, activation, optimizer, loss, lr);

        const rawScenes = await trainModel(trainXs, testXs, testLabels, autoencoder, encoder, 100);

        // 🎯 **Apply Min-Max Scaling (Now Done Only Once)**
        const scaledScenes = minMaxScale(rawScenes);

        // 🎯 **Apply Final Rounding Before Saving**
        const finalScenes = roundScenes(scaledScenes);
        
        fs.writeFileSync(filenames[i], JSON.stringify(finalScenes, null, 2));

        console.log(`Final Min-Max Scaled Predictions saved to ${filenames[i]}`);
    }
}

main();