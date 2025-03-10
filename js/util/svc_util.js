// Contains utility functions for the service layer for SVC model
export const svc_url = `${window.location.protocol}//${window.location.hostname}:3000`;

// Generates random data in the range of min and max
export function getRandomArbitrary(min, max) {
    // Source: https://shorturl.at/p57Rg
    return Math.random() * (max - min) + min;
}


export function getColor(classLabel) {
    if (classLabel  == null){
        return [0.5, 0.5, 0.5, 0.2]; // grey
    }
    let color = classLabel == 0 ? [1,0,0, 0.2] : (classLabel == 1 ? [0,1,0, 0.2] : [0,0,1, 0.2]); 
    return color;
}

// Resets the SVC model
export async function resetModel(params) {
    const response = await fetch(`${svc_url}/reset`, {
        method: 'POST',
        // mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    });
    const result = await response.json();

    return result;
}

// Returns the iris dataset in 3D space for visualization from SVC server
export async function getIrisData() {
    const response = await fetch(`${svc_url}/get_iris_data`, {
        method: 'GET',
        // mode: 'no-cors'
    });
    const result = await response.json();

    return result;
}

export async function predict(x, y, z) {
    const response = await fetch(`${svc_url}/predict`, {
        method: 'POST',
        // mode: 'no-cors',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'x': x,
            'y': y,
            'z': z
        })
    });
    if (!response.ok) {
        console.error('There was a problem with the fetch operation:', response.status);
        return null;
    }
    const result = await response.json();
    if ( !(0 <= result['prediction'] <= 3)) {
        console.error('Invalid prediction:', result['prediction']);
        return null;
    }
    return result['prediction'];
}
