"""
-------------------------------------------------------
[Program Description]
-------------------------------------------------------
Author:  einsteinoyewole
ID:      [your ID]
Email:   [your email address]
__updated__ = "3/30/25"
-------------------------------------------------------
"""

# Imports
import gym
import tictactoe_gym
import random
import numpy as np
import torch
import torch.nn as nn
from collections import deque
from tictactoe_gym.envs.tictactoe_env import TicTacToeEnv


# Constants

def reset_to_random_state(environment: TicTacToeEnv, num_moves: int = 3):
    """
    -------------------------------------------------------
    Resets the Tic Tac Toe environment to a random state by
    making a specified number of random moves.
    -------------------------------------------------------
    Parameters:
        environment (gym.Env): The Tic Tac Toe environment to reset.
        num_moves (int): The max number of random moves to make (default is 5).
    Returns:
         environment (gym.Env): The Tic Tac Toe environment in a random state.
    -------------------------------------------------------
    """
    environment.reset()
    environment._player = 1 if random.choice([True, False]) else -1
    mvs = random.randint(0, num_moves)  # Random number of moves to make
    for _ in range(mvs):
        available_actions = environment.get_actions()
        if len(available_actions) == 0:
            break  # No more moves possible
        action = np.random.choice(available_actions)
        environment.step(action)
    return environment


class QNetwork(nn.Module):
    """
    -------------------------------------------------------
    QNetwork Class
    -------------------------------------------------------
    Parameters:
        input_size (int): Size of the input layer (default is 9 for Tic Tac Toe)
        hidden_size (int): Size of the hidden layers (default is 36)
        output_size (int): Size of the output layer (default is 9 for Tic Tac Toe)
    -------------------------------------------------------
    """

    def __init__(self, input_size=9, hidden_size=36, output_size=9):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.output = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        """
        -------------------------------------------------------
        Forward pass through the network
        -------------------------------------------------------
        Parameters:
              x (torch.Tensor): Input tensor of shape (batch_size, input_size)
        Returns:
            y_hat (torch.Tensor): Output tensor of shape (batch_size, output_size)
        -------------------------------------------------------
        """
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.output(x)


class ReplayBuffer:
    """
    -------------------------------------------------------
    Stores and samples experiences for reinforcement learning
    -------------------------------------------------------
    """

    def __init__(self, capacity=10000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)  # Use deque for efficient appending and popping

    def add(self, state, action, reward, afterstate, done):
        """
        -------------------------------------------------------
        Adds a new experience to the replay buffer
        -------------------------------------------------------
        Parameters:
            state (np.ndarray): Current state of the environment
            action (int): Action taken
            reward (float): Reward received after taking the action
            afterstate (np.ndarray): State of the environment after taking the action
            done (bool): Whether the episode has ended
        -------------------------------------------------------
        """
        as_valid_actions = afterstate.get_actions() if isinstance(afterstate, TicTacToeEnv) else []
        as_mask = torch.zeros(9)
        as_mask[as_valid_actions] = 1  # Mask for valid actions in the afterstate
        self.buffer.append((state.flatten(), action, reward, afterstate.flatten(), done, as_mask))
        # The buffer will automatically discard the oldest experience if it exceeds capacity

    def sample(self, batch_size):
        """
        -------------------------------------------------------
        [Function Description]
        -------------------------------------------------------
        Parameters:
           [parameter name - parameter description (parameter type and constraints)]
        Returns:
           [return value name - return value description (return value type)]
        -------------------------------------------------------
        """
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, afterstates, dones, as_masks = zip(*batch)
        return (
            torch.FloatTensor(np.array(states)),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(np.array(afterstates)),
            torch.BoolTensor(dones),
            torch.stack(as_masks)  # Concatenate the masks into a single tensor
        )

    def __len__(self):
        return len(self.buffer)


class TicTacToeAgent:
    """
    -------------------------------------------------------
    TicTacToeAgent Class
    -------------------------------------------------------
    Parameters:
        state_size (int): Size of the state representation (default is 9 for Tic Tac Toe)
        action_size (int): Number of possible actions (default is 9 for Tic Tac Toe)
        buffer_capacity (int): Maximum capacity of the replay buffer (default is 10000)
    -------------------------------------------------------
    """

    def __init__(self, state_size=9, action_size=9, buffer_capacity=10000):
        self.state_size = state_size
        self.action_size = action_size
        self.policy_net = QNetwork(input_size=state_size, output_size=action_size)
        self.target_net = QNetwork(input_size=state_size, output_size=action_size)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=1e-4)
        self.replay_buffer = ReplayBuffer(buffer_capacity)
        self.epsilon = 1.0
        self.gamma = 0.99
        self.batch_size = 256
        self.losses = []  # To store loss values for analysis

    def select_action(self, state: torch.Tensor, environment: TicTacToeEnv):
        """
        -------------------------------------------------------
        Select an action based on the current state using the Q-network
        -------------------------------------------------------
        Parameters:
            state (np.ndarray): Current state of the game
            environment (gym.Env): The Tic Tac Toe environment to get available actions
        Returns:
            action (int): Selected action index
        -------------------------------------------------------
        """
        # Epsilon-greedy action selection
        valid_actions = environment.get_actions()  # Get available actions
        if np.random.rand() < self.epsilon:
            action = random.choice(valid_actions)
        else:
            with torch.no_grad():
                q_values = self.policy_net(torch.FloatTensor(state.flatten()))
                # Mask Q-values for unavailable actions
                mask = torch.ones_like(q_values) * -torch.inf
                mask[valid_actions] = 0
                masked_q = q_values + mask
                action = torch.argmax(masked_q).item()
        return action

    def get_state_value(self, state: list):
        """
        -------------------------------------------------------
        Returns state value
        -------------------------------------------------------
        Parameters:
            state (np.ndarray): Current state of the game
        Returns:
            afterstate (np.ndarray): The next state after taking an action
        -------------------------------------------------------
        """
        assert len(state) == self.state_size, "State size must match the agent's state size"
        state_tensor = torch.FloatTensor(state)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
            # Mask Q-values for unavailable actions
            masked_q = torch.where(state_tensor == 0, q_values, -torch.inf)  # Mask invalid actions

        return masked_q

    def _get_opponent_action(self, environment: TicTacToeEnv):
        """
        -------------------------------------------------------
        Simple oppnent action policy that selects a random available action
        -------------------------------------------------------
        Parameters:
            state (np.ndarray): Current state of the game
            environment (gym.Env): The Tic Tac Toe environment to get available actions
        Returns:
            action (int): Selected action index
        -------------------------------------------------------
        """
        action = random.choice(environment.get_actions())
        return action

    def _update_network(self):
        """
        -------------------------------------------------------
        Update the target network with the policy network's weights
        -------------------------------------------------------
        """
        states, actions, rewards, afterstates, dones, as_masks = self.replay_buffer.sample(self.batch_size)

        # Get Double Q-learning targets
        with torch.no_grad():
            next_q = self.target_net(afterstates).max(1)[0]
            targets = rewards + (1 - dones.float()) * self.gamma * next_q

        # Get current Q-values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        loss = nn.MSELoss()(current_q, targets.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.losses.append(loss.item())  # Store the loss for analysis

    def train(self, environment: TicTacToeEnv, num_episodes: int = 10000, target_update: int = 500):
        """
        -------------------------------------------------------
        Train the Tic Tac Toe agent using the specified environment
        -------------------------------------------------------
        """
        self.losses = []  # Reset the losses list for each training session
        for episode in range(num_episodes):
            environment = reset_to_random_state(environment)  # Reset to a random state
            state = environment.get_observation(environment._player)  # Get the initial state
            done = False

            while not done:
                action = self.select_action(state, environment)
                next_state, reward, done, trunc, info = environment.step(action)
                afterstate = next_state

                # # Opponent's move
                # if not done:
                #     opponent_action = self._get_opponent_action(environment)
                #     next_state, _, done, _, info = environment.step(opponent_action)

                # Store experience with afterstate
                self.replay_buffer.add(state, action, reward, afterstate, done)

                state = next_state

                # Train the agent if enough experiences are available
                if len(self.replay_buffer) >= self.batch_size:
                    self._update_network()

            # Update target network periodically
            if episode % target_update == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())

            self.epsilon = max(0.1, self.epsilon * 0.995)  # Decay epsilon
            print(f"Episode {episode + 1}/{num_episodes}")
        return self.losses  # Return the list of losses for analysis


def save_agent(agent: TicTacToeAgent, filename: str):
    """
    -------------------------------------------------------
    [Function Description]
    -------------------------------------------------------
    Parameters:
       [parameter_name - parameter description (parameter_type and constraints)]
    Returns:
       [return value name - return value description (return value type)]
    -------------------------------------------------------
    """
    with open(filename, 'wb') as f:
        torch.save({
            'policy_net_state_dict': agent.policy_net.state_dict(),
            'target_net_state_dict': agent.target_net.state_dict(),
            'optimizer_state_dict': agent.optimizer.state_dict(),
            'epsilon': agent.epsilon,
            'losses': agent.losses
        }, f)


def load_agent(filename: str) -> TicTacToeAgent:
    """
    -------------------------------------------------------
    [Function Description]
    -------------------------------------------------------
    Parameters:
       [parameter_name - parameter description (parameter_type and constraints)]
    Returns:
       [return value name - return value description (return value type)]
    -------------------------------------------------------
    """
    agent = TicTacToeAgent()
    with open(filename, 'rb') as f:
        checkpoint = torch.load(f)
        agent.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        agent.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        agent.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        agent.epsilon = checkpoint['epsilon']
        agent.losses = checkpoint['losses']
    return agent
