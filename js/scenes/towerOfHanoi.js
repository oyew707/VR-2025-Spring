import towerStack from '../util/towerStack.js';
import * as cg from "../render/core/cg.js"; 
import { buttonState, controllerMatrix } from "../render/core/controllerInput.js";
import { lcb, rcb } from '../handle_scenes.js'

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
            if (targetY+xTolerance >= discPosition[1] >= targetY-0.1) {
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
            let discGroup = model.add();
            discGroup.disc = discGroup.add('donut');
            discGroup.collisionCube = discGroup.add('cube');
            let discObject = {
                color: colors[discIndex % colors.length],
                value: discWidth,
                height: discHeight,
                object: discGroup,
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
    let offset = null;

    model.move(0,1.5,0).scale(.1).animate(() => {
        board.identity();

        if (!controllerMatrix.left || !controllerMatrix.right) {
            return; // Skip frame if controller tracking is lost
        }
        // Update all disc positions and orientations
        discs.forEach((disc, index, array) => {
            disc.object.disc
                .identity()
                .color(...disc.color)
                .scale(disc.value, disc.value, disc.height);
            disc.object.collisionCube
                .identity()
                .opacity(0.0001)
                .scale(disc.value, disc.value, disc.height/2);
            disc.object.identity()
                .move(...disc.position)
                .turnX(Math.PI/2);
            // console.log(index, "Disc position:", disc.position);
            // console.log(index, "Disc scale:", disc.value, disc.value, disc.height);
        });
        
        // input
        let leftPressed   = buttonState.left[0].pressed;
        let rightPressed  = buttonState.right[0].pressed;

        if ((leftPressed || rightPressed) && !selectedDisc) {
            console.log("Pressed and not selected");
            // Check for intersection with discs
            for (let i = 0; i < discs.length; i++) {
                let disc = discs[i];
                const hit = (leftPressed ? lcb : rcb).hitRect(disc.object.collisionCube.getGlobalMatrix());
                if (hit) {console.log("Tower:", disc.tower, "TOwer:", towers[disc.tower]);}
                // Check if the disc is at the top of the stack and the controller is close enough
                if (hit && towers[disc.tower].stack.peek() === disc) {
                    // Select the disc
                    selectedDisc = disc;
                    let projectedPosition = (leftPressed ? lcb : rcb).projectOntoBeam(selectedDisc.position);
                    offset = cg.subtract(disc.position, projectedPosition);
                    break;
                }
            }
        } else if (selectedDisc && (leftPressed || rightPressed)) {
            // Use projectOntoBeam to get the new position
            const previousPosition = selectedDisc.position;
            const projectedPosition = (leftPressed ? lcb : rcb).projectOntoBeam(selectedDisc.position);
            const newPosition = cg.add(projectedPosition, offset);

            // Update the matrix with the new position to check for collision
            let newDiscMatrix = selectedDisc.object.collisionCube.getGlobalMatrix(); // Get the current matrix
            newDiscMatrix[12] = newPosition[0]; // Update X position
            newDiscMatrix[13] = newPosition[1]; // Update Y position
            newDiscMatrix[14] = newPosition[2]; // Update Z position

            // TODO: Work on collision detection, this does not work
            // Check for collision with other discs
            let noCollision = discs.some(otherDisc => {
                if (otherDisc === selectedDisc) return true; // Skip the selected disc itself

                let otherDiscMatrix = otherDisc.object.collisionCube.getGlobalMatrix(); // Get the matrix for the other disc
                return !cg.isBoxIntersectBox(newDiscMatrix, otherDiscMatrix); // Check for collision
            });
            if (noCollision) {
                console.log("No collision detected");
                // If no collision, update the position
                selectedDisc.position = newPosition;
                selectedDisc.object.identity().move(...selectedDisc.position).turnX(Math.PI/2);;
            } else {
                console.log("Collision detected, reverting to previous position");
                // If there is a collision, revert to the previous position
                selectedDisc.position = previousPosition;
                selectedDisc.object.identity().move(...selectedDisc.position).turnX(Math.PI/2);;
            }
        } else if (selectedDisc) {
            console.log("Released");
            // Check if the disc is dropped on a valid tower
            const newTowerIndex = findValidTower(selectedDisc.position, towers);
            if (newTowerIndex !== null && newTowerIndex !== selectedDisc.tower) {
                const oldTowerStack = towers[selectedDisc.tower].stack;
                const newTowerStack = towers[newTowerIndex].stack;
                const newYPosition = newTowerStack.peek() ? newTowerStack.peek().position[1] + 0.2 : baseY;

                console.log("Dropped on tower:", newTowerIndex);

                if (newTowerStack.push(selectedDisc)) {
                    oldTowerStack.pop();
                    selectedDisc.tower = newTowerIndex;
                    selectedDisc.position = [towers[newTowerIndex].pos, newYPosition, 0];
                    selectedDisc.valid_position = selectedDisc.position;
                } else {
                    // If the disc can't be placed, return it to its original position
                    selectedDisc.position = [...selectedDisc.valid_position];
                    console.log("Invalid move, returning to original position");
                }
            } else {
                // If not dropped on a valid tower, return to original position
                selectedDisc.position = [...selectedDisc.valid_position];
            }
            // Update the disc's transformation
            selectedDisc = null;
        }
    });
        
 }
 