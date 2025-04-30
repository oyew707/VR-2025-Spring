"""
-------------------------------------------------------
Virtual environment to be used for simulations
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "4/29/25"
-------------------------------------------------------
"""

# Imports
import json
import time
from typing import Dict, TypedDict, NotRequired, Optional
import numpy as np
from gymnasium_env.envs.towerOfHanoi import get_optimal_states
from env_utils import *
from gymnasium_env.envs.towerOfHanoiVR import Actions

# Constants
STARTING_HEADSET = [0, 1.6, -0.5]
CROPPED_BOX = (775, 472, 1630, 858)  # (left, upper, right, lower)
image_size = 224
NUM_DISKS = 4
NUM_PEGS = 3


class StateType(TypedDict):
    reward: NotRequired[float]
    pressedButton: NotRequired[bool]
    observation: Image.Image
    isterminal: bool
    info: dict


class TowerOfHanoiEnvSim():
    """
    -------------------------------------------------------
    Tower of Hanoi environment for reinforcement learning.
    -------------------------------------------------------
    Parameters:
    -------------------------------------------------------
    """

    def __init__(self, device: str = 'right'):
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
        self.device = device
        self.height, self.width = image_size, int(
            image_size * ((CROPPED_BOX[2] - CROPPED_BOX[0]) / (CROPPED_BOX[3] - CROPPED_BOX[1])))
        # Set up the browser
        self.webdriver = setup_browser()

        # Set up the environment
        # Load the Webpage and the VR environment
        enter_xr_mode(self.webdriver, "towerOfHanoiSim")

        # Get the initial state of the environment
        info = self._get_info()
        # Move the headset to the starting position
        headset_delta = np.subtract(STARTING_HEADSET, info['headset']['position'])
        headset_input(self.webdriver, headset_delta, [0, 0, 0, 0])

    def _get_obs(self) -> Image.Image:
        """
        -------------------------------------------------------
        Get the current observation of the environment.
        -------------------------------------------------------
        Returns:
            img (np.ndarray): The current observation image.
        -------------------------------------------------------
        """
        img = get_screenshot(self.webdriver)
        img = img.crop(CROPPED_BOX)
        img = img.resize((self.height, self.width))
        return img

    def _get_info(self) -> dict:
        """
        -------------------------------------------------------
        Get additional information about the environment. Specifically,
        the state (position and angle) of the headset and controllers.
        -------------------------------------------------------
        Returns:
            info (dict): A dictionary containing the state of the headset
                         and controllers as well as the disc and towers.
        -------------------------------------------------------
        """
        headset_state = get_headset_state(self.webdriver)
        left_controller_state = get_controller_state(self.webdriver, "left")
        right_controller_state = get_controller_state(self.webdriver, "right")
        disc_state = self.get_state()
        return {
            "headset": headset_state,
            "left_controller": left_controller_state,
            "right_controller": right_controller_state,
            "tower": disc_state,
        }

    def set_state(self, globalDiscInfo: Dict):
        """
        -------------------------------------------------------
        Set the state of the environment.
        -------------------------------------------------------
        Parameters:
           globalDiscInfo (dict): A dictionary containing the state of the discs
        -------------------------------------------------------
        """
        assert self.webdriver is not None, "Driver is not initialized"
        assert urlparse(
            self.webdriver.current_url).geturl() == URL, f"Driver is not on the correct URL {self.webdriver.current_url}"

        # Get tower state
        set_str = json.dumps(globalDiscInfo)

        self.webdriver.execute_script(f"""
                window.discs = {set_str};
            """)

    def get_state(self) -> Dict:
        """
        -------------------------------------------------------
        Get the current global disc of the environment.
        -------------------------------------------------------
        Returns:
            globalDiscInfo (dict): A dictionary containing the state of the discs
        -------------------------------------------------------
        """
        assert self.webdriver is not None, "Driver is not initialized"
        assert urlparse(
            self.webdriver.current_url).geturl() == URL, f"Driver is not on the correct URL {self.webdriver.current_url}"

        globalDiscInfo = self.webdriver.execute_script("""
                return {
                    'discs': window.discs,
                    'isTerminal': window.towerIsValid,
                };
            """)
        return globalDiscInfo

    def _process_action(self, action: int, info: Dict,
                        change_position: Optional[np.ndarray] = None) -> np.ndarray:
        """
        -------------------------------------------------------
        Process and clean up the given action.
        -------------------------------------------------------
        Parameters:
            action (int): The action to be processed (0: headset, 1: left, 2: right).
            info (dict): The current state of the environment.
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
        controller = info['left_controller' if self.device == 'left' else 'right_controller']

        # Get controller and headset position
        if action == Actions.left.value:
            new_position = np.array(controller['position']) + change_position
        elif action == Actions.right.value:
            new_position = np.array(controller['position']) + change_position
        else:
            raise ValueError("Invalid action")

        # Clip new positions to valid ranges
        new_position[0] = np.clip(new_position[0], -1.5, 1.5)  # x
        new_position[1] = np.clip(new_position[1], 1., 1.5)  # y
        new_position[2] = np.clip(new_position[2], -1, -0.5)  # z

        return new_position

    def takeAction(self, action, st: StateType, pressed):
        """
        -------------------------------------------------------
        Take an action in the environment
        1. set the simulation env to the given state
        2. check if the controller is close to any of the discs
        3. if the controller is close to a disc, move it
        4. set the new position of the controller
        -------------------------------------------------------
        Parameters:
           action (list): The action to take. The first element is the action type.
                          The second element is the change in position of the controller.
                          The third element is the change in angle of the controller.
                          The fourth element is whether the button is pressed or not.
           st (StateType): The state of the environment we want to start from.
           pressed (bool): Whether the button is pressed or not.
        Returns:
           newState (StateType): The new state of the environment after taking the action.
        -------------------------------------------------------
        """
        # Set the env to the current state
        self.set_state(st['info']['tower']['discs'])
        info = self._get_info()
        # Assume only one device is used and set it to the position
        p1 = info['left_controller' if self.device == 'left' else 'right_controller']['position']
        p2 = st['info']['left_controller' if self.device == 'left' else 'right_controller']['position']
        delta = np.subtract(p2, p1)
        print(f"Moving the controller {p1} to the prev state position {p2}")
        controller_input(self.webdriver, self.device, delta, [0, 0, 0, 0],
                         buttonState='pressed' if pressed else 'released')

        # Extract the actions
        change_position = action[1]
        change_angle = action[2]
        pressedButton = action[3]
        print(f"Action: {action=}, {change_position=}, {change_angle=}, {pressedButton=}")

        # Check if the controller is close to any of the discs
        hit = self._check_hit()
        # If the controller is close to a disc, move it
        if pressed and hit is not None:
            print("Should Move the Disc")
            curr_contr_pos = self._process_action(action[0], info, change_position)
            info['left_controller' if self.device == 'left' else 'right_controller']['position'] = curr_contr_pos
            curr_disc_pos = 10 * np.subtract(curr_contr_pos, np.array([0, 1.5, -0.5]))
            info['tower']['discs'][str(hit)]['position'] = curr_disc_pos
            # set the new position of the disc
            self.set_state(info['info']['tower']['discs'])


        # Set the new position of the controller
        controller_input(self.webdriver, self.device, change_position, change_angle,
                         buttonState='pressed' if pressedButton else 'released')

        newState: StateType = {
            "observation": self._get_obs(),
            "isterminal": info.get('isTerminal', False),
            "info": info,
        }

        return newState

    def _check_hit(self):
        """
        -------------------------------------------------------
        Check if the controller is close to any of the discs.
        -------------------------------------------------------
        Returns:
            index (int): The index of the disc that the controller is close to.
                         Returns None if no disc is close.
        -------------------------------------------------------
        """
        # Get positions of discs and controller
        info = self._get_info()

        # Check if the controller is close to any of the disc
        controller_pos = info['left_controller' if self.device == 'left' else 'right_controller']['position']
        for index, discInfo in info['tower']['discs'].items():
            disc_pos = discInfo['position']
            disc_pos = np.add(disc_pos, np.array([0, 1.5, -0.5])) * 0.1
            xz_dst = np.linalg.norm([disc_pos[0] - controller_pos[0], disc_pos[2] - controller_pos[2]])
            y_dst = disc_pos[1] - controller_pos[1]
            # Check if the distance is within a threshold
            if xz_dst < 0.05 + discInfo['value'] * 0.1 and y_dst < 0.05 + discInfo['height'] * 0.05:
                return index
        return None
