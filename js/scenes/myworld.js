import * as cg from "../render/core/cg.js";
import { buttonState } from "../render/core/controllerInput.js";
import { lcb } from '../handle_scenes.js'; // IMPORT LEFT CONTROLLER BEAM
import * as global from "../global.js";
import { quat } from "../render/math/gl-matrix.js";
import { G2 } from "../util/g2.js";
import { Gltf2Node } from "../render/nodes/gltf2.js";

let swan = new Gltf2Node({ url: 'media/gltf/world2/black_swan/scene.gltf', txtr: 4 });
let gold_gun  = new Gltf2Node({ url: 'media/gltf/world2/james_bond_golden_gun/scene.gltf', txtr: 3 });

export const init = async model => {
    // 
    // let g2A = new G2();
    // model.txtrSrc(1, g2A.getCanvas());
    // let objA = model.add('square').txtr(1);

    swan.translation = [0, 0, -0.5];
    swan.scale = [0.8,0.8,0.8];

    gold_gun.translation = [1, 0, -0.5];
    // gold_gun.rotation = [1, 0, 0, 1];
    gold_gun.scale = [0.03,0.03,0.03];

    global.gltfRoot.addNode(gold_gun);
    global.gltfRoot.addNode(swan);

    let g2A = new G2();
    model.txtrSrc(1, g2A.getCanvas());
    let objA = model.add('square').txtr(1);

    let redCount = 3;
    let greenCount = 3;

    // Function to create a balloon mesh
    function createBalloonMesh(color) {
        return clay.combineMeshes([
            ['sphere', cg.mScale(0.1, 0.12, 0.1), color], // Scaled Balloon Body
            ['sphere', cg.mMultiply(cg.mTranslate(0, -0.11, 0), cg.mScale(0.02, 0.02, 0.02)), [color[0]*0.8, color[1]*0.8, color[2]*0.8]], // Scaled Knot
            ['tubeY', cg.mMultiply(cg.mTranslate(0, -0.25, 0), cg.mScale(0.002, 0.2, 0.002)), [0.9, 0.9, 0.9]]  // Scaled String
        ]);
    }

    // Define red and yellow balloon meshes
    clay.defineMesh('Balloon', createBalloonMesh([1, 0.2, 0.2]));  // Default is a red balloon
    clay.defineMesh('redBalloon', createBalloonMesh([1, 0.2, 0.2]));
    clay.defineMesh('yellowBalloon', createBalloonMesh([1, 1, 0]));

    let balloons = [];

    // Function to add a balloon
    function addBalloon(type, x, z) {
        let balloon = model.add(type);
        balloon.move(x, 0, z);
        balloon.delay = Math.random() * 2; // Random delay for natural movement
        balloon.isAnimating = true; // Add a flag to control animation
        balloon.isPopping = false;  // Add a flag to control popping
        balloon.popProgress = 0;
        balloon.originalScale = 0.5; // Store the original scale
        balloon.scale(balloon.originalScale);
        return balloon;
    }

    // Add balloons
    for (let i = 0; i < 3; i++) {
        balloons.push(addBalloon('redBalloon', Math.random() * 6 - 3, Math.random() * 6 - 3));  // Random position
        balloons.push(addBalloon('yellowBalloon', Math.random() * 6 - 3, Math.random() * 6 - 3));  // Random position
    }


    const ballRadius = 0.1;  // Define the balloon radius for collision detection

    model.animate(() => {
        let isPressed = inputEvents.isPressed('right') ?? false;
        // console.log("ispressed: " + isPressed.toString());
        let handpos = isPressed ? inputEvents.pos('right') : [0,0,0];
        // console.log("handpos: " + handpos.toString());
        
        g2A.update();
        objA.identity().move(handpos).scale(.07);


        balloons.forEach((balloon, index) => {
            if (balloon.isAnimating){
                let x = balloon.getMatrix()[12];
                let y = balloon.getMatrix()[13];
                let z = balloon.getMatrix()[14];

                // Check for hit and press
                let ballPosition = [x, y, z];

                let pointOnBeam = lcb.projectOntoBeam(ballPosition);
                let isHit = cg.distance(pointOnBeam, ballPosition) < ballRadius;
                let isPressed = buttonState.left[0].pressed;

                if (isHit && isPressed) {
                    // Stop animating the balloon
                    balloon.isPopping = true;
                    balloon.popProgress = 0;
                    if (index % 2 == 0) {
                        redCount--;
                    }else {
                        greenCount--;
                    }
                }
                
                
                // Display balloon
                if (balloon.isPopping) {
                    // Pop the balloon
                    balloon.popProgress += 0.1; // Adjust this value to control popping speed
                    let scale;
                    if (balloon.popProgress < 0.5) {
                       // Expand slightly
                       scale = balloon.originalScale * (2 + balloon.popProgress * 0.2);
                    } else {
                       // Shrink rapidly
                       scale = balloon.originalScale * (2 - (balloon.popProgress - 0.5) * 2);
                    }
                    balloon.scale(scale);
        
                    if (balloon.popProgress > 1) {
                       balloon.isAnimating = false;
                       balloon.isPopping = false;
                    }
                 } else {
                    y = Math.min(2, model.time * 0.1 + Math.sin(model.time + balloon.delay) * 0.1);
                    
                    balloon.identity().move(x, y, z).turnY(model.time / 2);
                }
            }
           
        });
     });

     // ANIMATED DRAWING OF A WIGGLY LINE
 
    g2A.render = function() {
        this.setColor([.5,.5,1,.5]);
        this.fillRect(-1,-1,2,2);
  
        this.setColor('yellow');
        this.textHeight(.05);
 
        let textLines = [
             "Hello",
             "Try to pop the balloons",
             "Aim controller beam at ",
             "balloon and press it",
             `Red Balls: ${redCount}`,
             `Yellow Balls: ${greenCount}`
         ];
         
         let formattedText = textLines.join("\n");
        this.text(formattedText, 0, .9, 'center');
  
 
     }
     g2A.addWidget(objA, 'button',  .7, -.8, '#ff8080', 'reset', () => { 
         // Reset the drawing pad
    });
}
