"""
-------------------------------------------------------
Test Environment for Tower of Hanoi in VR
Includes logging, reward tracking, and proximity metrics
-------------------------------------------------------
Author:  Alon Florentin
Email:   abf386@nyu.edu
__updated__ = 4/30/25
-------------------------------------------------------
"""
# Imports
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time

from env_utils import (
    setup_browser, enter_xr_mode,
    get_screenshot, controller_input,
    get_controller_state, get_tower_state
)

# Constants
MAX_DELTA_POS = 0.05
VIEW_MIN = np.array([-0.6, 0.9, -1.1], dtype=np.float32)
VIEW_MAX = np.array([ 0.6, 1.6, -0.35], dtype=np.float32)

STEP_PENALTY = -0.005
GRAB_BONUS = 100.0
MOVE_REWARD_SCALE = 300.0
MOVE_REWARD_MAX = 500.0

TOWER_X, TOWER_Y, TOWER_Z = 0.0, 1.064, -1.0
PLACE_THRESH = 0.18
MAX_STEPS = 600


class VRHanoiEnv(gym.Env):
    """
    --------------------------------------------------------
    Environment for Tower of Hanoi in VR with rewards
    ---------------------------------------------------------
    Parameters:
        render (bool): Whether to render the environment
        height (int): Height of the observation space
        width (int): Width of the observation space
    ---------------------------------------------------------
    """
    def __init__(self, render=True, height=512, width=512):
        super().__init__()
        self.height, self.width = height, width
        self.render = render

        self.observation_space = spaces.Box(low=0, high=255, shape=(height, width, 3), dtype=np.uint8)
        self.action_space = spaces.Dict({
            "right_movement": spaces.Box(low=-MAX_DELTA_POS, high=MAX_DELTA_POS, shape=(3,), dtype=np.float32),
            "buttons": spaces.MultiBinary(1),
        })

        self.webdriver = setup_browser(render)
        self.max_steps = MAX_STEPS

        # Episodic tracking
        self.episode_rewards = []
        self.episode_grabs = 0
        self.episode_min_dists = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        enter_xr_mode(self.webdriver)
        time.sleep(5.0)

        self.stage = "approach"
        self.grab_ref_y = None
        self.step_count = 0
        self.selected_disc_id = None
        self.initial_grab_pos = None
        self.move_started = False
        self.cumulative_reward = 0.0
        self.min_gx, self.min_gy, self.min_gz = float('inf'), float('inf'), float('inf')
        self.did_grab = False

        info = get_controller_state(self.webdriver, "right")
        disc_pos = np.array([-0.48, 1.352, -1.0])
        delta = disc_pos - np.array(info['position'])
        controller_input(self.webdriver, 'right', delta, [0,0,0,0], buttonIndex=1, buttonState='released')
        time.sleep(0.3)
        info = get_controller_state(self.webdriver, "right")
        print(f"📍 Controller reset to: {info['position']}")

        return self._get_obs(), {}

    def _get_obs(self):
        img = get_screenshot(self.webdriver)
        img = img.resize((self.height, self.width))
        return np.array(img.convert("RGB"))

    def step(self, action):
        delta = np.clip(action["right_movement"], -MAX_DELTA_POS, MAX_DELTA_POS)
        grip = bool(action["buttons"][0])

        curr = np.array(get_controller_state(self.webdriver, "right")["position"], dtype=np.float32)
        dest = np.clip(curr + delta, VIEW_MIN, VIEW_MAX)
        controller_input(
            self.webdriver, "right",
            delta_position=(dest - curr).tolist(),
            delta_angles=[0,0,0,0],
            buttonIndex=1,
            buttonState="pressed" if grip else "released"
        )

        tower = get_tower_state(self.webdriver)
        disc_local = list(tower["discs"].values())[3]
        local = np.array(disc_local["position"], dtype=np.float32)
        disk_pos = local * 0.32 + np.array([0,1,-1.0], dtype=np.float32)
        ctrl_pos = dest

        dx, dy, dz = np.abs(disk_pos - ctrl_pos)
        gx, gy, gz = np.abs(np.array([TOWER_X, TOWER_Y, TOWER_Z]) - disk_pos)

        # Track best proximity this episode
        self.min_gx = min(self.min_gx, gx)
        self.min_gy = min(self.min_gy, gy)
        self.min_gz = min(self.min_gz, gz)

        reward = STEP_PENALTY
        done = False

        if self.stage == "approach":
            reward += np.exp(-5*dx) + np.exp(-5*dy) + np.exp(-5*dz)
            if grip and dx < 0.1 and dy < 0.1 and dz < 0.1:
                self.stage = "move"
                self.selected_disc_id = 3
                self.initial_grab_pos = disk_pos.copy()
                self.move_started = False
                self.grab_ref_y = disk_pos[1]
                self.did_grab = True
                reward += GRAB_BONUS
                print("🌟 Grab successful, switching to move stage")

        elif self.stage == "move":
            if grip and self.selected_disc_id is not None:
                reward += 5.0
                local_pos = (ctrl_pos - np.array([0, 1, -1.0])) / 0.32
                script = f"""
                    let pos = [{local_pos[0]}, {local_pos[1]}, {local_pos[2]}];
                    if (!isNaN(pos[0]) && !isNaN(pos[1]) && !isNaN(pos[2])) {{
                        console.log("📦 Moving disc to:", pos);
                        if (towerState && towerState.discs && towerState.discs[{self.selected_disc_id}]) {{
                            towerState.discs[{self.selected_disc_id}].position = pos;
                        }}
                    }} else {{
                        console.warn("⚠️ Invalid disc position attempted:", pos);
                    }}
                """

                self.webdriver.execute_script(script)

                dist_moved = np.abs(disk_pos - self.initial_grab_pos)
                if not self.move_started and np.any(dist_moved > 0.2):
                    self.move_started = True

                if self.move_started:
                    shaping = (
                        np.exp(-5 * gx) +
                        np.exp(-5 * gy) +
                        np.exp(-5 * gz)
                    )
                    reward += MOVE_REWARD_SCALE * shaping

            if not grip:
                placement_error = gx + gy + gz
                final_reward = MOVE_REWARD_MAX * np.exp(-5 * placement_error)
                reward += final_reward
                print(f"🏁 Released disc. Final placement reward: {final_reward:.2f} | Δx={gx:.2f}, Δy={gy:.2f}, Δz={gz:.2f}")
                done = True
                self.stage = "approach"
                self.selected_disc_id = None
                self.move_started = False

        self.step_count += 1
        self.cumulative_reward += reward

        if self.step_count >= self.max_steps:
            done = True

        if done:
            self.episode_rewards.append(self.cumulative_reward)
            if len(self.episode_rewards) > 10:
                self.episode_rewards.pop(0)
            if self.did_grab:
                self.episode_grabs += 1
            self.episode_min_dists.append((self.min_gx, self.min_gy, self.min_gz))
            if len(self.episode_min_dists) > 10:
                self.episode_min_dists.pop(0)

            if len(self.episode_rewards) == 10:
                avg_reward = np.mean(self.episode_rewards)
                grabs = sum(1 for r in self.episode_min_dists if r is not None)
                min_dists = np.min(self.episode_min_dists, axis=0)
                print(f"\n📊 Last 10 episodes:")
                print(f"    Avg reward: {avg_reward:.2f}")
                print(f"    Avg min Δx={min_dists[0]:.3f}, Δy={min_dists[1]:.3f}, Δz={min_dists[2]:.3f}")
                print(f"    Grabs: {self.episode_grabs}/10")
                self.episode_grabs = 0  # reset counter for next window

        return self._get_obs(), reward, done, False, {}

    def restart_browser(self):
        try:
            self.webdriver.quit()
        except:
            pass
        time.sleep(2)
        self.webdriver = setup_browser(render=True)
        enter_xr_mode(self.webdriver)
        print("🔄 Chrome restarted")

    def close(self):
        if hasattr(self, "webdriver"):
            self.webdriver.quit()
