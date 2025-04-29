"""
-------------------------------------------------------
Virtual Reality Tower of Hanoi Environment 
Stage 2: Grab, Hold, and Place on Tower 1
-------------------------------------------------------
Author: Alon – 04/28/2025
-------------------------------------------------------
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time
from enum import Enum

from env_utils import (
    setup_browser, enter_xr_mode,
    get_headset_state, get_controller_state,
    get_screenshot, controller_input,
    get_tower_state
)

# ─── Constants ─────────────────────────────────────────────────────────────
MAX_DELTA_POS    = 0.08
MAX_DELTA_QUAT   = 0.0

VIEW_BOUNDS_MIN  = np.array([-0.75, 1.0, -0.6])
VIEW_BOUNDS_MAX  = np.array([ 0.75, 1.5, -0.35])

STEP_PENALTY     = -0.005

# Stage 1: Grab
GRAB_DIST           = 0.1       # must be THIS close
STAGE1_FINAL_REWARD = 100.0     # first grab bonus

# Stage 2: Hold
HOLD_REWARD_STEP    = 20.0      # per step while correctly holding

# Stage 3: Place on Tower 1
TOWER_TARGET_X      = 0.0       # x-coordinate of tower 1
MAX_TOWER_DIST      = 1.5       # normalize shaping rewards
PLACE_DIST_THRESH   = 0.18      # considered valid placement if < this
TOWER_PROX_SCALE    = 50.0      # per-step shaping
STAGE3_FINAL_REWARD = 10000.0   # final huge reward for placing

MAX_ENV_STEPS       = 600

# ─── Environment Class ──────────────────────────────────────────────────────
class VRHanoiEnv(gym.Env):
    def __init__(self, render=True, height=512, width=512):
        super().__init__()
        self.height, self.width = height, width

        self.observation_space = spaces.Box(
            low=0, high=255, shape=(height, width, 3), dtype=np.uint8
        )
        self.action_space = spaces.Dict({
            "right_movement": spaces.Box(
                low=np.array([-3,0,-3,-np.pi,-np.pi,-np.pi,-np.pi]),
                high=np.array([3,3,3, np.pi, np.pi, np.pi, np.pi]),
                dtype=np.float32
            ),
            "headset_movement": spaces.Box(
                low=np.array([-3,0,-3,-np.pi,-np.pi,-np.pi,-np.pi]),
                high=np.array([3,3,3, np.pi, np.pi, np.pi, np.pi]),
                dtype=np.float32
            ),
            "buttons": spaces.MultiBinary(1),
        })

        self.webdriver = setup_browser(render)
        self.max_steps = MAX_ENV_STEPS

    def _get_obs(self):
        img = get_screenshot(self.webdriver)
        img = img.resize((self.height, self.width))
        return np.array(img.convert("RGB"))

    def _get_info(self):
        return {
            "headset": get_headset_state(self.webdriver),
            "right_controller": get_controller_state(self.webdriver, "right"),
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        enter_xr_mode(self.webdriver)
        time.sleep(5.0)

        self.has_grabbed = False
        self.has_placed = False
        self.current_step = 0

        self.distance_history = []
        self.grip_counter = 0

        return self._get_obs(), self._get_info()

    def step(self, action):
        # ─── A) Unpack action ────────────────────────────────────────────────
        rm = action["right_movement"]
        pos_delta  = np.clip(rm[:3], -MAX_DELTA_POS, MAX_DELTA_POS)
        quat_delta = np.clip(rm[3:], -MAX_DELTA_QUAT, MAX_DELTA_QUAT)
        grip       = bool(action["buttons"][0])

        # ─── B) Move controller ──────────────────────────────────────────────
        ctrl = np.array(get_controller_state(self.webdriver, "right")["position"])
        new_ctrl = np.clip(ctrl + pos_delta, VIEW_BOUNDS_MIN, VIEW_BOUNDS_MAX)
        controller_input(
            self.webdriver,
            hand="right",
            delta_position=(new_ctrl - ctrl).tolist(),
            delta_angles=quat_delta.tolist(),
            buttonIndex=1,
            buttonState="pressed" if grip else "released"
        )

        # ─── C) Read disk and controller positions ────────────────────────────
        tower_state = get_tower_state(self.webdriver)
        disc_info   = list(tower_state['discs'].values())[4]
        disk_pos3d  = np.array(disc_info['position'])
        disk_pos    = disk_pos3d * 0.32 + np.array([0,1,-0.5])
        ctrl_pos    = np.array(get_controller_state(self.webdriver, "right")["position"])
        dist_to_disk = np.linalg.norm(disk_pos - ctrl_pos)

        self.distance_history.append(dist_to_disk)
        if len(self.distance_history) > 10:
            self.distance_history.pop(0)
        if grip:
            self.grip_counter += 1

        # ─── D) Reward Computation ────────────────────────────────────────────
        reward = STEP_PENALTY
        done = False

        # -- Stage 1: Approach and Grab -------------------------------------
        if not self.has_grabbed:
            reward += 1.2 * np.exp(-5.0 * dist_to_disk)
            if grip and dist_to_disk < GRAB_DIST:
                self.has_grabbed = True
                reward += STAGE1_FINAL_REWARD
                print(f"🌟 Stage1: Grabbed at dist {dist_to_disk:.4f}")

        # -- Stage 2: Hold and Move Toward Tower ---------------------------
        elif not self.has_placed:
            if grip and dist_to_disk < GRAB_DIST:
                reward += HOLD_REWARD_STEP

                tower_dist = abs(disk_pos[0] - TOWER_TARGET_X)
                norm_dist  = min(tower_dist / MAX_TOWER_DIST, 1.0)
                reward += TOWER_PROX_SCALE * (1.0 - norm_dist)

            # detect placement
            if not grip:
                tower_dist = abs(disk_pos[0] - TOWER_TARGET_X)
                if tower_dist < PLACE_DIST_THRESH:
                    self.has_placed = True
                    reward += STAGE3_FINAL_REWARD
                    done = True
                    print(f"🏆 Stage3: Placed on Tower1 at x={disk_pos[0]:.4f}")

        # ─── E) Logging ──────────────────────────────────────────────────────
        self.current_step += 1
        if self.current_step % 10 == 0:
            md = min(self.distance_history) if self.distance_history else dist_to_disk
            print(f"[Step {self.current_step}] min_dist={md:.4f}, dist={dist_to_disk:.4f}")
        if self.current_step % 50 == 0:
            print(f"[Step {self.current_step}] grips={self.grip_counter}")

        # ─── F) Return ───────────────────────────────────────────────────────
        obs, info = self._get_obs(), self._get_info()
        return obs, reward, done, False, info

    def render(self):
        pass

    def close(self):
        if hasattr(self, 'webdriver'):
            self.webdriver.quit()

    def restart_browser(self):
        try:
            self.webdriver.quit()
        except:
            pass
        time.sleep(2)
        self.webdriver = setup_browser(render=True)
        enter_xr_mode(self.webdriver)
        print("🔄 Chrome restarted")
