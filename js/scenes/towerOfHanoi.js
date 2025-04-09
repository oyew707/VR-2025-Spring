import towerStack from '../util/towerStack.js';
import * as cg from "../render/core/cg.js"; 
import { buttonState, controllerMatrix } from "../render/core/controllerInput.js";
import { lcb, rcb } from '../handle_scenes.js'

function createCubeMatrix(discCenter, discRadius, thickness = 0.1) {
    // Translate the cube to the disc's center
    let translation = cg.mTranslate(discCenter[0], discCenter[1], discCenter[2]);

    // Scale the cube to wrap the disc
    let scale = cg.mScale(discRadius, discRadius, thickness);

    // Combine translation and scale
    return cg.mMultiply(translation, scale);
}

function findValidTower(discPosition, towers) {

    const maxDistance = 0.2; // Maximum allowed distance from the tower
    const xTolerance = 0.3; // Degree of freedom for the x-axis
    const baseY = 0.2;      // Default Y position for the base of the tower

    for (let i = 0; i < towers.length; i++) {
        const tower = towers[i];
        const towerX = tower.pos; // X position of the tower
        const towerZ = 0;         // Z position of the tower (static)

        // Calculate the distance between the disc and the tower
        const dx = Math.abs(discPosition[0] - towerX);
        const dz = Math.abs(discPosition[2] - towerZ);

        // Check if the disc is within the allowed distance
        if (dx <= maxDistance && dz <= maxDistance) {
            // Get the top disc of the tower's stack (if any)
            const topDisc = tower.stack.peek();

            // Determine the Y position to check against
            const targetY = topDisc ? topDisc.position[1] : baseY;

            // Check if the disc can be placed on top of the stack or base
            if (targetY+xTolerance >= discPosition[1] >= targetY) {
                return i; // Return the index of the valid tower
            }
        }
    }

    return null; // No valid tower found
}


export const init = async model => {

    model.txtrSrc(1, '../media/textures/wood.jpg');
 
    let board = model.add();
    let base = board.add('cube').txtr(1).move(0,0,0).scale(2.5,0.1,1);
    let towerPos = [-1.5, 0, 1.5];
    let towers = [];
    towerPos.forEach((pos, i) => {
        let tower = board.add('tubeY').txtr(1).move(pos, 1, 0).scale(0.1, 1, 0.1);
        let tStack = new towerStack();
        towers.push({
            object: tower,
            stack: tStack,
            pos: pos
        });
    });

    let colors = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
    let discs = [];

            
    // Constants for proper disc appearance
    const baseY = 0.2;       // Starting Y position just above the base
    const discHeight = 0.2;  // Increased height for better proportions
    const minWidth = 0.4;     // Width of smallest disc
    const widthIncrement = 0.1; // Width difference between disc sizes

    const createDiscs = (numDiscs) => {
        
        for (let i = 0; i < numDiscs; i++) {
            // Calculate disc index from bottom to top (larger discs at bottom)
            const discIndex = numDiscs - 1 - i;
            
            // Calculate size (larger for bottom discs, smaller for top)
            const discWidth = minWidth + (discIndex * widthIncrement);
            
            // Position each disc directly on top of the previous one
            const yPos = baseY + (i * discHeight);
            
            let disc = model.add('donut')
                .color(colors[discIndex % colors.length])
                .move(towers[0].pos, yPos, 0)
                .turnX(Math.PI/2)
                .scale(discWidth, discWidth, discHeight);
            let discObject = {
                color: colors[discIndex % colors.length],
                value: discWidth,
                object: disc,
                position: [towers[0].pos, yPos, 0],
                valid_position: [towers[0].pos, yPos, 0],
                tower: 0,                
            };

            towers[0].stack.push(discObject);
            discs.push(discObject);
        }
    };

    createDiscs(5); // Start with 3 discs
    let selectedDisc = null;
    let lastControllerPosition = null;
    let canMove = false;

    let controllerPos = controllerMatrix.left ? controllerMatrix.left.slice(12,15) : controllerMatrix.right ? controllerMatrix.right.slice(12,15) : undefined;

    model.move(0,1.5,0).scale(.1).animate(() => {
        board.identity();

        if (!controllerMatrix.left || !controllerMatrix.right) {
            return; // Skip frame if controller tracking is lost
        }
        
        // input
        let leftPressed   = buttonState.left[0].pressed;
        let rightPressed  = buttonState.right[0].pressed;
        let leftReleased = !buttonState.left[0].pressed;
        let rightReleased = !buttonState.right[0].pressed;

        let lastControllerPosition = leftPressed ? controllerMatrix.left.slice(12,15) : rightPressed ? controllerMatrix.right.slice(12,15) : undefined;

        discs.forEach(disc => {
            if (leftPressed || rightPressed) {
                console.log("Left Pressed:", leftPressed);
                // Create the transformation matrix for the disc
                let discMatrix = createCubeMatrix(disc.position, disc.value);
                console.log("Disc Matrix:", discMatrix);
                
                // Check for intersection with the controller ray
                let isHit = leftPressed ? lcb.hitRect(discMatrix) : rightPressed ? rcb.hitRect(discMatrix) : false;

                if (isHit) {
                    console.log('Its hit');
                    canMove = towers[disc.tower].stack.peek().value == disc.value;

                    // Calculate the change in controller position
                    let delta = cg.subtract(controllerPos, lastControllerPosition);
                    console.log("Delta:", delta);
        
                    // Compute the new position for the selected disc
                    let newPosition = cg.add(disc.position, delta);

                    // Create the transformation matrix for the selected disc at the new position
                    let newDiscMatrix = createCubeMatrix(newPosition, disc.value);

                    // Check for collisions with other discs
                    let noCollision = discs.some(otherDisc => {
                        if (otherDisc === disc) return true; // Skip the selected disc itself
                        let otherDiscMatrix = createCubeMatrix(otherDisc.position, otherDisc.value);
                        return !cg.isBoxIntersectBox(newDiscMatrix, otherDiscMatrix);
                    });
                    if (noCollision) {
                        disc.position = newPosition;

                        // Update the disc's transformation
                        console.log("Moved disc to:", disc.position);

                    }
                } else {
                    console.log('Not hit');
                    canMove = false;
                }
            }
            disc.object
                .identity()
                .color(disc.color)
                .move(...disc.position)
                .turnX(Math.PI/2)
                .scale(disc.value, disc.value, discHeight);
        });
        
        lastControllerPosition = controllerPos;

        // if (leftPressed || rightPressed) {
        //     if (!selectedDisc) {
        //         // Check for intersection with discs
        //         discs.forEach(disc => {
        //             let discMatrix = createCubeMatrix(disc.position, disc.value);
        //             let isHit = leftPressed ? lcb.hitRect(discMatrix) : rightPressed ? rcb.hitRect(discMatrix) : false;
    
        //             if (isHit) {
        //                 selectedDisc = disc; // Select the disc
        //                 lastControllerPosition = controllerPos; // Store the controller's position
        //                 canMove = towers[selectedDisc.tower].stack.peek().value == selectedDisc.value;  // Check if the disc can be moved, i.e. at the top of the stack
        //             }
        //         });
        //     } else if (lastControllerPosition && controllerPos && canMove) {
        //         // Calculate the change in controller position
        //         let delta = cg.subtract(controllerPos, lastControllerPosition);
    
        //         // Compute the new position for the selected disc
        //         let newPosition = cg.add(selectedDisc.position, delta);

        //         // Create the transformation matrix for the selected disc at the new position
        //         let newDiscMatrix = createCubeMatrix(newPosition, selectedDisc.value);

        //         // Check for collisions with other discs
        //         let noCollision = discs.some(otherDisc => {
        //             if (otherDisc === selectedDisc) return true; // Skip the selected disc itself
        //             let otherDiscMatrix = createCubeMatrix(otherDisc.position, otherDisc.value);
        //             return !cg.isBoxIntersectBox(newDiscMatrix, otherDiscMatrix);
        //         });
    
        //         // If no collision, update the position and transformation of the selected disc
        //         if (noCollision) {
        //             selectedDisc.position = newPosition;

        //             // Update the disc's transformation
        //             selectedDisc.object.setMatrix(
        //                 cg.mMultiply(
        //                     cg.mTranslate(selectedDisc.position[0], selectedDisc.position[1], selectedDisc.position[2]),
        //                     cg.mMultiply(
        //                         cg.mRotateX(Math.PI / 2), // Rotate the disc on the X-axis
        //                         cg.mScale(selectedDisc.value * 2, selectedDisc.value * 2, 0.2) // Apply scaling
        //                     )
        //                 )
        //             );
        //             console.log("Moved disc to:", selectedDisc.position);

        //             // Update the last controller position
        //             lastControllerPosition = controllerPos;
        //         }
                
        //     }
        // }

        // if (leftReleased || rightReleased) {
        //     if (selectedDisc) {  
        //         // Check if the disc is dropped on a valid tower
        //         let newTower = findValidTower(selectedDisc.position, towers);
        //         if (newTower != null) {
        //             let oldTower = towers[selectedDisc.tower];
        //             let newTowerObj = towers[newTower];
                    
        //             // Add the disc to the new tower
        //             let isPushed = newTowerObj.stack.push(selectedDisc);
        //             if (isPushed) {
        //                 // Remove the disc from the old tower
        //                 oldTower.stack.pop();

        //                 // Update the disc's tower index
        //                 selectedDisc.tower = newTower;

        //                 // Update the disc's position to be on top of the new tower
        //                 selectedDisc.position = [towers[newTower].pos, selectedDisc.position[1], 0];
        //                 selectedDisc.valid_position = selectedDisc.position;
        //             }
        //             console.log("Moved disc to tower:", newTower);

        //         } else {
        //             // If not dropped on a valid tower, return to original position
        //             selectedDisc.position = selectedDisc.valid_position;
        //         }
        //         // Update the disc's transformation
        //         selectedDisc.object.setMatrix(
        //             cg.mMultiply(
        //                 cg.mTranslate(selectedDisc.position[0], selectedDisc.position[1], selectedDisc.position[2]),
        //                 cg.mMultiply(
        //                     cg.mRotateX(Math.PI / 2), // Rotate the disc on the X-axis
        //                     cg.mScale(selectedDisc.value * 2, selectedDisc.value * 2, 0.2) // Apply scaling
        //                 )
        //             )
        //         );
        //     }
        //     selectedDisc = null; // Deselect the disc
        //     lastControllerPosition = null; // Reset the last controller position
        //     canMove = false; // Reset the move flag
        //     // Check if the disc is dropped on a valid tower
            
        // }

    });
 }
 