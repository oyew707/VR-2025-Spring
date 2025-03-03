import { Diagram } from "../render/core/diagram.js";

export const init = async model => {
   // Create a new diagram
   //            new Diagram(model, textrUnitL, textrUnitR, [x,y,z], scale, draw => { ... });       
   let diagram = new Diagram(model, 0, 1, [0, 0, 0], 1, draw => {
      draw.clear(); // Clear the canvas for every frame

      const k = 5; // Number of petals
      const a = 0.5; // Scale factor
      const points = [];
      const path = [];

      // Generate points for the 3D rose
      for (let theta = 0; theta < 2 * Math.PI; theta += 0.1) {
         for (let phi = 0; phi < Math.PI; phi += 0.1) {
            const r = a * Math.sin(k * theta);
            const x = r * Math.sin(phi) * Math.cos(theta);
            const y = r * Math.sin(phi) * Math.sin(theta);
            const z = r * Math.cos(phi);
            points.push([x, y, z]);
         }
      }

      // Create a path by connecting consecutive points
      for (let i = 0; i < points.length - 1; i++) {
         path.push(points[i]);
         path.push(points[i + 1]);
      }

      // Draw the rose shape using lines
      path.forEach((point, index) => {
         if (index < path.length - 1) {
            draw.line(point, path[index + 1]); // Draw a line between consecutive points
         }
      });

      draw.setColor('red'); // Set the color of the rose diagram
   });

   // Animate the diagram
   model.animate(() => {
      diagram.update();
   });
};

