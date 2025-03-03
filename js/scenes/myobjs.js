import * as global from "../global.js";
import { quat } from "../render/math/gl-matrix.js";
import { Gltf2Node } from "../render/nodes/gltf2.js";
import { buttonState } from "../render/core/controllerInput.js";


let cupcakes = new Gltf2Node({ url: 'media/gltf/world1/cupcakes/scene.gltf', txtr: 4 });
let invincible    = new Gltf2Node({ url: 'media/gltf/world1/invincible/scene.gltf', txtr: 3 });
let cat  = new Gltf2Node({ url: 'media/gltf/world1/cat/scene.gltf' , alpha: .5, txtr: 2 });

export const init = async model => {

    cupcakes.translation = [-1, 1.6, -0.5];
    cupcakes.scale = [0.05,0.05,0.05];
    

    invincible.translation = [1, 0, -0.5];
    invincible.rotation = [1, 0, 0, 1];
    invincible.scale = [0.03,0.03,0.03];
    

    cat.translation = [0, 0, -0.5];
    cat.scale = [0.8,0.8,0.8];
    cat.visible = true;

    
    global.gltfRoot.addNode(cat);
    global.gltfRoot.addNode(cupcakes);
    global.gltfRoot.addNode(invincible);

    model.animate(() => {
        if (buttonState['right'].pressed) {
            cupcakes.visible = false;
        }
        if (buttonState['left'].pressed) {
            invincible.visible = false;
        }
    });
 }
