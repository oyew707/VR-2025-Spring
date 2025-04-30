"""
-------------------------------------------------------
Implements Monte Carlo Tree Search (MCTS) for the Tower of Hanoi game.
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "4/29/25"
-------------------------------------------------------
"""

# Imports
from copy import deepcopy
import numpy as np
from PIL import Image
import torch
import os
from typing import Union, TypedDict, Self
import gymnasium as gym
from gymnasium_envs.gymnasium_env.envs.towerOfHanoiSim import TowerOfHanoiEnvSim, StateType
from gymnasium_envs.gymnasium_env.envs.towerOfHanoiVR import Actions
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3 import DQN
from tqdm import tqdm

# Constants
torch.manual_seed(4)
CNN_EXTRACTOR_MODEL = "nn_models/state_extractor.pth"
TOH_GAME_MODEL = "nn_models/dqn_hanoi_4_disks.zip"


class ImageDataset(Dataset):
    """
    -------------------------------------------------------
    Load images from a directory and apply transformations.
    -------------------------------------------------------
    Parameters:
        image_dir (str): Directory with all the images.
        transform (callable, optional): Optional transform to be applied on an image.
        target_transform (callable): Should convert the target to a tensor.
        num_repeats (int): Number of times to repeat the dataset.
    -------------------------------------------------------
    """

    def __init__(self, image_dir, target_transform=None, transform=None, num_repeats=10):
        self.image_dir = image_dir
        self.num_repeats = num_repeats
        self.image_filenames = [f for f in os.listdir(image_dir) if f.endswith('.png') or f.endswith('.jpg')]
        self.box = (775, 472, 1630, 858)
        self.target_transform = target_transform
        self.transform = transform

    def __len__(self):
        """
        -------------------------------------------------------
        Returns the number of images in the dataset.
        -------------------------------------------------------
        Returns:
            len: Number of images in the dataset (int)
        -------------------------------------------------------
        """
        return len(self.image_filenames) * self.num_repeats

    def __getitem__(self, idx):
        """
        -------------------------------------------------------
        Load an image and its corresponding target.
        -------------------------------------------------------
        Parameters:
           idx : Index of the image to load (int)
        Returns:
            cropped_image: Transformed image (PIL Image)
            target: Target label (torch.Tensor)
        -------------------------------------------------------
        """
        idx = idx % len(self.image_filenames)  # Repeat the dataset
        # Load image
        img_name = self.image_filenames[idx]
        img_path = os.path.join(self.image_dir, img_name)
        image = Image.open(img_path)
        # Crop image
        cropped_image = image.crop(self.box)

        if self.transform:
            cropped_image = self.transform(cropped_image)

        label_str = img_name.split('_', 1)[1].rsplit('.', 1)[0]
        label_list = eval(label_str)
        if self.target_transform:
            label_list = self.target_transform(label_list)
        else:
            label_list = torch.tensor(label_list[::-1], dtype=torch.long)

        return cropped_image, label_list


class CNNStateLearner(nn.Module):
    """
    -------------------------------------------------------
    CNN model for learning the state of the Tower of Hanoi game.
    -------------------------------------------------------
    Parameters:
        num_pegs (int): Number of pegs in the game.
        num_disks (int): Number of disks in the game.
    """

    def __init__(self, num_pegs, num_disks):
        super(CNNStateLearner, self).__init__()
        self.num_pegs = num_pegs
        self.num_disks = num_disks

        self.cnn = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.linear_layers = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 28 * 62, 512),  # Much smaller input size!
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, num_pegs * num_disks)
        )

    def forward(self, X):
        """
        -------------------------------------------------------
        Forward pass through the CNN model.
        -------------------------------------------------------
        Parameters:
            X - Input tensor (torch.Tensor)
        Returns:
            output - Output tensor (torch.Tensor (batch_size, num_pegs, num_disks))
        -------------------------------------------------------
        """
        # Pass through CNN layers
        X = self.cnn(X)
        # Pass through linear layers
        output = self.linear_layers(X)
        # Reshape output to (batch_size, num_pegs, num_disks)
        output = output.view(-1, self.num_pegs, self.num_disks)
        # probabilities = F.softmax(output, dim=-1)  # Apply softmax to get probabilities across pegs
        return output


class StateNode():
    """
    -------------------------------------------------------
    Node in the Monte Carlo Tree Search (MCTS) for Tower of Hanoi.
    -------------------------------------------------------
    Parameters:
        state (StateType): Current state of the game.
        parent (StateNode): Parent node in the MCTS tree.
        action_pos (np.ndarray): Change in position from parent to current state.
        action_button (bool): Action button pressed.
    -------------------------------------------------------
    """

    def __init__(self, state: StateType, parent: Self = None, action_pos: np.ndarray = None,
                 action_button: bool = False):
        self.state = state
        self.parent = parent
        action_pos = [0,0,0] if action_pos is None else action_pos
        self.action = torch.cat([torch.tensor(action_pos), torch.tensor([int(action_button)])])
        self.children = {}
        self.visits = 0
        self.cumulative_rewards = 0
        self.isTerminal = state['isterminal']

    def __str__(self):
        """
        -------------------------------------------------------
        String representation of the StateNode.
        -------------------------------------------------------
        Returns:
            str: String representation of the node.
        -------------------------------------------------------
        """
        s = []
        s.append("totalReward: %s" % self.cumulative_rewards)
        s.append("numVisits: %d" % self.visits)
        s.append("possibleActions: %s" % (self.children.keys()))
        return "%s: {%s}" % (self.__class__.__name__, ', '.join(s))


class TowerOfHanoiPlanner:
    """
    -------------------------------------------------------
    Implement Monte Carlo Tree Search (MCTS) for the Tower of Hanoi game.
    Source: https://shorturl.at/8d6AM
        Modified for Tower of Hanoi VR env.
    -------------------------------------------------------
    Parameters:
        rolloutPolicy (DQN): Policy for the rollout phase(gives rewards).
        iterationLimit (int): Maximum number of iterations for MCTS.
        explorationConstant (float): Exploration constant for UCT.
        rollout_state_extractor (str): Path to the CNN state extractor model.
        num_disks (int): Number of disks in the game.
        num_pegs (int): Number of pegs in the game.
        actionPolicy (PPO): Policy for the selecting actions.
    -------------------------------------------------------
    """
    image_transform = T.Compose([
        T.Resize(224),
        T.ToTensor(),
        T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    max_number_of_actions = 6

    def __init__(self, rolloutPolicy: DQN, iterationLimit: int = 20,
                 explorationConstant: float = 1 / np.sqrt(2),
                 rollout_state_extractor: str = CNN_EXTRACTOR_MODEL, num_disks: int = 4, num_pegs: int = 3,
                 simulator: TowerOfHanoiEnvSim = TowerOfHanoiEnvSim()
                 ):
        assert iterationLimit > 0, "Iteration limit must be greater than 0"
        assert explorationConstant > 0, "Exploration constant must be greater than 0"
        self.searchLimit = iterationLimit
        self.explorationConstant = explorationConstant
        self.rolloutPolicy = rolloutPolicy
        self.cnn_feature_extractor = CNNStateLearner(num_pegs, num_disks)
        self.cnn_feature_extractor.load_state_dict(torch.load(rollout_state_extractor))
        self.actionPolicy = None
        self.root = None
        self.simulator = simulator

    def search(self, initial_state: StateNode, possibleActionGetter: callable):
        """
        -------------------------------------------------------
        Perform MCTS search to find the best action.
        -------------------------------------------------------
        Parameters:
           initial_state (StateNode or gym.Env): Initial state of the game.
           possibleActionGetter (callable): Function to get possible actions.
        Returns:
           bestChild (StateNode): Best child node after MCTS search.
        -------------------------------------------------------
        """
        # Check if initial_state is a gym.Env and initialize it
        self.root = deepcopy(initial_state)
        self.root.parent = None
        self.actionPolicy = possibleActionGetter

        # Select, expand, simulate and backup rewards in the tree
        for i in tqdm(range(self.searchLimit)):
            node = self._select_node(self.root)
            reward = self._rollout(node)
            self._backpropagate(node, reward)

        bestChild = self.getBestChild(self.root, 0)
        return bestChild

    def _select_node(self, node: StateNode):
        """
        -------------------------------------------------------
        Select the next node to expand in the MCTS tree.
        -------------------------------------------------------
        Parameters:
            node (StateNode): Current node in the MCTS tree.
        Returns:
           node (StateNode): Selected node for expansion.
        -------------------------------------------------------
        """
        while not node.isTerminal:  # Check if the node is terminal
            # Check if the node is fully expanded, if so, select the best child
            if self.max_number_of_actions == len(node.children):
                node = self.getBestChild(node, self.explorationConstant)
            else:
                return self.expand(node)  # if not fully expanded, expand the node
        return node

    def _rollout(self, node: StateNode):
        """
        -------------------------------------------------------
        Gets the expected reward for the given node.
        -------------------------------------------------------
        Parameters:
            node (StateNode): Current node in the MCTS tree.
        Returns:
            expected_reward (float): Expected reward for the node.
        -------------------------------------------------------
        """
        with torch.no_grad():
            x = self.image_transform(node.state['observation']).unsqueeze(0)
            pred_disc_state = self.cnn_feature_extractor(x)
            state_rewards = self.rolloutPolicy.q_net(pred_disc_state)
        return torch.mean(state_rewards).item()

    def expand(self, node):
        """
        -------------------------------------------------------
        Expand the node by adding a new child node based on the possible actions.
        -------------------------------------------------------
        Parameters:
            node (StateNode): Current node in the MCTS tree.
        Returns:
            newNode (StateNode): Newly created child node.
        -------------------------------------------------------
        """

        actions = self.actionPolicy(node.state['observation'], self.max_number_of_actions-len(node.children))
        for action in actions:
            # Create simulator action input
            typea = 2  # Actions for right controller
            pos_change = action.tolist()[:3]
            orientation_change = [0, 0, 0, 0]
            button = action.tolist()[3]
            act = [typea, pos_change, orientation_change, button]
            # Take action in the simulator
            newState = self.simulator.takeAction(act, node.state, bool(node.action[-1].item()))
            # Check if the new state is terminal
            newNode = StateNode(newState, parent=node, action_pos=pos_change, action_button=bool(button))
            node.children[action] = newNode
            if len(actions) == len(node.children):
                node.isFullyExpanded = True
            return newNode

    def _backpropagate(self, node: StateNode, reward: float):
        """
        -------------------------------------------------------
        Backpropagate the reward from the leaf node to the root node.
        -------------------------------------------------------
        Parameters:
            node (StateNode): Current node in the MCTS tree.
            reward (float): Reward received from the simulation.
        -------------------------------------------------------
        """
        # Backpropagate the reward to the root node
        while node is not None:
            node.visits += 1
            node.cumulative_rewards += reward
            node = node.parent

    def getBestChild(self, node: StateNode, explorationConstant: float):
        """
        -------------------------------------------------------
        Select the best child node based on UCT (Upper Confidence Bound for Trees).
        Randomly chooses based on the probability of the child node's value.
        nodevalue = child.totalReward / child.numVisits + explorationConstant * np.sqrt(
            2 * np.log(node.visits) / child.numVisits)
        -------------------------------------------------------
        Parameters:
            node (StateNode): Current node in the MCTS tree.
            explorationConstant (float): Exploration constant for UCT.
        Returns:
            selectedNode (StateNode): Selected child node based on UCT.
        -------------------------------------------------------
        """

        def softmax(x):
            e_x = np.exp(x - np.max(x))
            return e_x / e_x.sum()

        nodeValues = []
        childnodes = []
        # Get the values of the child nodes
        for child in node.children.values():
            nodeValue = child.cumulative_rewards / child.visits + explorationConstant * np.sqrt(
                2 * np.log(node.visits) / child.visits)
            nodeValues.append(nodeValue)
            childnodes.append(child)
        # Normalize the values using softmax and select a child node based on the probabilities
        print(f'softmax: {softmax(np.array(nodeValues))}, vals = {nodeValues}')
        selectedNode = np.random.choice(len(childnodes), p=softmax(np.array(nodeValues)))
        return childnodes[selectedNode]
