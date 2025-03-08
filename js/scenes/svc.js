import * as cg from "../render/core/cg.js";
import { G2 } from "../util/g2.js";
import { lcb, rcb } from '../handle_scenes.js';
import { forEach } from "../third-party/gl-matrix/src/gl-matrix/vec3.js";

const N = 8000;
const svc_url = `${window.location.protocol}//${window.location.hostname}:3000`;
let isProcessing = false;

// Trains the SVC model with the POST parameters.
async function updateSVC(params) {
    let result  = {'decision_boundary': [], 'support_vectors': [], 'accuracy': 0, 'reached_max_iter': false, 'converged': false};;
    if (isProcessing) {
        return result;
    }
    try {
        const response = await fetch(`${svc_url}/train_svc`, {
            method: 'POST',
            // mode: 'no-cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        });
        if (response.ok) {
            result = await response.json();
            //  {
            //     'decision_boundary': set_diff,
            //     'support_vectors': svc_model.support_vectors_.tolist(),
            //     'accuracy': svc_model.score(X, y),
            //     'reached_max_iter': reached_max_iter
            // }
            console.log("Model Converged:" + (!result).toString());
            isProcessing = false;
        } else if (response.status == 503){
            isProcessing = true;
            console.log("Model is still processing");
        }
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        isProcessing = false;
    } finally {
        return result;
    }
    
}

// Returns the iris dataset in 3D space for visualization from SVC server
async function getIrisData() {
    const response = await fetch(`${svc_url}/get_iris_data`, {
        method: 'GET',
        // mode: 'no-cors'
    });
    const result = await response.json();

    return result;
}

// Returns the mesh dataset in 3D space for visualization from SVC server
async function getMeshData() {
    const response = await fetch(`${svc_url}/get_mesh_data`, {
        method: 'GET',
        // mode: 'no-cors'
    });
    const result = await response.json();

    return result;
}

// Resets the SVC model
async function resetModel(params) {
    const response = await fetch(`${svc_url}/reset`, {
        method: 'POST',
        // mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });
    const result = await response.json();

    return result;
}

function getColor(classLabel) {
    if (classLabel  == null){
        return [0.5, 0.5, 0.5, 0.2]; // grey
    }
    let color = classLabel == 0 ? [1,0,0, 0.2] : (classLabel == 1 ? [0,1,0, 0.2] : [0,0,1, 0.2]); 
    return color;
}

export const init = async model => {
    let params = { 'max_iter': 5, 'C': 1.0, 'tol': 0.001, 'kernel': 'linear', 'degree': 3 };

    // Widget to control the SVC model
    let g2Params = new G2();
    let paramsObj = model.add('square').setTxtr(g2Params.getCanvas());

    // Widgets to display extra information
    let g2Info = new G2();
    let infoObj = model.add('square').setTxtr(g2Info.getCanvas());

    // Add sliders for numerical parameters
    g2Params.addWidget(paramsObj, 'slider', -0.6, 0.8, '#80ffff', 'C', value => params.C = max(0, value * 10));
    g2Params.addWidget(paramsObj, 'slider', -0.6, 0.6, '#80ffff', 'Tolerance', value => params.tol = value / 100);
    g2Params.addWidget(paramsObj, 'slider', -0.6, 0.4, '#80ffff', 'Max Iter', value => params.max_iter = Math.round(value * 100));

    // Add buttons for categorical parameters
    g2Params.addWidget(paramsObj, 'button', -0.6, 0.2, '#ff8080', 'Linear Kernel', () => params.kernel = 'linear');
    g2Params.addWidget(paramsObj, 'button', 0.0, 0.2, '#ff8080', 'Poly Kernel', () => params.kernel = 'poly');
    g2Params.addWidget(paramsObj, 'button', 0.6, 0.2, '#ff8080', 'RBF Kernel', () => params.kernel = 'rbf');


    model.txtrSrc(2, 'media/textures/disk.jpg');
    let particles = model.add('particles').info(N).txtr(2).flag('uTransparentTexture').scale(2);

    // Set the initial decision boundary
    await resetModel(params);
    // const initdata = await updateSVC(params);
    let grid = await getMeshData();
    let accuracy = 0;
    let reachedMaxIter = 0;
    let converged = 0;

    console.log(grid);
    let diff = [];

    let data = new Array(grid.length);
    grid.forEach((point, i, _) => {
        data[point['index']] = {
            p: [point['x'], point['y'], point['z']],
            s: .01,
            c: getColor(point['pred']),
        }
    });
    console.log("Init data", data.length, data[0]);


    particles.setParticles(data);

    // Get the iris data
    const irisData = await getIrisData({});

    let iris = [];
    for (let i = 0; i < irisData.length; i++) {
        let position = [irisData[i]['x'], irisData[i]['y'], irisData[i]['z']];
        let datapoint = model.add('sphere')
                        .identity()
                        .scale(0.001)
                        .color(getColor(irisData[i]['target'])) 
                        .move(...position);
        iris.push(datapoint); 
    }

    model.move(0,1.5,0).animate(() => {
        // Display widgets
        g2Params.update();
        paramsObj.identity().move(-0.5, 0, 0).scale(0.5);

        // Display info
        g2Info.update();
        infoObj.identity().move(-1, 0, 0).scale(0.5);

        if (diff.length == 0) {
            // if there is no diff run the next few epochs
            updateSVC(params).then((result) => {
                // console.log("Animate results", JSON.stringify(result));
                console.log("Params", JSON.stringify(params), "Result", result["accuracy"].toString());
                diff = result["decision_boundary"];
                accuracy = result["accuracy"];
                reachedMaxIter = result["reached_max_iter"];
                converged = result["converged"];
            });
        } else {
            // We want to change/keep 10 particles per frame, i.e. takes roughly 10s to update all particles
            for (let i = 0; i < 10 && diff.length > 0; i++) {

                data[diff[0]['index']].c = getColor(diff[0]['pred']);
                diff.shift();
            }
            particles.setParticles(data);
        }
    });

    g2Info.render = function() {
        this.setColor('white');
        this.fillRect(-1,-1,2,2);
        
        // Display accuracy and status
        this.setColor('black');
        this.textHeight(0.05);
        this.text(`Accuracy: ${accuracy.toFixed(3)}`, 0, 0.8, 'center');
        this.text(`Converged: ${converged ? "Yes" : "No"}`, 0, 0.7, 'center');
        this.text(`Max Iter Reached: ${reachedMaxIter ? "Yes" : "No"}`, 0, 0.6, 'center');
    };

}