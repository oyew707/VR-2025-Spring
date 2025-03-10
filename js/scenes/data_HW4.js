const tf = require('@tensorflow/tfjs');
const fs = require('fs'); // To save & load data

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
function createEncoder() {
    const encoder = tf.sequential();
    encoder.add(tf.layers.dense({ units: 8, activation: 'relu', inputShape: [4] }));
    encoder.add(tf.layers.dense({ units: 3, activation: 'linear' }));
    return encoder;
}

// 🎯 **Define autoencoder**
function createAutoencoder(encoder) {
    const autoencoder = tf.sequential();
    autoencoder.add(encoder);
    autoencoder.add(tf.layers.dense({ units: 8, activation: 'relu' }));
    autoencoder.add(tf.layers.dense({ units: 4, activation: 'linear' }));

    autoencoder.compile({ optimizer: 'adam', loss: tf.losses.meanSquaredError });
    return autoencoder;
}

// 🎯 **Train model and store predictions**
async function trainModel(trainXs, testXs, testLabels, autoencoder, encoder, epochs = 50) {
    let scenes = [];

    for (let i = 0; i < epochs; i++) {
        await autoencoder.fit(trainXs, trainXs, { epochs: 1 });

        let latentSpacePredictions = encoder.predict(testXs);
        let predictionsArray = await latentSpacePredictions.array();

        let scaledPredictions = minMaxScale(predictionsArray, 0, 10);

        let labeledScene = scaledPredictions.map((point, index) =>
            [...point, testLabels[index]] // No rounding here!
        );

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

// 🎯 **Smooth Frame Interpolation Function (Divides Each Scene into 54 Slices)**
function smoothFrames(scenes) {
    let smoothedScenes = [];

    for (let i = 0; i < scenes.length - 1; i++) {
        let currentScene = scenes[i];
        let nextScene = scenes[i + 1];

        for (let j = 0; j < 54; j++) {
            let interpolatedFrame = currentScene.map((point, index) => {
                return [
                    point[0] + ((nextScene[index][0] - point[0]) * (j / 54)),
                    point[1] + ((nextScene[index][1] - point[1]) * (j / 54)),
                    point[2] + ((nextScene[index][2] - point[2]) * (j / 54)),
                    point[3] // Label stays the same
                ];
            });
            smoothedScenes.push(interpolatedFrame);
        }
    }

    return smoothedScenes;
}

// 🎯 **Final Rounding Function (Only Rounds Before Saving)**
function roundScenes(scenes) {
    return scenes.map(frame =>
        frame.map(point =>
            [roundTo(point[0], 5), roundTo(point[1], 5), roundTo(point[2], 5), point[3]] // Labels stay the same
        )
    );
}

// 🎯 **Rounding Helper Function**
function roundTo(value, decimals) {
    return Number(value.toFixed(decimals));
}

// 🎯 **Main Function (Training & Saving Data)**
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

    const encoder = createEncoder();
    const autoencoder = createAutoencoder(encoder);

    console.log("Training Autoencoder and Generating Scenes...");
    const rawScenes = await trainModel(trainXs, testXs, testLabels, autoencoder, encoder, 50);

    // 🎯 **Apply Smoothing**
    const smoothedScenes = smoothFrames(rawScenes);

    // 🎯 **Apply Final Rounding Before Saving**
    const finalScenes = roundScenes(smoothedScenes);

    // 🎯 **Print the Last 5 Predictions**
    console.log("Last 5 Predictions (Smoothed & Rounded):");
    console.log(finalScenes.slice(-5)); // Get last 5 frames after smoothing

    // 🎯 **Save Smoothed & Rounded Predictions to JSON File**
    fs.writeFileSync("predictions.json", JSON.stringify(finalScenes, null, 2));
    console.log("Final Smoothed Predictions saved to predictions.json");
}

main();
