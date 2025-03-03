import * as cg from "../render/core/cg.js";
import { buttonState, joyStickState } from "../render/core/controllerInput.js";


window.turnInfo = {                              // SHARED STATE IS A GLOBAL VARIABLE.
    turn: 'red',                                   // Red for x and blue for o
    xyz: [0,0.1,0],                               // position of player box to play
    record: {}                                  // Stores record of each turn
 };



export const init = async model => {

    let game = model.add();
    const cubes = new Array();
    for (let i = 1; i < 4; i++) {  // X axis
        for (let j = 1; j < 4; j++) {  // Y axis
            for (let k = 1; k < 4; k++) {  // Z axis
                cubes.push(game.add('cube').color(0, 1, 0).move(i*0.5, j*0.5, k*0.5).scale(.1).opacity(0.5));
            }
        }
    }
    console.log("Number of cubes: " + cubes.length.toString());

    let ball = game.add('cube').color(turnInfo.turn);


    inputEvents.onPress = hand => {   // back button
        turnInfo.xyz = inputEvents.pos(hand);      // AFTER AN INPUT EVENT MODIFIES STATE
        server.broadcastGlobal('turnInfo');        // BROADCAST THE NEW STATE VALUE.
        console.log("[onPress] turnInfo: " + JSON.stringify(turnInfo));
     }
     inputEvents.onDrag = hand => {
        turnInfo.xyz = inputEvents.pos(hand);      // AFTER AN INPUT EVENT MODIFIES STATE
        server.broadcastGlobal('turnInfo');        // BROADCAST THE NEW STATE VALUE.
        console.log("[onDrag] turnInfo: " + JSON.stringify(turnInfo));
     }
     inputEvents.onRelease = hand => {
        // TODO: Fix the intersect function
        
        let i = 0;
        while(i < cubes.length){
            let isIntersect = cg.isBoxIntersectBox(ball.getGlobalMatrix(), cubes[i].getGlobalMatrix());
            console.log("Intersected with cube: " + i.toString() + " " + isIntersect.toString());
            
            if(!turnInfo.record.hasOwnProperty(i.toString())  &&  // if cube is not already clicked
                isIntersect  // if sphere intersects with cube
            ){
                console.log("Intersected with cube: " + i.toString());
                cubes[i].color(turnInfo.turn);
                turnInfo.record[i.toString()] = turnInfo.turn;
                turnInfo.turn = turnInfo.turn == 'red' ? 'blue' : 'red';
                // Log Record
                console.log("records: " + JSON.stringify(window.record));
                i = cubes.length; // break
            }
            i += 1;
        }
        turnInfo.xyz = [0,0.1,0];                      // AFTER AN INPUT EVENT MODIFIES STATE
        server.broadcastGlobal('turnInfo');        // BROADCAST THE NEW STATE VALUE.
     }


    model.animate(() => {
        turnInfo = server.synchronize('turnInfo'); // BEGIN ANIMATE BY SYNCHRONIZING STATE.

        model.identity().move(0,1,0);
        ball.identity().move(turnInfo.xyz).scale(.1);
        
    })

}