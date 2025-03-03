import { buttonState } from "../render/core/controllerInput.js";
import { lcb, rcb } from '../handle_scenes.js'; // IMPORT LEFT CONTROLLER BEAM
import { G2 } from "../util/g2.js";
import { Gltf2Node } from "../render/nodes/gltf2.js";
import * as cg from "../render/core/cg.js";

export const init = async model => {
    clay.defineMesh('simpleGun', clay.combineMeshes([
        // Gun barrel (shortened)
        ['tubeZ', cg.mMultiply(cg.mScale(0.005, 0.005, 0.05), cg.mTranslate(0, 0.005, 0.02)), [0.2, 0.2, 0.2]],

        // Gun body
        ['cube', cg.mMultiply(cg.mScale(0.01, 0.015, 0.02), cg.mTranslate(0, 0, -0.02)), [0.3, 0.3, 0.3]],

        // Gun handle (shortened and repositioned)
        ['cube', cg.mMultiply(cg.mScale(0.0075, 0.02, 0.0075), cg.mTranslate(0, -0.06, -0.03)), [0.4, 0.2, 0.1]],

        // Gun trigger
        ['cube', cg.mMultiply(cg.mScale(0.003, 0.01, 0.005), cg.mTranslate(0, -0.02, -0.025)), [0.1, 0.1, 0.1]],
        //   // Gun sight
        //   ['pyramid', cg.mMultiply(cg.mScale(0.05, 0.05, 0.05), cg.mTranslate(0, 0.35, 0.2)), [1, 0, 0]]
    ]));

    let simpleGun = model.add('simpleGun');

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
    clay.defineMesh('bullet', ['sphere', cg.mScale(0.01, 0.01, 0.01), [0, 0, 0]]);

    let bullets = [];
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

    // Function to add a bullet
    function addBullet(position, direction) {
        let bullet = model.add('sphere');
        bullet.move(...position);
        bullet.direction = direction;
        bullet.speed = 0.1; // Adjust as needed
        bullet.life = 100; // Frames to live
        return bullet;
    }


    // Add balloons
    for (let i = 0; i < 3; i++) {
        balloons.push(addBalloon('redBalloon', Math.random() * 6 - 3, Math.random() * 6 - 3));  // Random position
        balloons.push(addBalloon('yellowBalloon', Math.random() * 6 - 3, Math.random() * 6 - 3));  // Random position
    }

    const ballRadius = 0.1;  // Define the balloon radius for collision detection

    model.animate(() => {
        let isLeftPressed = inputEvents.isAltPressed('left') ?? false;
        let isRightPressed = inputEvents.isAltPressed('right') ?? false;

        if (isLeftPressed || isRightPressed) {
            let hand = isLeftPressed ? 'left' : 'right';
            let handPos = inputEvents.pos(hand);
            let beam = isLeftPressed ? lcb : rcb;

            // Get the beam matrix
            let beamMatrix = beam.beamMatrix();
            
            // Extract beam direction from the matrix
            let beamDirection = cg.normalize([
                beamMatrix[8],  // Third column, first row
                beamMatrix[9],  // Third column, second row
                beamMatrix[10]  // Third column, third row
            ]);
            
            // Calculate rotation to align gun with beam
            // let rotationMatrix = cg.mAimZ(beamDirection);
            
            // Calculate rotation angles from beam direction
            let yaw = Math.atan2(beamDirection[0], beamDirection[2]);
            let pitch = Math.asin(-beamDirection[1]);

            // Position and rotate the gun
            simpleGun.identity(); // Reset transformations
            simpleGun.move(...handPos); // Translate to hand position
            simpleGun.turnY(yaw);   // Rotate around Y-axis (yaw)
            simpleGun.turnX(pitch); // Rotate around X-axis (pitch)
            // simpleGun.turnZ(Math.PI); // Rotate around X-axis (pitch)
            simpleGun.move(0, -0.02, 0.05); // Adjust position relative to hand


            // SHOOTING
            if (inputEvents.isPressed(hand)) {
                let gunPosition = cg.mTransform(simpleGun.getMatrix(), [0, 0, 0]); // Get the world position of the gun
                let bullet = addBullet(gunPosition, beamDirection);
                bullets.push(bullet);
            }
        } else {
            simpleGun.identity().scale(0);
            // Hide the gun if not pressed
        }

        // Animate and update bullets
        for (let i = 0; i < bullets.length; i++) {
            let bullet = bullets[i];
            let bulletPos = bullet.getMatrix().slice(12, 15); // Get current position

            // Move the bullet along the beam direction
            let newBulletPos = cg.add(bulletPos, cg.scale(bullet.direction, bullet.speed));
            bullet.move(...newBulletPos);
            bullet.life--;

            if (bullet.life <= 0) {
                bullet.scale(0); // "Destroy" the bullet
                bullets.splice(i, 1); // Remove from the array
                i--; // Adjust the index
            }
        }

        balloons.forEach((balloon, index) => {
            if (balloon.isAnimating){
                let x = balloon.getMatrix()[12];
                let y = balloon.getMatrix()[13];
                let z = balloon.getMatrix()[14];


            }
            if (balloon.isPopping){
                
            } else {
                y = Math.min(2, model.time * 0.1 + Math.sin(model.time + balloon.delay) * 0.1);
                    
                balloon.identity().move(x, y, z).turnY(model.time / 2);
            }
        });
    });
}

