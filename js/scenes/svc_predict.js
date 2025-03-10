import * as cg from "../render/core/cg.js";
import { G2 } from "../util/g2.js";
import { lcb, rcb } from '../handle_scenes.js';
import { getRandomArbitrary, svc_url, getColor, predict } from "../util/svc_util.js";
import { buttonState } from "../render/core/controllerInput.js";

async function generateParticles(numParticles) {
    let particles = [];
    for (let i = 0; i < numParticles; i++) {
        let x = getRandomArbitrary(0, 0.5);
        let y = getRandomArbitrary(0, 0.5);
        let z = getRandomArbitrary(0, 0.5);
        let classLabel = await predict(x, y, z);
        let color = getColor(classLabel);
        particles.push({
            p: [x, y, z],
            s: .01,
            c: color,
        });
    }
    return particles;
}

export const init = async model => {
    model.txtrSrc(2, 'media/textures/disk.jpg');
    let N = 100;
    let particles = model.add('particles').info(N).txtr(2).flag('uTransparentTexture').scale(2);
    let random_data = await generateParticles(N);
    console.log("Random data", random_data.length, random_data[0]);
    particles.setParticles(random_data);

    let L = {}, R = {}; 

    inputEvents.onPress   = hand => (hand=='left' ? L : R).isDown = true;         // Track when a trigger is pressed //
    inputEvents.onRelease = hand => (hand=='left' ? L : R).isDown = false;

    model.move(0,0.5,-1.5).animate(() => {
        // for (let b = 0 ; b < 6 ; b++) {
        //     L.isB[b] = buttonState.left [b].pressed;
        //     R.isB[b] = buttonState.right[b].pressed;
        // }
        for (let n = 0 ; n < N; n++) {                                            //                                 //
            let select = L.index == n || R.index == n;                              // While a tile is at a controller //
            random_data[n].s = select ? 0.1 : .0s1;                                         // Make it bigger       //         
        }

        particles.setParticles(random_data);

        // Ray/Triangle Intersection, Source wordcloud2
        let mesh = clay.formMesh('particles,' + particles.getInfo());              //                                 //
        if (mesh) {                                                                // Use the inverse of the object's //
            let invMatrix = cg.mInverse(particles.getGlobalMatrix());               // matrix to transform the ray.    //
                                                                                    // This is much more efficient     //
            let initRay = ray => {                                                  // than using the forward matrix   //
            let m = (ray == L ? lcb : rcb).beamMatrix();                         // to transform every tile.        //
            ray.V = cg.mTransform(invMatrix, [m[12], m[13], m[14]]);             //                                 //
            ray.W = cg.mTransform(invMatrix, [-m[8],-m[9],-m[10],0]).slice(0,3); // Initialize the ray's V and W    //
            ray.V = cg.add(ray.V, cg.scale(ray.W, 0.11));                        // and set the ray index to -1,    //
            if (! ray.isDown || ray.index < 0) {                                 // indicating that it has not yet  //
                ray.index = -1;                                                   // hit any tiles.                  //
                ray.t = 1000;                                                     //                                 //
            }                                                                    //                                 //
            if (ray.isDragging = ray.index >= 0 && ray.wasDown && ray.isDown) {  // If either controller is already //
                let p = cg.add(ray.V, cg.scale(ray.W, ray.t));                    // dragging a tile, then just move //
                random_data[ray.index].p = p;                                            // that tile, and send a message   //
                console.log("Predicting", random_data[ray.index].p[0], random_data[ray.index].p[1], random_data[ray.index].p[2]);
                let pred = predict(random_data[ray.index].p[0], random_data[ray.index].p[1], random_data[ray.index].p[2]); 
                random_data[ray.index].c = getColor(pred);                           // to the server to update the     //
            }                                                                    // the tile's new position.        //
            }                                                                       //                                 //
            initRay(L);                                                             //                                 //
            initRay(R);                                                             //                                 //
                                                                                    //                                 //
            if (! L.isDragging || ! R.isDragging) {                                  // If either controller is not     //
                for (let n = 0 ; n < mesh.length ; n += 3*16) {                      // dragging a tile, then find the  //
                    let A = [ mesh[   n], mesh[   n+1], mesh[   n+2] ],               // nearest tile, if any, that the  //
                        B = [ mesh[16+n], mesh[16+n+1], mesh[16+n+2] ],               // controller ray intersects.      //
                        C = [ mesh[32+n], mesh[32+n+1], mesh[32+n+2] ];               //                                 //
                    let testRay = ray => {                                            // To do this, do a ray/triangle   //
                        if (! ray.isDragging) {                                        // intersection with both of the   //
                            let t = cg.rayIntersectTriangle(ray.V, ray.W, A, B, C);     // tile's two component triangles. //
                            if (t > 0 && t < ray.t) {                                   //                                 //
                            ray.t = t;                                               // When finished, the ray contains //
                            ray.index = mesh.order[n / (3*16) >> 1];                 // the index and distance of the   //
                            }                                                           // nearest tile it intersects.     //
                        }                                                              //                                 //
                    }                                                                 //                                 //
                    testRay(L);                                                       //                                 //
                    testRay(R);                                                       //                                 //
                }                                                                    //                                 //
            }                                                                          //                                 // 
        }
        L.wasDown = L.isDown;                                                      // Remember the previous trigger   //
        R.wasDown = R.isDown; 
    });
}