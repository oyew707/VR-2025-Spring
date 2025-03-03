import { G2 } from "../util/g2.js";
import { matchCurves } from "../render/core/matchCurves.js";
import { buttonState } from "../render/core/controllerInput.js";
import * as cg from "../render/core/cg.js";

export const init = async model => {
 
    let redCount = 3;
    let greenCount = 3;

    let g2A = new G2();
    model.txtrSrc(1, g2A.getCanvas());
    let objA = model.add('square').txtr(1);
 
    model.animate(() => {
        let isPressed = inputEvents.isPressed('right') ?? false;
        // console.log("ispressed: " + isPressed.toString());
        let handpos = isPressed ? inputEvents.pos('right') : [0,0,0];
        // console.log("handpos: " + handpos.toString());
        
        g2A.update();
        objA.identity().move(handpos).scale(.07);

    });
 
    // ANIMATED DRAWING OF A WIGGLY LINE
 
    g2A.render = function() {
       this.setColor([.5,.5,1,.5]);
       this.fillRect(-1,-1,2,2);
 
       this.setColor('yellow');
       this.textHeight(.05);

       let textLines = [
            "Hello",
            "Welcome to the Balloon Game",
            "Pop the balloons to score",
            "Aim controller beam at ",
            "balloon and press it",
            `Red Balls: ${redCount}`,
            `Yellow Balls: ${greenCount}`
        ];
        
        let formattedText = textLines.join("\n");
       this.text(formattedText, 0, .9, 'center');
 

    }
    g2A.addWidget(objA, 'button',  .7, -.8, '#ff8080', 'reset', () => { 
        // Reset the drawing pad
   });

 }
 
 