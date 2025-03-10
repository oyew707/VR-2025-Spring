"""
-------------------------------------------------------
Flask server for SVC model training and iris dataset retrieval.
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "3/2/25"
-------------------------------------------------------
"""

# Imports
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from model import get_iris_data, train_svc, reset, get_mesh_decision, svc_predict
from threading import Lock

# Constants
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://192.168.68.103:2024", "http://localhost:2024", "http://10.19.170.217:2024"],
        "methods": ["GET", "POST", "PUT", "OPTIONS"],  # Explicit methods
        "allow_headers": ["Content-Type"]  # Required for JSON requests
    }
})
lock = Lock()


@app.route('/train_svc', methods=['POST', 'OPTIONS'])
@cross_origin()
def train_req():
    """
    -------------------------------------------------------
    Trains the SVC model with the POST parameters.
    -------------------------------------------------------
    Returns:
       result - The result of the training process (JSON)
            - Contains the decision boundary, support vectors   and accuracy metrics

    -------------------------------------------------------
    """
    params = request.json
    # Check if the server is busy, if so return 503
    if not lock.acquire(blocking=False):
        return jsonify({"error": "Server is busy"}), 503
    try:
        result = train_svc(
            C=params.get('C'),
            kernel=params.get('kernel'),
            degree=params.get('degree'),
            gamma=params.get('gamma'),
            tol=params.get('tol'),
            max_iter=params['max_iter']
        )
        result['decision_boundary'] = result['decision_boundary'].to_dict(orient='records')
    finally:
        lock.release()
    return jsonify(result)


@app.route('/get_iris_data', methods=['GET', 'OPTIONS'])
@cross_origin()
def iris_data_req():
    """
    -------------------------------------------------------
    Returns the iris dataset in 3D space for visualization.
    -------------------------------------------------------
    """
    iris_data = get_iris_data()
    return jsonify(iris_data.to_dict(orient='records'))


@app.route('/get_mesh_data', methods=['GET', 'OPTIONS'])
@cross_origin()
def mesh_data_req():
    """
    -------------------------------------------------------
    Returns the mesh dataset in 3D space for visualization.
    -------------------------------------------------------
    """
    mesh_data = get_mesh_decision()
    return jsonify(mesh_data.to_dict(orient='records'))


@app.route('/reset', methods=['PUT', 'POST', 'OPTIONS'])
@cross_origin()
def reset_req():
    """
    -------------------------------------------------------
    Resets the SVC model and iris data and grid.
    -------------------------------------------------------
    """
    params = request.json
    reset(**params)
    return jsonify({})

@app.route('/predict', methods=['POST', 'OPTIONS'])
@cross_origin()
def predict_req():
    """
    -------------------------------------------------------
    Predicts the target value for a given set of features.
    -------------------------------------------------------
    Returns:
       result - The predicted target value (JSON)
    -------------------------------------------------------
    """
    params = request.json
    x = params.get('x')
    y = params.get('y')
    z = params.get('z')

    if x is None or y is None or z is None:
        return jsonify({"error": "Missing parameters"}), 400

    # Convert to df (as we trained with df)
    df = pd.DataFrame([[x, y, z]], columns=['x', 'y', 'z'])

    # Predict the target value
    prediction = int(svc_predict(df)[0])
    print(f"Prediction: {prediction}")
    return jsonify({"prediction": prediction})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=3000)
