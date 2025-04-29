"""
-------------------------------------------------------
[Program Description]
-------------------------------------------------------
Author:  einsteinoyewole
ID:      [your ID]
Email:   [your email address]
__updated__ = "4/29/25"
-------------------------------------------------------
"""


# Imports
from PIL import Image
import torch
import os
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3 import DQN

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

class StateNode:
    """
    -------------------------------------------------------
    Node in the Monte Carlo Tree Search (MCTS) for Tower of Hanoi.
    -------------------------------------------------------
    Parameters:
        state (torch.Tensor): Current state of the game.
        parent (StateNode): Parent node in the MCTS tree.
        action_pos (np.ndarray): Change in position.
        action_button (bool): Action button pressed.
    -------------------------------------------------------
    """
    def __init__(self, state, parent=None, action_pos=None, action_button=False):
        self.state = state
        self.parent = parent
        self.action = [action_button, action_pos]
        self.children = {}
        self.visits = 0
        self.cumulative_rewards = 0

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
        return "%s: {%s}"%(self.__class__.__name__, ', '.join(s))

class TowerOfHanoiPlanner:
    """
    -------------------------------------------------------
    Implement Monte Carlo Tree Search (MCTS) for the Tower of Hanoi game.
    Source: https://shorturl.at/8d6AM
        Modified for Tower of Hanoi VR env.
    -------------------------------------------------------
    Parameters:
       [parameter name - parameter description (parameter type and constraints)]
    -------------------------------------------------------
    """
    image_transform = T.Compose([
        T.Resize(224),
        T.ToTensor(),
        T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    def __init__(self, rolloutPolicy:DQN, iterationLimit:int = 20, explorationConstant:float = 1.4,
                 rollout_state_extractor:str = CNN_EXTRACTOR_MODEL, num_disks:int = 4, num_pegs:int = 3,
                 ):
        assert iterationLimit > 0, "Iteration limit must be greater than 0"
        assert explorationConstant > 0, "Exploration constant must be greater than 0"
        self.searchLimit = iterationLimit
        self.explorationConstant = explorationConstant
        self.rolloutPolicy = rolloutPolicy
        self.cnn_feature_extractor = CNNStateLearner(num_pegs, num_disks)
        self.cnn_feature_extractor.load_state_dict(torch.load(rollout_state_extractor))

    def search(*args, **kwargs):
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
    


def function_definition:
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

    [other comments as necessary]
