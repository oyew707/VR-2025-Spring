# RLiVR (Tower of Hanoi)

This repository contains a custom Gymnasium environment for simulating a Virtual Reality (VR) version of the Tower of Hanoi puzzle. The environment is designed to work with the Gymnasium framework and provides a flexible interface for interacting with the VR environment.

## The Game
The challenge involves moving multiple disks from a starting peg to a goal peg. The agent must find the optimal strategy with the minimum number of moves , strictly adhering to the rule that a larger disk may never be placed on top of a smaller one.

## Architecture & Methodology
Our solution utilizes Hierarchical RL, splitting the problem into high-level planning and low-level control.

- **VR Integration**: The 3D interactive environment is built using WebXR. The custom Gym environment uses Selenium browser automation and Meta’s Immersive Web Emulator to allow the RL agent to interact. Users and agents interact by grabbing a disc, moving it above a tower, and dropping it.
- **Planning/Learning Strategy (The Brain)**: We trained a Deep Q-Network (DQN) model using stable-baselines3 to understand the core game logic. It uses a disc-peg state representation and a restricted action space of six allowed moves.
- **Learning RL Control (The "Movement")**: We used Policy Gradient Methods (PPO) for low-level continuous control of Oculus controllers (pose + grip). The action space consists of 7-DOF hand movements and a controller button to pick up and drop disks.
- We also created an environment where the agent moves discs without controllers. A trained Convolutional Neural Network (CNN) maps raw VR observations to the internal disc-peg state representations, bridging raw pixels to high-level planning.

## Demos & Results
With the reward shaping implemented, we observed increased rewards as the agent explored closer to the needed discs, eventually successfully grabbing the first disc (though some drift issues remain during target positioning).
- Learning the Game Strategy (DQN):

<video src="https://github.com/user-attachments/assets/978ee31f-a305-4f62-bb7d-ada894374e93" controls="controls" style="max-width: 100%;">
</video>


- VR Movements + RL Control

<video src="https://github.com/user-attachments/assets/e2bc0297-edd8-4d3f-99e0-52e2566a4d04" controls="controls" style="max-width: 100%;">
</video>






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

## Usage
Below is an example of how to use the Tower of Hanoi environment in a Python script. This example demonstrates how to reset the environment, take random actions, and print the results.
```python
import numpy as np
from gymnasium_envs.gymnasium_env.envs.towerOfHanoi import TowerOfHanoiEnv

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

