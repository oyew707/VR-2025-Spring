"""
-------------------------------------------------------
[Program Description]
-------------------------------------------------------
Author:  einsteinoyewole
ID:      [your ID]
Email:   [your email address]
__updated__ = "3/31/25"
-------------------------------------------------------
"""
import torch
# Imports
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from train import load_agent

# Constants
ttt_agent = load_agent('tictactoe_ddqn.pth')
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://192.168.68.103:2024", "http://localhost:2024", "http://10.19.170.217:2024", "http://10.19.152.41:2024"],
        "methods": ["GET", "POST", "PUT", "OPTIONS"],  # Explicit methods
        "allow_headers": ["Content-Type"]  # Required for JSON requests
    }
})

@app.route('/get_state_values', methods=['POST', 'OPTIONS'])
@cross_origin()
def get_state_val():
    """
    -------------------------------------------------------
    Returns the values of actions given a state of tic tac toe.
    -------------------------------------------------------
    """
    params = request.json
    state = params['state']
    values = ttt_agent.get_state_value(state)
    # Ensure the values are in the correct format
    values = [float(value) if not torch.isinf(value) else -1000 for value in values]
    print(f"State: {state} Values: {values}")
    return jsonify(values)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=3000)
