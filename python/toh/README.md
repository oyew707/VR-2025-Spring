
# Tower of Hanoi Gym Environment

This repository contains a custom Gymnasium environment for simulating a Virtual Reality (VR) version of the Tower of Hanoi puzzle. The environment is designed to work with the Gymnasium framework and provides a flexible interface for interacting with the VR environment.

---

## Quick Overview

- **Environments**
  - `gymnasium_envs/gymnasium_env/envs/towerOfHanoi.py`: Classic, tabular Tower of Hanoi environment (discrete state/action).
  - `gymnasium_envs/gymnasium_env/envs/towerOfHanoiVR.py`: VR-based environment with image observations and continuous actions.
  - `gymnasium_envs/gymnasium_env/envs/towerOfHanoiSim.py`: Simulator for planning and state manipulation.

- **RL Algorithms**
  - `runDQN.py`: Trains a DQN agent on the classic environment.
  - `runPPO.py`: Trains a PPO agent on the VR environment using image observations.
  - `runPPOwPlanning.py`: Trains a PPO agent with integrated planning (MCTS) and rule guidance.

- **Planning and Models**
  - `planner.py`: Implements Monte Carlo Tree Search (MCTS) for planning, using a DQN agent and a CNN state extractor.
  - `ppo.py`: Custom PPO implementation supporting hybrid action spaces and MCTS-based action selection.

---

## Features

- **Observation Space**: The environment captures screenshots of the VR environment as observations.
- **Action Space**: Supports continuous movement for the headset and controllers, as well as discrete button states.
- **VR Integration**: Interacts with a VR environment through a browser-based WebXR interface.
- **Extendable**: Easily modify the reward function and termination conditions to suit your use case.

## Installation

- To install the environment, clone the repository and follow the setup described [here](https://github.com/oyew707/VR-2025-Spring/tree/tower_hanoi#how-to-setup-the-environment).
- Checkout the `tower_hanoi` branch for the Tower of Hanoi environment.
- Make sure to install the required dependencies for the Python environment:
```bash
cd python/toh
pip install -r requirements.txt
```
- Start the VR server:
```bash
cd ../../
./startserver
```
- Train Agents
```
python runDQN.py #DQN (on array representation)
python runPPO.py #(PPO (VR))
python runPPOwPlanning.py #(PPO + Planning)
```

## Usage
Below is an example of how to use the Tower of Hanoi environment in a Python script. This example demonstrates how to reset the environment, take random actions, and print the results.

```python
import numpy as np
from gymnasium_envs.gymnasium_env.envs.towerOfHanoiVR import TowerOfHanoiEnv

# Initialize the environment
env = TowerOfHanoiEnv()

# Reset the environment
observation, info = env.reset()

# Perform random actions in the environment
for _ in range(10):  # Perform 10 random steps
    # Sample a random action
    random_action = env.action_space.sample()

    # Perform the action
    observation, reward, terminated, truncated, info = env.step(
        action=np.random.choice([0, 1, 2]),  # Randomly choose an action (headset, left, right)
        change_position=np.random.uniform(-1, 1, size=3),  # Random position change
        change_orientation=np.random.uniform(-np.pi, np.pi, size=4),  # Random orientation change
        button=np.random.choice([True, False])  # Random button press/release
    )

    # Print the results
    print(f"Observation: {observation.shape}, Reward: {reward}, Terminated: {terminated}, Info: {info}")

    if terminated:
        print("Episode terminated.")
        break

# Close the environment
env.close()
```

## Notes
- The VR environment requires a running VR server and browser integration.
- RL code is modular and can be adapted for specific implementation goals.
- For more details on the VR setup, see the main project README.