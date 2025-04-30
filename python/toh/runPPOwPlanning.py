"""
-------------------------------------------------------
Runs a PPO agent on the Tower of Hanoi environment.
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "4/30/25"
-------------------------------------------------------
"""


# Imports
from gymnasium_env.envs import TowerOfHanoiEnvVR
from ppo import PPO
import time
import torch
import numpy as np
import random
import os

# Constants
SEED = 4
torch.manual_seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

# Env hyperparameters
action_std = 0.2                    # starting std for action distribution (Multivariate Normal)
action_std_decay_rate = 0.01        # linearly decay action_std (action_std = action_std - action_std_decay_rate)
min_action_std = 0.1                # minimum action_std (stop decay after action_std <= min_action_std)
action_std_decay_freq = int(2.5e1)  # action_std decay frequency (in num timesteps)
max_episodes = 10                   # max training episodes
max_ep_len = 6000                   # max timesteps in one episode

# PPO hyperparameters
cont_action_dim = 3
binary_action_dim = 1
K_epochs = 80           # update policy for K_epochs (K_epochs = 80)
eps_clip = 0.2          # clip parameter for PPO
gamma = 0.99            # discount factor
lr_actor = 0.0003       # learning rate for actor head
lr_critic = 0.001       # learning rate for critic head , shared parameters is min of both

# Initialize the environment
env = TowerOfHanoiEnvVR()

# Reset the environment
observation, info = env.reset()
print(f"{info=}")

# Initialize the PPO agent
ppo_agent = PPO(

    cont_action_dim=cont_action_dim,
    binary_action_dim=binary_action_dim,
    eps_clip=eps_clip,
    gamma=gamma,
    lr_actor=lr_actor,
    lr_critic=lr_critic,
    K_epochs=K_epochs,
    use_mcts=True,
    action_std_init=action_std,
    iterationLimit=24
)

for ep in range(max_episodes):
    # Reset the environment
    observation, info = env.reset()

    # Initialize variables
    done = False
    score = 0
    step = 0
    prev_action = torch.tensor([0, 0, 0, 1])

    for t in range(max_ep_len):
        # Select action
        action = ppo_agent.select_action(observation, env._get_info(), prev_action)

        typea = 2  # Actions for right controller
        pos_change = action[:3]
        orientation_change = [0, 0, 0, 1]
        button = bool(action[3])

        # Take action in the environment
        observation, reward, terminated, truncated, info = env.step(typea, pos_change, orientation_change, button)

        # Store transition in PPO agent
        ppo_agent.buffer.rewards.append(reward)
        ppo_agent.buffer.is_terminals.append(terminated)

        # Update score and step count
        score += reward
        step += 1
        prev_action = action if isinstance(action, torch.Tensor) else torch.tensor(action)

        if terminated or truncated:
            break

        if t % action_std_decay_freq == 0:
            # Decay action std
            ppo_agent.decay_action_std(action_std_decay_rate, min_action_std)
        if t % 100 == 0:
            # Print progress every 100 steps
            print(f"Episode {ep + 1}/{max_episodes} - Step {t} - Action Std: {ppo_agent.action_std}")
    print(f"\nEpisode {ep + 1}/{max_episodes} - Score: {score} - Steps: {step}\n")
    print('-'*50)

    # Update PPO agent after each episode
    ppo_agent.update()

    print(f"Episode {ep + 1}/{max_episodes} - Score: {score} - Steps: {step}")

# Save the model
ppo_agent.save(f"./ppo_hanoi_{int(time.time())}.pth")

# Clean up
ppo_agent.planner.simulator.close()
env.close()
