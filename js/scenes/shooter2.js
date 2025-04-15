import * as cg from "../render/core/cg.js";
import { G3 } from "../util/g3.js";
import { G2 } from "../util/g2.js";

let pink = '#ff8080', blue = '#00c0ff', myGender, yShare = 1.5;

let player0Tiles = [
   [-0.3, yShare - 0.1, -0.6], // Each player has 3 cards
   [ 0.0, yShare - 0.1, -0.6],
   [ 0.3, yShare - 0.1, -0.6],
];

let player1Tiles = [
   [-0.3, yShare - 0.1, 0.6],
   [ 0.0, yShare - 0.1, 0.6],
   [ 0.3, yShare - 0.1, 0.6],
];

let sharedTiles = [  // Shared tiles both players can interact with
   [-0.3, yShare, 0],
   [ 0.0, yShare, 0],
   [ 0.3, yShare, 0],
];

let p = [...player0Tiles, ...player1Tiles, ...sharedTiles];  // DEFAULT TILE POSITIONS
let V = [[0,0,0],[0,0,0],[0,0,0]];
let sharedHidden = [false, false, false];

server.init('p3S', { p: p, id: 0, sharedHidden: sharedHidden });  // PERSISTENT STATE OBJECT
server.init('p3I', {});  // MESSAGE PASSING OBJECT

let g2Health0 = new G2();
let g2Health1 = new G2();

export const init = async model => {
    let health0 = model.add('square').setTxtr(g2Health0.getCanvas());
    let health1 = model.add('square').setTxtr(g2Health1.getCanvas());

    let g3 = new G3(model, draw => {
        let w = .2, h = .075, b = .003;
        let p = p3S.p;  // Get all tile positions
        let sharedHidden = p3S.sharedHidden;  // Get all shared tile visibility

        if (p){
            for (let n = 0; n < p.length; n++) {
                let isShared = n >= 6;
                if (isShared && sharedHidden[n - 6]) continue;

                // Set player 0 tiles to pink and player 1 tiles to blue, shared tiles to white
                let color = (n < 3) ? pink : (n < 6) ? blue : 'white';

                draw.color('black')
                    .fill2D([[-w-b, -h-b], [w+b, -h-b], [w+b, h+b], [-w-b, h+b]], p[n]);  // backgrouond to make white tile more distinct
                draw.color(color)
                    .fill2D([[-w, -h], [w, -h], [w, h], [-w, h]], p[n]);

                if (!isShared) {
                    // WHY?
                    if ((draw.view() == 1 && n < 3) || // if G3 is rendered for right eye and tile is player 0
                    (draw.view() == 0 && n >= 3 && n < 6)) {  // if G3 is rendered for left eye and tile is player 1
                        draw.color('black')
                            .textHeight(0.06)
                            .text("A", p[n]);
                    }
                } else {
                draw.color('black')
                        .textHeight(0.06)
                        .text("B", p[n]);
                }
            }
        }

        // Update G2 objects .... Why is this being called in a G3 draw function?
        g2Health0.update(); health0.identity().move(-.5, 1.8, -.5).scale(.15);
        g2Health1.update(); health1.identity().move(-.5, 1.8,  .5).scale(.15);

        if (draw.view() == 0) {  // G3 is rendered for left eye
            for (let hand in { left: {}, right: {} }) {  // for each hand
                if (draw.pinch(hand, 1)){  // pinch gesture
                    server.send('p3I', {  // Send the position of the pinch to all clients
                        pinch: cg.roundVec(4, draw.finger(hand, 1)),  // pinch position
                        gender: myGender  // WHAT's the point of sending Gender, why not just use clientID?
                    });
                }
            }
        }
   });

    model.animate(() => {
        if (clientID == clients[0]) {
            myGender = 0;
        } else {
            myGender = 1;
        }
        // myGender = clientID == clients[0] ? 0 : 1;
        p3S = server.synchronize('p3S');


        // Whats the point of this? Randomly change the position of the tiles?
        for (let i = 6; i < 9; i++) {
            if (p3S.sharedHidden[i - 6]) continue;
            for (let j = 0; j < 3; j++) {
                // Whats V? 
                V[i - 6][j] = Math.max(-0.01, Math.min(0.01,
                    V[i - 6][j] + 0.1 * (Math.random() - 0.5) * model.deltaTime));
                // Seems like this will eventually make the tiles move out of the screen
                p3S.p[i][j] += V[i - 6][j] * model.deltaTime;
                if (j === 2){
                    p3S.p[i][j] = Math.max(-0.3, Math.min(0.3, p3S.p[i][j]));
                }
            }
        }

        // Respond to a pinch message by the G3 objects
        server.sync('p3I', msgs => {
            for (let id in msgs) {  // Go through all messages
                let f = msgs[id].pinch;  // pinch position
                if (!f) continue;

                // Get the closest shared tile to the pinch position
                const distances = [];
                for (let i = 6; i < 9; i++) {
                    if (p3S.sharedHidden[i - 6]){
                        distances.push(10000);
                        continue;
                    }
                    let d = cg.distance(p3S.p[i], f);
                    distances.push(d);
                }
                let argmin = distances.indexOf(Math.min(...distances));
                p3S.sharedHidden[argmin] = true;
                // The mechanism needs a delay, otherwise all the tiles will be hidden at once
            }
        });

        // First client ensures the game state is consistent across clients
        if (clientID == clients[0])
            server.broadcastGlobal('p3S');

        g3.update();
   });

   // This should not be hardcoded
   g2Health0.render = function() {
      this.clear();
      this.setColor([0, 1, 0, 1]);
      this.textHeight(.1);
      this.text('Player 1 Health: 100', 0, 0, 'center');
   }

   // This should not be hardcoded And should alsso only be shown if there are two players
   g2Health1.render = function() {
      this.clear();
      this.setColor([0, 1, 0, 1]);
      this.textHeight(.1);
      this.text('Player 2 Health: 100', 0, 0, 'center');
   }
};

