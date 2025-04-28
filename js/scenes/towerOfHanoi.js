import towerStack from '../util/towerStack.js';
import * as cg from "../render/core/cg.js"; 
import { buttonState, controllerMatrix } from "../render/core/controllerInput.js";
import { lcb, rcb } from '../handle_scenes.js'

let numOfDiscs = 4; // Number of discs in the game
const defTower = 0; // Default tower index
let towerState = { discs: {}, selectedDisc: null, towers: {}, terminal: false };
server.init('towerState', towerState); // Initialize shared state for discs and towers
server.init('resetMessage', {}); // Initialize shared state for reset message
let towers = {}, avatars = [], discs = {};

function findValidTower(discPosition, towers) {

    const maxDistance = 0.2; // Maximum allowed distance from the tower
    const xTolerance = 0.3; // Degree of freedom for the x-axis
    const baseY = 0.2;      // Default Y position for the base of the tower

    for (let i in towerState.towers) {
        const tower = towers[i];
        const towerX = towerState.towers[i].pos; // X position of the tower
        const towerZ = 0;         // TODO: i think this might need to change

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
                return parseInt(i); // Return the index of the valid tower
            }
        }
    }

    return null; // No valid tower found
}

function checkCompleteState(towers) {
    let lastTower = towers[Object.keys(towers).length - 1].stack;
    if (lastTower.size() === numOfDiscs) {
        console.log("Game Complete");
        towerState.terminal = true;
        return true;
    }
    return false;
}

function resetTowerState(model) {
    console.log("Tower state reset");
    // Reset the tower stacks
    for (let t in towerState.towers) {
        towers[t.tid].stack = new towerStack();
    }
    // Remove the discs from the model
    for (d in discs){
        model.removeNode(discs[d].object);
    }
    discs = {};
    towerState.discs = {};
    towerState.selectedDisc = null;
    towerState.terminal = false;
    // Reset the discs
    createDiscs(numOfDiscs);
    console.log("Discs reset");
}

export const init = async model => {

    model.txtrSrc(1, '../media/textures/wood.jpg');
 
    let board = model.add();
    let base = board.add('cube').txtr(1).move(0,0,0).scale(2.5,0.1,1);
    let towerPos = [-1.5, 0, 1.5];
    towerPos.forEach((pos, i) => {
        let tower = board.add('tubeY').txtr(1).move(pos, 1, 0).scale(0.1, 1, 0.1).opacity(0.5);
        let tStack = new towerStack();
        towerState.towers[i] = {
            pos: pos,
            tid: i,
        };
        towers[i] = {
            object: tower,
            stack: tStack,
            tid: i,
        };
    });

    let colors = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
            
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
            const yPos = baseY + (i * (discHeight+0.1)); // Adjusted for better spacing
            let discGroup = model.add();
            discGroup.disc = discGroup.add('donut');
            discGroup.collisionCube = discGroup.add('cube');
            let discObject = {
                did: i,
                object: discGroup,
            };
            discs[i] = discObject;
            towerState.discs[i] = {
                color: colors[discIndex % colors.length],
                value: discWidth,
                height: discHeight,
                position: [towerState.towers[0].pos, yPos, 0],
                valid_position: [towerState.towers[0].pos, yPos, 0],
                tower: 0,  
                did: i
            };
            towers[0].stack.push(towerState.discs[i]);
        }
    };

    let selectedDisc = null;
    let offset = null;

    model.move(0,1.5,-0.5).scale(.1).animate(() => {
        
        towerState = server.synchronize('towerState'); // Fetch shared state
        // discs = towerState.discs;
        // towers = towerState.towers;
        board.identity();
        checkCompleteState(towers)

        if (!controllerMatrix.left || !controllerMatrix.right) {
            return; // Skip frame if controller tracking is lost
        }

        if (Object.keys(towerState.discs).length === 0) {
            console.log("No discs found, creating new discs");
            createDiscs(numOfDiscs);
        }
        if (Object.keys(discs).length == 0){
            console.log("No discs found, creating new discs");
            createDiscs(numOfDiscs);
        }


        // Update all collision cube position first
        Object.values(discs).forEach((disc, index, array) => {
            let discInfo = towerState.discs[disc.did];
            disc.object.collisionCube
                .identity()
                .opacity(0.0001)
                .scale(discInfo.value, discInfo.value, discInfo.height/2);
            disc.object.identity()
                .move(...discInfo.position)
                .turnX(Math.PI/2);
        });

        // Update all disc positions and orientations
        Object.values(discs).forEach((disc, index, array) => {
            let discInfo = towerState.discs[disc.did];
            disc.object.disc
                .identity()
                .color(...discInfo.color)
                .scale(discInfo.value, discInfo.value, discInfo.height);
            disc.object.identity()
                .move(...discInfo.position)
                .turnX(Math.PI/2);
        });
        
        // input
        let leftPressed   = buttonState.left[0].pressed;
        let rightPressed  = buttonState.right[0].pressed;

        if ((leftPressed || rightPressed) && !selectedDisc) {
            // Check for intersection with discs
            for (let i in discs) {
                let disc = discs[i];  // Get the disc node object
                let discInfo = towerState.discs[i];  // Get the disc info from the shared state
                let towerInfo = towerState.towers[discInfo.tower];  // Get the tower info from the shared state
                let tower = towers[towerInfo.tid];  // Get the tower object from the local towers object

                let controllerPos = inputEvents.pos(leftPressed ? 'left' : 'right');
                let globaldiscpos = disc.object.collisionCube.getGlobalPos();

                let hit = (cg.distance([controllerPos[0], controllerPos[2]], [globaldiscpos[0], globaldiscpos[2]]) < 0.05 + (discInfo.value*0.1)) &&  // Check distance in XZ plane
                          (Math.abs(controllerPos[1] - globaldiscpos[1]) < 0.05 + (discInfo.height*0.1)/2);  // Check distance in Y axis
                console.log("Hit:", hit, "Controller Position:", controllerPos, "Disc Position:", globaldiscpos, "Sliced");

                if (hit && tower.stack.peek().did == discInfo.did) {
                    // Select the disc
                    selectedDisc = disc;
                    towerState.selectedDisc = i;
                    break;
                }
            }
        } else if ((selectedDisc && towerState.selectedDisc) && (leftPressed || rightPressed)) {

            let controllerPos = inputEvents.pos(leftPressed ? 'left' : 'right');
            const newPosition = cg.scale(cg.subtract(controllerPos, [0, 1.5, -0.5]), 10);  // transformation to undo global positioning
            console.log("New position:", newPosition);

            // Update the matrix with the new position to check for collision
            let newDiscMatrix = selectedDisc.object.collisionCube.getGlobalMatrix(); // Get the current matrix
            newDiscMatrix[12] = controllerPos[0]; // Update X position
            newDiscMatrix[13] = controllerPos[1]; // Update Y position
            newDiscMatrix[14] = controllerPos[2]; // Update Z position

            // TODO: Work on collision detection, this does not work
            // Check for collision with other discs
            let noCollision = Object.values(discs).some(otherDisc => {
                if (otherDisc === selectedDisc) return true; // Skip the selected disc itself

                let otherDiscMatrix = otherDisc.object.collisionCube.getGlobalMatrix(); // Get the matrix for the other disc
                return !cg.isBoxIntersectBox(newDiscMatrix, otherDiscMatrix); // Check for collision
            });
            if (noCollision) {
                console.log("No collision detected");
                // If no collision, update the position
                towerState.discs[towerState.selectedDisc].position = newPosition;
                selectedDisc.object.identity().move(...newPosition).turnX(Math.PI/2);;
            } else {
                console.log("Collision detected, reverting to previous position");
                // If there is a collision, revert to the previous position
                towerState.discs[towerState.selectedDisc].position = previousPosition;
                selectedDisc.object.identity().move(...previousPosition).turnX(Math.PI/2);;
            }
        } else if (selectedDisc) {
            // Check if the disc is dropped on a valid tower
            let selectedDiscInfo = towerState.discs[towerState.selectedDisc];
            const newTowerIndex = findValidTower(selectedDiscInfo.position, towers);
            if (newTowerIndex !== null && newTowerIndex != selectedDiscInfo.tower) {
                const oldTowerStack = towers[selectedDiscInfo.tower].stack;
                const newTowerStack = towers[newTowerIndex].stack;
                const newYPosition = newTowerStack.peek() ? newTowerStack.peek().position[1] + 0.2 : baseY;

                console.log("Dropped on tower:", newTowerIndex);

                if (newTowerStack.push(selectedDiscInfo)) {  // Attempt to push the disc onto the new tower
                    // If successful, update the disc's tower and position and remove it from the old tower
                    oldTowerStack.pop();
                    towerState.discs[towerState.selectedDisc].tower = newTowerIndex;
                    towerState.discs[towerState.selectedDisc].position = [towerState.towers[newTowerIndex].pos, newYPosition, 0];
                    towerState.discs[towerState.selectedDisc].valid_position = [towerState.towers[newTowerIndex].pos, newYPosition, 0];
                } else {
                    // If the disc can't be placed, return it to its original position
                    towerState.discs[towerState.selectedDisc].position = [...selectedDiscInfo.valid_position];
                    console.log("Invalid move, returning to original position");
                }
            } else {
                // If not dropped on a valid tower, return to original position
                towerState.discs[towerState.selectedDisc].position = [...selectedDiscInfo.valid_position];
            }
            // Update the disc's transformation
            selectedDisc = null;
            towerState.selectedDisc = null;
            offset = null;
        }
    });

    if (clientID == clients[0]) {
        server.broadcastGlobal('towerState'); // Broadcast the updated state to all clients
    }
    server.sync('resetMessage', msgs => {
        console.log("Reset message received");
        for (let id in msgs) {
            console.log("Reset message from client:", id);
            console.log("Reset message content:", msgs[id]);
            if (msgs[id].reset) {
                resetTowerState(model);
            }
        }
    });

        
 }
 