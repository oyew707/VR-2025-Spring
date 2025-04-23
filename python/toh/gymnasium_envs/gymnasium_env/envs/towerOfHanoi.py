"""
-------------------------------------------------------
Virtual Reality Tower of Hanoi Environment
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "4/14/25"
-------------------------------------------------------
"""
# Imports
from enum import Enum
from typing import List
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from env_utils import *


# Constants

class Actions(Enum):
    headset = 0
    left = 1
    right = 2


class TowerOfHanoiEnv(gym.Env):
    """
    -------------------------------------------------------
    Virtual Reality Tower of Hanoi Environment
    -------------------------------------------------------
    Parameters:
        height (int): Height of the observation space.
        width (int): Width of the observation space.
        render (bool): Whether to render the environment.
    -------------------------------------------------------
    """

    def __init__(self, height=512, width=512, render=True):
        super(TowerOfHanoiEnv, self).__init__()

        self.height, self.width = height, width
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(height, width, 3),  # (H, W, RGB channels)
            dtype=np.uint8
        )

        self.action_space = spaces.Dict({
            # Continuous components (3D position (first 3) + quaternion (last 4))
            "left_movement": spaces.Box(low=np.array([-3, 0, -3, -np.pi, -np.pi, -np.pi, -np.pi]),
                                        high=np.array([3, 3, 3, np.pi, np.pi, np.pi, np.pi]),
                                        dtype=np.float32),
            "right_movement": spaces.Box(low=np.array([-3, 0, -3, -np.pi, -np.pi, -np.pi, -np.pi]),
                                         high=np.array([3, 3, 3, np.pi, np.pi, np.pi, np.pi]),
                                         dtype=np.float32),
            "headset_movement": spaces.Box(low=np.array([-3, 0, -3, -np.pi, -np.pi, -np.pi, -np.pi]),
                                           high=np.array([3, 3, 3, np.pi, np.pi, np.pi, np.pi]),
                                           dtype=np.float32),
            # Discrete button states (MultiBinary for multiple buttons)
            "buttons": spaces.MultiBinary(1)  # Just one button for now
        })

        # Set up the browser
        self.webdriver = setup_browser(render)

    def _get_obs(self) -> np.ndarray:
        """
        -------------------------------------------------------
        Get the current observation of the environment.
        -------------------------------------------------------
        Returns:
            img (np.ndarray): The current observation image.
        -------------------------------------------------------
        """
        img = get_screenshot(self.webdriver)
        img = img.resize((self.height, self.width))
        img = np.array(img.convert("RGB"))
        return img

    def _get_info(self) -> dict:
        """
        -------------------------------------------------------
        Get additional information about the environment. Specifically,
        the state (position and angle) of the headset and controllers.
        -------------------------------------------------------
        Returns:
            info (dict): A dictionary containing the state of the headset
                         and controllers.
        -------------------------------------------------------
        """
        headset_state = get_headset_state(self.webdriver)
        left_controller_state = get_controller_state(self.webdriver, "left")
        right_controller_state = get_controller_state(self.webdriver, "right")
        return {
            "headset": headset_state,
            "left_controller": left_controller_state,
            "right_controller": right_controller_state
        }

    def reset(self, seed=None, options=None):
        """
        -------------------------------------------------------
        Reset the environment to an initial state by reloading the webpage
        and entering the VR environment.
        -------------------------------------------------------
        Parameters:
            seed (int): Random seed for reproducibility.
            options (dict): Additional options for resetting the environment.
        Returns:
            observation (dict): Initial observation of the environment.
            info (dict): Additional information about the environment.
        -------------------------------------------------------
        """
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        # Load the Webpage and the VR environment
        enter_xr_mode(self.webdriver)

        # Get the initial state of the environment
        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def _process_action(self, action: int, change_position: np.ndarray | None) -> np.ndarray:
        """
        -------------------------------------------------------
        Process and clean up the given action.
        -------------------------------------------------------
        Parameters:
            action (int): The action to be processed (0: headset, 1: left, 2: right).
            change_position (np.ndarray): The change in x, y, z position for the action.
        Returns:
            new_position (np.ndarray): The cleaned-up position after applying the action.
        -------------------------------------------------------
        """
        if change_position is None:
            change_position = np.array([0, 0, 0])

        # Clip position changes to the range [-0.1, 0.1]
        change_position = np.clip(change_position, -0.1, 0.1)

        # Get current positions of headset and controllers
        info = self._get_info()
        headset = info["headset"]
        left_controller = info["left_controller"]
        right_controller = info["right_controller"]

        # Get controller and headset position
        if action == Actions.headset.value:
            new_position = np.array(headset['position']) + change_position
        elif action == Actions.left.value:
            new_position = np.array(left_controller['position']) + change_position
        elif action == Actions.right.value:
            new_position = np.array(right_controller['position']) + change_position
        else:
            raise ValueError("Invalid action")

        # Clip new positions to valid ranges
        new_position[0] = np.clip(new_position[0], -5, 5)  # x
        new_position[1] = np.clip(new_position[1], 0, 3)  # y
        new_position[2] = np.clip(new_position[2], -5, 5)  # z

        # Ensure the distance between headset and controllers is not more than 3
        if action in [Actions.left.value, Actions.right.value]:
            controller_state = left_controller if action == Actions.left.value else right_controller
            distance = np.linalg.norm(new_position - headset['position'])
            if distance > 3:
                direction = change_position / np.linalg.norm(change_position)
                max_change = 3 - np.linalg.norm(
                    np.array(controller_state["position"]) - np.array(headset["position"]))
                new_position = direction * max_change

        return new_position

    # TODO: Discuss and Implement reward function and termination
    def step(self, action, change_position=None, change_orientation=None, button: bool = False):
        """
        -------------------------------------------------------
        Apply an action to the environment and return the new state,
        reward, and termination status.
        -------------------------------------------------------
        Parameters:
           action (int): The action to be taken (0: headset, 1: left, 2: right).
           change_position (Iterable): The change in x,y,z position for the action.
           change_orientation (Iterable): The change in orientation (quaternion) for the action.
           button (bool): Whether the button is pressed or released.
        Returns:
            observation (np.ndarray): The new observation of the environment.
            reward (float): The reward received after taking the action.
            terminated (bool): Whether the episode has ended.
            truncated (bool): Whether the episode has been truncated.
            info (dict): Additional information about the environment.
        -------------------------------------------------------
        """
        # Apply the action to the environment
        if change_orientation is None:
            change_orientation = np.array([0, 0, 0, 0])

        # Clip orientation changes to the range [-0.52, 0.52] radians
        change_orientation = np.clip(change_orientation, -0.52, 0.52)

        # Process the action
        change_position = self._process_action(action, change_position)

        if action == Actions.headset.value:
            headset_input(self.webdriver, change_position, change_orientation)
        elif action == Actions.left.value:
            butt = "pressed" if button else "released"
            controller_input(self.webdriver, "left", change_position,
                             change_orientation, buttonIndex=1, buttonState=butt)
        elif action == Actions.right.value:
            butt = "pressed" if button else "released"
            controller_input(self.webdriver, "right", change_position,
                             change_orientation, buttonIndex=1, buttonState=butt)
        else:
            raise ValueError("Invalid action")

        # An episode is done iff the agent has reached the target
        console_logs = getConsoleLogs(self.webdriver)
        terminated = checkTerminal(console_logs)
        # 100 if the agent has reached the target, -1 if the agent has made an invalid move
        reward = 100 if terminated else -1 if checkInvalidMove(console_logs) else 0
        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, False, info

    def close(self):
        """
        -------------------------------------------------------
        Close the environment and clean up resources.
        -------------------------------------------------------
        """
        self.webdriver.quit()
