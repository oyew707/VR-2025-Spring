

let numOfDiscs = 4; // Number of discs in the game
const defTower = 0; // Default tower index
let towers = {}, discObjs = {};
window.discs = {};
window.towerIsValid = true;
let towerPos = [-1.5, 0, 1.5];
  
function validateAllDiscPositions(towers) {
    const maxDistance = 0.2; // Maximum allowed distance from the tower
    const xTolerance = 0.3; // Degree of freedom for the x-axis
    const baseY = 0.2;      // Default Y position for the base of the tower

    // Clear previous tower stacks
    towerPos.forEach((pos, i) => {
        towers[i].stack = [];
    });
    // Loop through all discs to validate their positions
    for (let discId in window.discs) {
        const disc = window.discs[discId];
        const discPosition = disc.position;
        disc.tower = null; // Reset tower assignment for each disc

        // Loop through towers to find a valid one for the current disc
        for (let i in towers) {
            const tower = towers[i];
            const towerX = tower.pos; // X position of the tower
            const towerZ = 0; // TODO: Update if necessary

            // Calculate the distance between the disc and the tower
            const dx = Math.abs(discPosition[0] - towerX);
            const dz = Math.abs(discPosition[2] - towerZ);

            // Check if the disc is within the allowed distance
            if (dx <= maxDistance && dz <= maxDistance) {
                disc.tower = parseInt(i);
                tower.stack.push(disc); 
                break;
            }
        }

        // If no valid tower is found, return false
        if (disc.tower === null) {
            return false;
        }
    }
    // Check if all discs are within their respective tower's bounds
    return Object.values(towers).every((tower, i) => {
        tower.stack.sort((a, b) => b.value - a.value); // Sort discs in the tower by their value
        // Check if all discs are within their respective tower's bounds
        tower.stack.every((disc, j) => {
            let yTarget = baseY + (j * (disc.height + 0.1))
            return yTarget+xTolerance >= discPosition[1] >= yTarget-0.1
        });
    });

}
export const init = async model => {

    model.txtrSrc(1, '../media/textures/wood.jpg');
 
    let board = model.add();
    let base = board.add('cube').txtr(1).move(0,0,0).scale(2.5,0.1,1);
    
    towerPos.forEach((pos, i) => {
        let tower = board.add('tubeY').txtr(1).move(pos, 1, 0).scale(0.1, 1, 0.1).opacity(0.5);
        towers[i] = {
            object: tower,
            pos: pos,
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
                color: colors[discIndex % colors.length],
                value: discWidth,
                height: discHeight,
                position: [towerPos[0], yPos, 0],
                valid_position: [towerPos[0], yPos, 0],
                tower: 0,
            };
            discObjs[i] = {
                did: i,
                object: discGroup,
            };
            window.discs[i] = discObject;
        }
    };

    model.move(0,1.5,-0.5).scale(.1).animate(() => {
        board.identity();

        if (Object.keys(discs).length == 0){
            console.log("No discs found, creating new discs");
            createDiscs(numOfDiscs);
        }

        // Update all collision cube position first
        Object.values(discObjs).forEach((disc, index, array) => {
            let discInfo = window.discs[disc.did];
            disc.object.collisionCube
                .identity()
                .opacity(0.0001)
                .scale(discInfo.value, discInfo.value, discInfo.height/2);
            disc.object.identity()
                .move(...discInfo.position)
                .turnX(Math.PI/2);
        });
        // Update all disc positions and orientations
        Object.values(discObjs).forEach((disc, index, array) => {
            let discInfo = window.discs[disc.did];
            disc.object.disc
                .identity()
                .color(...discInfo.color)
                .scale(discInfo.value, discInfo.value, discInfo.height);
            disc.object.identity()
                .move(...discInfo.position)
                .turnX(Math.PI/2);
        });

        window.towerIsValid = validateAllDiscPositions(towers);
    });
}