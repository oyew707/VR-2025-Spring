import { lcb, rcb } from '../handle_scenes.js'; // IMPORT LEFT CONTROLLER BEAM
import { G2 } from "../util/g2.js";

const agent_url = `${window.location.protocol}//${window.location.hostname}:3000`;

window.tictactoestate = {
    cubes: [],
    values: [1, 1, 1, 1, 1, 1, 1, 1, 1], // Default values for cubes
    currentPlayer: 1,
    player1: null,
    player2: null,
    gameState: 'GAME_START',
    winner: null,
};
server.init('ttt', {});  

const WIN_PATTERNS = [
    [0,1,2], [3,4,5], [6,7,8], // Rows
    [0,3,6], [1,4,7], [2,5,8], // Columns
    [0,4,8], [2,4,6] // Diagonals
];

function checkWin(cubes){
    // Check if all cubes are occupied
    if (cubes.every(cubeObj => cubeObj.owner != 0)) {
        setTimeout(() => {
            tictactoestate.gameState = 'DRAW';
            server.broadcastGlobal('tictactoestate'); // Broadcast the updated state
            console.log('Game is a draw!');
        }, 1000); // 1-second delay
        return;
    }
    for (let pattern of WIN_PATTERNS) {
        const owner = cubes[pattern[0]].owner;
        if (owner && pattern.every(i => cubes[i].owner === owner)) {
            setTimeout(() => {
                tictactoestate.winner = owner;
                tictactoestate.gameState = owner === 1 ? 'PLAYER_1_WIN' : 'PLAYER_2_WIN';
                server.broadcastGlobal('tictactoestate'); // Broadcast the updated state
                console.log(`Player ${owner} wins!`);
            }, 1000); // 1-second delay
            return;
        }
    }
}

async function getActionValue() {
    // tictactoestate = server.synchronize('tictactoestate'); // Synchronize game state
    let params = { 'state': tictactoestate.cubes.map(cube => cube.owner * tictactoestate.currentPlayer) };
    if (params.state.filter(x => x == 0).length == tictactoestate.values.filter(x => x == 1).length) {
        console.log('No action value needed');
        return;
    }
    const response = await fetch(`${agent_url}/get_state_values`, {
        method: 'POST',
        // mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });
    const result = await response.json();

    // Ensure the length of result matches the length of cubes
    if (result.length !== tictactoestate.cubes.length) {
        console.error('Result length does not match cubes length!');
        return;
    }

    // Find min and max values for cubes where owner == 0
    const availableValues = result.filter((_, index) => tictactoestate.cubes[index].owner === 0);
    const minValue = Math.min(...availableValues);
    const maxValue = Math.max(...availableValues);

    // Standardize the values
    const standardizedValues = result.map((value, index) => {
        if (tictactoestate.cubes[index].owner !== 0) {
            return 1; // Set to 1 for occupied cubes
        }
        // Scale values between 0.5 and 1
        return 0.5 + ((value - minValue) / (maxValue - minValue)) * 0.5;
    });
    tictactoestate.values = standardizedValues;
}

export const init = async model => {
    let round = t => (1000 * t >> 0) / 1000; 

    const cubeSize = 0.1; // Size of each cube
    const spacing = 0.25; // Space between cubes
    const colors = { default: [0.5, 0.5, 0.5], red: [1, 0, 0], green: [0, 1, 0] };

    let cubeObjects = [];

    // Create a 3x3 grid of cubes
    for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
            let cube = model.add('cube');
            tictactoestate.cubes.push({
                // obj: cube, 
                color: colors.default, 
                position: [round(i * spacing - spacing), round(j * spacing - spacing), 0],
                owner: 0, // 0 means unoccupied, 1 for player 1 and -1 for player 2
            });
            cubeObjects.push(cube);
            console.log('Cube created at:', i * spacing - spacing, j * spacing - spacing, 0);
        }
    }

    // HUD Object
    let g2A = new G2();
    g2A.render = function() {
        let text = '';
        if (tictactoestate.gameState === 'GAME_START') {
            if ((clientID == tictactoestate.player1 && tictactoestate.currentPlayer == 1) ||
               (clientID == tictactoestate.player2 && tictactoestate.currentPlayer == -1)) {
                text = 'Your Turn';
            } else if (clientID == tictactoestate.player1) {
                text = 'Player 2 Turn';
            } else if (clientID == tictactoestate.player2) {
                text = 'Player 1 Turn';
            }
        } else if (tictactoestate.gameState === 'PLAYER_1_WIN') {
            text = 'Player 1 Wins!';
        } else if (tictactoestate.gameState === 'PLAYER_2_WIN') {
            text = 'Player 2 Wins!';
        } else if (tictactoestate.gameState === 'DRAW') {
            text = 'Game is a Draw!';
        }
        this.setColor('white');
        this.fillRect(-1,-1,2,2);
        this.setColor('black');
        this.textHeight(.1);
        this.text(text, 0, 0, 'center');
    }
    model.txtrSrc(1,g2A.getCanvas());
    let objA = model.add('square').txtr(1);

    // Hover interaction: Increase cube size on intersection
    model.move(0, 1.5, -1).animate(() => {
        g2A.update();
        tictactoestate = server.synchronize('tictactoestate'); // Synchronize game state

        // First client sets all players and ensures the game state is initialized
        if (clientID == clients[0]) {
            if (tictactoestate.gameState !== 'GAME_START' && (inputEvents.isAltPressed('left') || inputEvents.isAltPressed('right'))) {
                // Reset game state if the game is not in the start state and first client presses a button
                tictactoestate.gameState = 'GAME_START';
                tictactoestate.cubes.forEach(cube => {
                    cube.owner = 0; // Reset all cubes to unoccupied
                    cube.color = colors.default; // Reset color
                });
            }
            tictactoestate.player1 = clientID;
            tictactoestate.player2 = clientID;
            if (clients.length >= 2) {
                tictactoestate.player2 = clients[1]; // Second client becom
            }
            getActionValue(); // Get action values from the agent 
            server.broadcastGlobal('tictactoestate');
        }
        
        
        cubeObjects.forEach((cube, index) => {
            if (tictactoestate.gameState !== 'GAME_START') {
                cube.identity()
                    .move(cubeObjects[index].getGlobalMatrix())
                    .scale(cubeSize)
                    .color(...tictactoestate.cubes[index]['color']) // Default color
                    .opacity(tictactoestate.values[index]); // Set opacity based on action value
                return;
            }
            tictactoestate = server.synchronize('tictactoestate'); // Synchronize game state
            let leftHit = lcb.hitRect(cube.getGlobalMatrix());
            let rightHit = rcb.hitRect(cube.getGlobalMatrix());
            let isHit = leftHit || rightHit;
            let canPlay = (tictactoestate.currentPlayer == 1 && clientID == tictactoestate.player1) || (tictactoestate.currentPlayer == -1 && clientID == tictactoestate.player2);

            let cubeState = tictactoestate.cubes[index];
            if (isHit) {
                let leftPressed = inputEvents.isPressed('left');
                let rightPressed = inputEvents.isPressed('right');
                let isPressed = leftPressed || rightPressed;

                if (((leftHit && leftPressed) || (rightHit && rightPressed)) && Boolean(cubeState['owner'] == 0) && canPlay) {
                    console.log('Cube info:', cubeState, 'Pressed:', isPressed, 'Can play:', canPlay, 'index: ', index);
                    // Make a play
                    let newColor = tictactoestate.currentPlayer === 1 ? colors.red : colors.green;
                    cubeState['owner'] = tictactoestate.currentPlayer;
                    cubeState['color'] = newColor;
                    tictactoestate.cubes[index]['owner'] = tictactoestate.currentPlayer;
                    tictactoestate.cubes[index]['color'] = newColor;
                    tictactoestate.currentPlayer = tictactoestate.currentPlayer === 1 ? -1 : 1; // Switch player
                    checkWin(tictactoestate.cubes);


                    cube.identity()
                        .move(cubeState['position']) // Position in grid
                        .scale(cubeSize)
                        .color(...cubeState['color']) // Default color
                        .opacity(tictactoestate.values[index]); // Set opacity based on action value

                    server.broadcastGlobal('tictactoestate');

                } else { // If the cube is unoccupied, increase its size
                    cube.identity()
                        .move(cubeState['position']) // Increased size on hover
                        .scale(cubeSize * 1.2)
                        .color(...cubeState['color']) // Default color
                        .opacity(canPlay ? tictactoestate.values[index]: 1);
                }

            } else {
                cube.identity()
                    .move(cubeState['position']) // Position in grid
                    .scale(cubeSize)
                    .color(...cubeState['color']) // Default color
                    .opacity(canPlay ? tictactoestate.values[index]: 1);  // Set opacity based on action value
            }
        });
        objA.hud().scale(.6);
    });
};
