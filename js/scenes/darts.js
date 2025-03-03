import { G2 } from "../util/g2.js";
import * as cg from "../render/core/cg.js";

window.dartState = {
    color: [0.8, 0.8, 0.8],  // Light gray
    position: [0, 1.6, -1],  // Default position
    isFlying: false,
    targetPosition: [0, 1.6, -2],  // Default target position
    speed: 0,
    score: 0,
};



export const init = async model => {
    const createDart = () => {
        let dart = model.add('tubeZ'); 

        return dart;
    };

    const createTarget = () => {
        let target = model.add();
        let circles = []; // Store the circle objects
        
        const circleSizes = [0.03, 0.06, 0.09, 0.12, 0.15];  // [0.05, 0.15, 0.25, 0.35, 0.45]
        circleSizes.reverse().forEach((size, i, arr) => {            
            let col = target.add('tubeZ')
                        // .identity()
                        .scale(size, size, 0.001)  // Z-axis flattening
                        .color(1, i % 2 ? 0 : 1, i % 2 ? 0 : 1) // White if even, red else
                        // .move(...dartState.targetPosition);
            circles.push({
                object: col,
                size: size,
                score: (i+1) * 2 // Assign decreasing score values (10, 8, 6, 4, 2)
                }); // Store circle info
        });

        return {
            target: target,
            circles: circles // Return both the target and the circles
        };
    };

    const dart = createDart();
    const targetdt = createTarget()
    const target = targetdt.target; // Get the target object
    const circles = targetdt.circles.reverse(); // Get the circles from the target object


    let scoreG2 = new G2(false, 512, 128); // G2 instance for the score
    let instructionG2 = new G2(true, 512, 128); // G2 instance for instructions

    // Instruction texture
    model.txtrSrc(1, instructionG2.getCanvas()); // Use texture unit 1
    let instructionObj = model.add('square').txtr(1); // Use texture unit 1


    // Score texture
    model.txtrSrc(2, scoreG2.getCanvas()); // Use texture unit 2
    let scoreObj = model.add('square').txtr(2); // Use texture unit 2

    // Input event handlers
    inputEvents.onPress = hand => {
        dartState.color = hand === 'left' ? [0, 1, 0] : [0, 0, 1];  // Green for left, blue for right
        dartState.isFlying = false;
        dartState.position = inputEvents.pos(hand);
        server.broadcastGlobal('dartState');
    };

    inputEvents.onDrag = hand => {
        dartState.color = hand === 'left' ? [0, 1, 0] : [0, 0, 1];  // Green for left, blue for right
        dartState.isFlying = false;
        dartState.position = inputEvents.pos(hand);
        server.broadcastGlobal('dartState');     
     }

    inputEvents.onRelease = hand => {
        dartState.color = [0.25, 0, 0.8];  // black color when flying
        dartState.isFlying = true;
        dartState.speed = Math.random() * 0.01 + 0.05;  // Random speed
        server.broadcastGlobal('dartState');
    };

    model.animate(() => {
        dartState = server.synchronize('dartState'); // BEGIN ANIMATE BY SYNCHRONIZING STATE.
        // Set dart position
        dart.identity()
            .move(...dartState.position)
            .scale(0.01, 0.01, 0.1)  //  1cm thick (x and y) and 10cm long (z)
            .color(...dartState.color);

        // Handle throwing/ flight
        if (dartState.isFlying) {
            const speed = dartState.speed * 0.6;

            // Update only Z position
            dartState.position[2] -= speed;

            // // Aim the dart towards the target
            // dart.aimZ([0, 0, -1]);

            const dx = dartState.position[0] - dartState.targetPosition[0];
            const dy = dartState.position[1] - dartState.targetPosition[1];
            const distanceSquared = dx * dx + dy * dy;
            // Reset if past target plus a bit
            if (dartState.position[2] < dartState.targetPosition[2] - 0.5 || dartState.speed <= 0) {
                // Award points based on distance from target
                let points = 0;

                for (let circle of circles) {
                    // Check if the dart is within the target's range
                    if (distanceSquared <= circle.size ** 2) {
                        // The dart is within the target's radius
                        points = circle.score;
                        console.log(`Hit circle with score ${points} at position ${circle.size}`);
                        break;
                    }

                };
                
                dartState.score += points;
                dartState.position = [0, 1.6, -1];  // Reset and position dart at eye level
                dartState.isFlying = false;
                dartState.color = [0.8, 0.8, 0.8];  // Reset to initial color
            }
        }



    instructionG2.setColor([1,0,0]);
    instructionG2.textHeight(.15);
    instructionG2.setFont('sans-serif');
    instructionG2.text("Throw darts at bullseye!", 0, 0);

    // Update score display
    scoreG2.clear(); // Clear the previous score
    scoreG2.setColor([1,0,0]);
    scoreG2.textHeight(.08);
    scoreG2.setFont('Arial');

    scoreG2.text('Score = ' + dartState.score, 0, 0, 'left');
    scoreG2.update(); // Update the g2 canvas

    scoreObj.identity().move(1.5,1.5,-1).scale(0.8, 0.3, 1);
    instructionObj.identity().move(0.5,1.7,-1).scale(1.6, 0.6, 1);// Set instruction position

    target.identity().move(...dartState.targetPosition);  // Set target position
});
}
