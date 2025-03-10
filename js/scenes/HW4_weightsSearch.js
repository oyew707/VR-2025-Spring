const tf = require('@tensorflow/tfjs');

// 🎯 **Hyperparameters to Test**
const activations = ["relu", "sigmoid", "tanh"];
const lossFunctions = ['meanSquaredError', 'meanAbsoluteError'];
const optimizers = ["adam", "rmsprop", "sgd"];
const learningRates = {
    relu: [0.01, 0.05, 0.1],    
    sigmoid: [0.001, 0.007, 0.01], 
    tanh: [0.05, 0.065, 0.07] 
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
    encoder.add(tf.layers.dense({ units: 3, activation: activation }));
    return encoder;
}

// 🎯 **Define autoencoder**
function createAutoencoder(encoder, activation, loss, lr, optimizerType) {
    const autoencoder = tf.sequential();
    autoencoder.add(encoder);
    autoencoder.add(tf.layers.dense({ units: 8, activation: activation }));
    autoencoder.add(tf.layers.dense({ units: 4, activation: 'linear' }));

    let optimizer;
    if (optimizerType === "adam") optimizer = tf.train.adam(lr);
    else if (optimizerType === "rmsprop") optimizer = tf.train.rmsprop(lr);
    else if (optimizerType === "sgd") optimizer = tf.train.sgd(lr);

    autoencoder.compile({ optimizer: optimizer, loss: loss });
    return autoencoder;
}

// 🎯 **Train model & return final latent space representation**
async function trainAndEvaluate(trainXs, testXs, testLabels, activation, loss, lr, optimizerType) {
    let totalSpreadScore = 0;
    const runs = 3; // **Run each experiment 3 times for stability**

    for (let i = 0; i < runs; i++) {
        const encoder = createEncoder(activation);
        const autoencoder = createAutoencoder(encoder, activation, loss, lr, optimizerType);

        for (let epoch = 1; epoch <= 100; epoch++) {
            await autoencoder.fit(trainXs, trainXs, { epochs: 1, verbose: 0 });
        
            if (epoch % 40 === 0) {
                console.log(`Training... Epoch ${epoch}/100 | Activation: ${activation} | Optimizer: ${optimizerType} | Loss: ${loss} | LR: ${lr}`);
            }
        }
        

        const latentSpacePredictions = encoder.predict(testXs);
        const latentArray = await latentSpacePredictions.array();

        // 🎯 **Simple Variance-Based Evaluation**
        function clusterSpreadScore(data) {
            let means = [0, 0, 0];
            let count = data.length;

            for (let i = 0; i < count; i++) {
                means[0] += data[i][0];
                means[1] += data[i][1];
                means[2] += data[i][2];
            }
            means = means.map(sum => sum / count);

            let variance = [0, 0, 0];
            for (let i = 0; i < count; i++) {
                variance[0] += Math.pow(data[i][0] - means[0], 2);
                variance[1] += Math.pow(data[i][1] - means[1], 2);
                variance[2] += Math.pow(data[i][2] - means[2], 2);
            }
            variance = variance.map(sum => sum / count);

            return variance.reduce((a, b) => a + b, 0);
        }

        totalSpreadScore += clusterSpreadScore(latentArray);
    }

    return { loss, lr, optimizerType, spreadScore: totalSpreadScore / runs };  
}

// 🎯 **Main Function (Find Optimal for Each Activation)**
async function findOptimalConfigs() {
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

    let bestConfigs = {};

    for (let activation of activations) {
        let bestConfig = null;
        let bestScore = -Infinity;

        for (let loss of lossFunctions) {
            for (let optimizerType of optimizers) {
                for (let lr of learningRates[activation]) {  
                    const { spreadScore } = await trainAndEvaluate(trainXs, testXs, testLabels, activation, loss, lr, optimizerType);

                    if (spreadScore > bestScore) {
                        bestScore = spreadScore;
                        bestConfig = { activation, loss, lr, optimizerType, spreadScore };
                    }
                }
            }
        }

        bestConfigs[activation] = bestConfig;
    }

    // 🎯 **Print Optimal Configurations in Terminal**
    console.log("\n🔹 Optimal Configurations:\n");
    for (let activation in bestConfigs) {
        let config = bestConfigs[activation];
        console.log(`✅ Activation: ${config.activation} | Loss: ${config.loss} | Optimizer: ${config.optimizerType} | LR: ${config.lr} | Spread Score: ${config.spreadScore.toFixed(4)}`);
    }
}

findOptimalConfigs();