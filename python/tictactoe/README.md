# Tic Tac Toe VR Game

This project is a VR-based Tic Tac Toe game where players interact with a 3x3 grid of cubes in a virtual space. Players take turns selecting cubes by aiming and pressing a controller button when the beam intersects a cube. The game is powered by a reinforcement learning (RL) agent that evaluates game states and provides action values.

---

## How to Start the Game

1. **Set Up the Python Server**:
   - Navigate to the `python/tictactoe` directory.
   - Start the RL agent server by running:
     ```sh
     python rlagent.py
     ```

2. **Start the VR Server**:
   - At the root of the project, run:
     ```sh
     ./startserver
     ```

3. **Access the Game**:
   - Open a browser and navigate to:
     - `http://localhost:2024` (if running locally), or
     - `http://[server-ip]:2024` (if accessing remotely).

---

## Game Mechanics

- **Objective**: Be the first player to align three cubes in a row, column, or diagonal.
- **Player Interaction**:
  - Players use VR controllers to aim at cubes on the 3x3 grid.
  - A beam from the controller highlights the cube being targeted.
  - Press the controller button to select a cube.
  - The cube changes color to indicate ownership:
    - **Red**: Player 1
    - **Green**: Player 2
  - Press down on the joystick (alt press) to reset when the game is in a terminal state.
- **Turn-Based Gameplay**:
  - Players alternate turns.
  - The game checks for a win or draw after each move.
  - The RL agent suggests moves for whoever is playing based on opacity.
- **Game States**:
  - **Game Start**: The game begins with an empty grid.
  - **Player Win**: A player wins by aligning three cubes.
  - **Draw**: The game ends in a draw if all cubes are filled without a winner.

---

## Reinforcement Learning Agent

The game is powered by a Double Deep Q-Network (DDQN) RL agent. The agent was trained to evaluate game states and provide action values for optimal moves. Below is a brief overview of the RL agent:

- **Architecture**:
  - The agent uses a neural network (`QNetwork`) with two hidden layers to approximate Q-values for each possible action.
  - The network takes the current game state as input and outputs Q-values for all possible actions.

- **Training**:
  - The agent was trained using a replay buffer to store experiences (state, action, reward, next state).
  - The agent uses Double Q-learning to reduce overestimation of Q-values.
  - The training process involves:
    - Selecting actions using an epsilon-greedy policy.
    - Updating the Q-network using the Mean Squared Error (MSE) loss between predicted and target Q-values.

- **Deployment**:
  - The trained agent is loaded from a checkpoint (`tictactoe_ddqn.pth`) and serves action values via the `/get_state_values` API endpoint.

