import gymnasium as gym
from gymnasium import spaces
import numpy as np
from enum import Enum

from env_utils import (
    get_screenshot, setup_browser, enter_xr_mode,
    get_headset_state, get_controller_state,
    controller_input, get_disk_pose, get_peg_pose
)

# ─── Hyperparameters & Shaping constants ────────────────────────────────
MAX_DELTA_POS     = 0.02   # m/step
MAX_DELTA_QUAT    = 0.2    # rad/step
VIEW_BOUNDS_MIN   = np.array([-1.0, 0.5, -1.0])
VIEW_BOUNDS_MAX   = np.array([ 1.0, 2.0,  1.0])

SUCCESS_DIST      = 0.05   # m threshold for success
SUCCESS_REWARD    = 1.0
STEP_PENALTY      = -0.01

# Shaping rewards
BEAM_THRESH            = 0.1   # m for beam–tower intersection
BEAM_REWARD            = 0.2
GRAB_INIT_DIST_THRESH  = 0.08  # m for initial grab
GRAB_INIT_REWARD       = 0.5
HOLD_REWARD_PER_STEP   = 0.1
PROXIMITY_SCALE        = 0.5   # * (prev_dist - new_dist)

class Actions(Enum):
    headset = 0
    right   = 1

class VRHanoiEnv(gym.Env):
    def __init__(self, render=True, height=512, width=512):
        super().__init__()
        self.height, self.width = height, width
        self.webdriver = setup_browser(render)

        # obs = RGB screenshot
        self.observation_space = spaces.Box(0, 255,
                                            shape=(height, width, 3),
                                            dtype=np.uint8)

        # Dict of 7‐pos + 7‐rot + button
        self.action_space = spaces.Dict({
            "right_movement": spaces.Box(
                low=np.array([-3,0,-3,-np.pi]*2),
                high=np.array([3,3,3,np.pi]*2),
                dtype=np.float32),
            "headset_movement": spaces.Box(
                low=np.array([-3,0,-3,-np.pi]*2),
                high=np.array([3,3,3,np.pi]*2),
                dtype=np.float32),
            "buttons": spaces.MultiBinary(1),
        })

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        enter_xr_mode(self.webdriver)

        # initialize shaping state
        disk_pos  = np.array(get_disk_pose(self.webdriver, disk_id=0))
        peg1_pos  = np.array(get_peg_pose(self.webdriver, peg_index=1))
        self.prev_dist = np.linalg.norm(disk_pos - peg1_pos)
        self.grabbed_once = False

        return self._get_obs(), self._get_info()

    def _get_obs(self):
        img = get_screenshot(self.webdriver)
        img = img.resize((self.height, self.width))
        return np.array(img.convert("RGB"))

    def _get_info(self):
        return {
            "headset":         get_headset_state(self.webdriver),
            "right_controller": get_controller_state(self.webdriver, "right")
        }

    def step(self, action):
        # ─── A) Clip deltas ────────────────────────────────────────────
        rm = action["right_movement"]
        pos_delta  = np.clip(rm[:3], -MAX_DELTA_POS,  MAX_DELTA_POS)
        quat_delta = np.clip(rm[3:], -MAX_DELTA_QUAT, MAX_DELTA_QUAT)
        grip       = bool(action["buttons"][0])

        # ─── B) Enforce view bounds ────────────────────────────────────
        ctrl_state = get_controller_state(self.webdriver, "right")["position"]
        ctrl       = np.array(ctrl_state)
        new_ctrl   = np.clip(ctrl + pos_delta, VIEW_BOUNDS_MIN, VIEW_BOUNDS_MAX)
        pos_to_apply = new_ctrl - ctrl

        controller_input(
            self.webdriver,
            hand="right",
            delta_position=pos_to_apply.tolist(),
            delta_angles=quat_delta.tolist(),
            buttonIndex=1,
            buttonState="pressed" if grip else "released"
        )

        # ─── C) Base reward & success check ────────────────────────────
        disk_pos = np.array(get_disk_pose(self.webdriver, disk_id=0))
        peg1_pos = np.array(get_peg_pose(self.webdriver, peg_index=1))
        dist     = np.linalg.norm(disk_pos - peg1_pos)

        if dist < SUCCESS_DIST:
            reward     = SUCCESS_REWARD
            terminated = True
        else:
            reward     = STEP_PENALTY
            terminated = False

        # ─── D) Beam–tower intersection shaping ────────────────────────
        tower_xs = self.webdriver.execute_script(
            "return window._hanoi_towers.map(t => t.pos);"
        )
        ctrl_x = new_ctrl[0]
        ctrl_z = new_ctrl[2]
        for tx in tower_xs:
            dist_xz = np.sqrt((ctrl_x - tx)**2 + (ctrl_z - 0.0)**2)
            if dist_xz < BEAM_THRESH:
                reward += BEAM_REWARD
                break

        # ─── E) Grab initiation reward ────────────────────────────────
        if grip and not self.grabbed_once:
            if np.linalg.norm(ctrl - disk_pos) < GRAB_INIT_DIST_THRESH:
                reward             += GRAB_INIT_REWARD
                self.grabbed_once = True

        # ─── F) Ongoing hold reward ───────────────────────────────────
        if grip and np.linalg.norm(new_ctrl - disk_pos) < GRAB_INIT_DIST_THRESH:
            reward += HOLD_REWARD_PER_STEP

        # ─── G) Proximity shaping ──────────────────────────────────────
        delta  = self.prev_dist - dist
        reward += PROXIMITY_SCALE * delta
        self.prev_dist = dist

        obs, info = self._get_obs(), self._get_info()
        return obs, reward, terminated, False, info

    def render(self):
        print("[INFO] rendered one frame")

    def close(self):
        self.webdriver.quit()
