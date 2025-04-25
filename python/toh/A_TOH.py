# A_TOH.py

import os
import numpy as np
import gymnasium as gym
from gymnasium.wrappers import TimeLimit
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# import your VR env
from gymnasium_envs.gymnasium_env.envs.testEnv import VRHanoiEnv

# ───── Action repeat (frame-skip) wrapper ─────────────────────────────────
class ActionRepeatWrapper(gym.Wrapper):
    def __init__(self, env, n_repeat: int = 4):
        super().__init__(env)
        self.n_repeat = n_repeat

    def step(self, action):
        total_reward = 0.0
        terminated = False
        truncated = False
        info = {}
        for _ in range(self.n_repeat):
            obs, reward, terminated, truncated, info = self.env.step(action)
            total_reward += reward
            if terminated or truncated:
                break
        return obs, total_reward, terminated, truncated, info

# ───── Flatten Dict-action into a single Box for PPO ───────────────────────
class ActionFlattenWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        orig = env.action_space  # a Dict space
        # extract Box lows/highs
        low_rm  = orig["right_movement"].low.astype(np.float32)
        high_rm = orig["right_movement"].high.astype(np.float32)
        low_hm  = orig["headset_movement"].low.astype(np.float32)
        high_hm = orig["headset_movement"].high.astype(np.float32)
        # MultiBinary → [0,1]
        btn_shape = orig["buttons"].shape
        low_btn  = np.zeros(btn_shape, dtype=np.float32)
        high_btn = np.ones(btn_shape,  dtype=np.float32)
        # concat
        low  = np.concatenate([low_rm, low_hm, low_btn], axis=0)
        high = np.concatenate([high_rm, high_hm, high_btn], axis=0)

        self.action_space = gym.spaces.Box(low=low, high=high, dtype=np.float32)
        self.orig_action_space = orig

    def step(self, action_flat):
        rm  = action_flat[:7]
        hm  = action_flat[7:14]
        btn = action_flat[14:]         # shape (1,)
        dict_act = {
            "right_movement": rm,
            "headset_movement": hm,
            "buttons": (btn > 0.5).astype(np.int8),
        }
        return self.env.step(dict_act)

# ───── Environment builder with TimeLimit, repeats & flattening ──────────
def make_env():
    env = VRHanoiEnv(render=True, height=128, width=128)
    # End episode after 200 steps so Monitor logs data
    env = TimeLimit(env, max_episode_steps=200)
    # Repeat each action for 4 frames
    env = ActionRepeatWrapper(env, n_repeat=2)
    # Flatten Dict action into a Box
    env = ActionFlattenWrapper(env)
    # Record episode stats
    env = Monitor(env, filename=None)
    return env

if __name__ == "__main__":
    # prepare log directory
    log_dir = "./vr_hanoi_logs"
    os.makedirs(log_dir, exist_ok=True)

    # create vectorized env
    vec_env = DummyVecEnv([make_env])

    # instantiate PPO with CNN policy for image obs
    model = PPO(
        policy="CnnPolicy",
        env=vec_env,
        verbose=1,
        tensorboard_log=log_dir
    )

    # train
    model.learn(total_timesteps=50_000)
    model.save("ppo_vrhanoi_stage2")
    print("✅ Training complete — model saved to ppo_vrhanoi_stage2.zip")

    # quick render test
    test_env = VRHanoiEnv(render=True, height=512, width=512)
    obs, _ = test_env.reset()
    done = False
    print("\n🎬 Final Run:")
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _, _ = test_env.step(action)
        print(f"Reward: {reward:.3f}")
    print("\n🏁 Episode finished.")
    test_env.close()
