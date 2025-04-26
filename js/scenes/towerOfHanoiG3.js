import towerStack from '../util/towerStack.js';
import * as cg from "../render/core/cg.js";
import { G3 } from "../util/g3.js";

let numDiscs = 3;
let towers = [], avatars = [], discs = [];
const towerPositions = [-1.5, 0, 1.5];
towerPositions.forEach(pos => {
    towers.push({ pos, stack: new towerStack() });
});

// Initialize separate message channel
server.init('pinchMessages', {});
server.init('towerState', {
    discs: discs,
    towers: towers
});


function initializeDiscs(config = {numDiscs: 3}) {
    towers.forEach(t => {
        t.stack = new towerStack();
    });
    for(let i = 0; i < numDiscs; i++) {
        const discIndex = numDiscs - 1 - i;
        const discWidth = 0.4 + (discIndex * 0.1);
        discs.push({
            width: discWidth,
            tower: 0,
            position: [towers[0].pos, 0.2 + i*0.2, 0]
        });
    }
    return discs;
}

function findNearestDisc(pos) {
    let minDist = Infinity, nearest = null;
    towers.forEach(tower => {
        if(tower.stack.size() > 0) {
            const disc = tower.stack.peek();
            const dist = cg.distance(pos, [tower.pos, disc.y, 0]);
            if(dist < minDist) {
                minDist = dist;
                nearest = { tower, disc };
            }
        }
    });
    return nearest;
}


export const init = async model => {
    let g3 = new G3(model, draw => {
        // Draw towers and discs
        towers.forEach(tower => {
            draw.color('#606060').fill2D([[-.1,-.1],[.1,-.1],[.1,.1],[-.1,.1]], [tower.pos, 0, 0]);
            discs.forEach((disc, i) => {
                draw.color(disc.color).fill2D([[-disc.width,-.1],[disc.width,-.1],[disc.width,.1],[-disc.width,.1]], 
                    disc.position);
            });
        });
        
        // Draw other participants' avatars
        avatars.forEach(avatar => {
            draw.color('#FFFFFF').textHeight(.1).text(avatar.id, avatar.pos);
        });

        // Pinch selection/messages
        if(draw.view() === 0) {
            for(let hand of ['left','right']) {
                if(draw.pinch(hand, 1)) {
                    const fingerPos = draw.finger(hand, 1);
                    const nearest = findNearestDisc(fingerPos);
                    if(nearest) server.send('pinchMessages', {
                        selectedDisc: nearest,
                        pinchPos: cg.roundVec(4, fingerPos)
                    });
                }
            }
        }
    });

    
    let discs = initializeDiscs({numDiscs});

    model.animate(() => {
        const towerState = server.synchronize('towerState');
        
        // Process messages
        server.sync('pinchMessages', msgs => {
            msgs.forEach(handlePinchMessage);
        });
        
        // Update game state
        if(clientID === clients[0]) {
            // console.log('Updating game state, clientID:', clientID, 'towerState:', towerState);
            server.broadcastGlobal('towerState');
        }
        
        g3.update();
    });
};

