import * as cg from "../render/core/cg.js";
import { G3 } from "../util/g3.js";

export const init = async model => {

   let image = new Image();
   image.src = '../media/textures/brick.png';

   let g3 = new G3(model, draw => {
      let N = 30;
      let p = (i,j) => [ .5*(i-N/2) / N, 2.0 + .1 * cg.noise(5*i/N,5*j/N,model.time), .5*(j-N/2) / N ];
      draw.color('#ffffff');
      draw.lineWidth(.0006);
/*
      for (let j = 0 ; j <= N ; j++)
      for (let i = 0 ; i <= N ; i++) {
         let a = p(i,j);
         if (i < N) draw.line(a,p(i+1,j));
         if (j < N) draw.line(a,p(i,j+1));
      }
*/

      draw.color('#004080');
      for (let j = 0 ; j <= N ; j++) {
         let path = [];
         for (let i = 0 ; i <= N ; i++)
	    path.push(p(i,j));
	 draw.draw(path);
      }
      for (let i = 0 ; i <= N ; i++) {
         let path = [];
         for (let j = 0 ; j <= N ; j++)
	    path.push(p(i,j));
	 draw.draw(path);
      }
/*
      draw.lineWidth(.002);

      draw.color('#ffffff');
      draw.line([-.1,1.6,0],[.1,1.6,0]);
      draw.line([-.1,1.6,0],[-.1,1.4,0]);
      draw.line([-.1,1.4,0],[.1,1.4,0]);

      draw.image(image, [0,1.5,.01], 0,0, .3);

      draw.color('#0000ff');

      draw.fill2D([[-.5,-1],[.5,-1],[0,1]],[0,1.5,.01],.2);

      draw.lineWidth(.007);
      draw.draw2D([[-.5,-1],[.5,-1],[0,1],[-.5,-1]],[.2,1.5,.01],.2);

      draw.color('#808080');
      draw.textHeight(.2);
      draw.text('Xy\nXy', [-.12,1.532,0]);

      //draw.color('#ff0000');
      draw.color([1,0,0]);
      draw.lineWidth(.2);
      draw.line([0,1.5,0],[.2,1.5,0]);
*/
      draw.color('#ffffff');
      draw.fill2D([[-1,-1],[1,-1],[1,1],[-1,1]],[0,1.25,.3],.04);
      draw.color('#000000');
      draw.textHeight(.0025);
      //draw.text('This is an example\nof text in our new\nvector based\ngraphics system.', [0,1.25,.3], 'center');
      //draw.text('XXXXXXXXXXXXXXXX', [0,1.25,.3]);
      draw.image(image, [0,1.25,.3], 0,0, .03);
      draw.text('XXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX\nXXXXXXXXXXXXXXXX', [0,1.25,.3]);
/*
      draw.fill([[-.1,1.4,0],[.1,1.4,0],[.1,1.6,0],[-.1,1.6,0]]);
      for (let i = 0 ; i < 20 ; i++)
         draw.fill([p(i,0),p(i+1,0),p(i+1,1),p(i,1)]);

      draw.textHeight(.0005);
      draw.color('yellow');
      for (let j = 0 ; j <= N ; j++)
      for (let i = 0 ; i <= N ; i++)
         draw.text(i+'\n'+j,[(2*i-N)/N/13,1.5+(2*j-N)/N/13,0],'center');
*/
   });
   model.animate(() => {
      g3.update();
   });
}

