import * as cg from "../render/core/cg.js";
import { loadPredictions } from "./data_HW4.js"; // Import function to load predictions

export const init = async model => {
    // 🎯 **Load Predictions**
    let predictions = await loadPredictions(); // Load predictions from JSON
    let firstFrame = predictions[0]; // Get first frame

    // 🎯 **Render First 3 Points**
    let sphere1 = model.add('sphere').move(firstFrame[0][0], firstFrame[0][1], firstFrame[0][2]).scale(0.2).color(1, 0, 0);  // Red
    let sphere2 = model.add('sphere').move(firstFrame[1][0], firstFrame[1][1], firstFrame[1][2]).scale(0.2).color(0, 1, 0);  // Green
    let sphere3 = model.add('sphere').move(firstFrame[2][0], firstFrame[2][1], firstFrame[2][2]).scale(0.2).color(0, 0, 1);  // Blue
};
