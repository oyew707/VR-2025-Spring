# A_TOH.py — PPO Training for VR Tower of Hanoi

import os
import numpy as np
import gymnasium as gym
from gymnasium.wrappers import TimeLimit
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

# Import VR Environment
from gymnasium_envs.gymnasium_env.envs.testEnv import VRHanoiEnv

# ─── Action Repeat Wrapper (Frame-Skip) ─────────────────────────────────────
class ActionRepeatWrapper(gym.Wrapper):
    def __init__(self, env, n_repeat: int = 2):
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

# ─── Flatten Dict-Action Space into Box ─────────────────────────────────────
class ActionFlattenWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        orig = env.action_space
        low_rm, high_rm = orig["right_movement"].low.astype(np.float32), orig["right_movement"].high.astype(np.float32)
        low_hm, high_hm = orig["headset_movement"].low.astype(np.float32), orig["headset_movement"].high.astype(np.float32)
        low_btn = np.zeros(orig["buttons"].shape, dtype=np.float32)
        high_btn = np.ones(orig["buttons"].shape, dtype=np.float32)

        low = np.concatenate([low_rm, low_hm, low_btn], axis=0)
        high = np.concatenate([high_rm, high_hm, high_btn], axis=0)

        self.action_space = gym.spaces.Box(low=low, high=high, dtype=np.float32)
        self.orig_action_space = orig

    def step(self, action_flat):
        rm = action_flat[:7]
        hm = action_flat[7:14]
        btn = action_flat[14:]
        dict_act = {
            "right_movement": rm,
            "headset_movement": hm,
            "buttons": (btn > 0.5).astype(np.int8),
        }
        return self.env.step(dict_act)

# ─── Build Environment with Wrappers ────────────────────────────────────────
def make_env():
    env = VRHanoiEnv(render=True, height=128, width=128)
    env = TimeLimit(env, max_episode_steps=384)         # End episode after 200 steps
    # env = ActionRepeatWrapper(env, n_repeat=2)        # Frame-skip = 2
    env = ActionFlattenWrapper(env)                     # Flatten action space
    env = Monitor(env, filename=None)                   # Track episode stats
    return env

# ─── Setup Directories ──────────────────────────────────────────────────────
log_dir = "./vr_hanoi_logs"
os.makedirs(log_dir, exist_ok=True)

# ─── Initialize Vectorized Environment ──────────────────────────────────────
vec_env = DummyVecEnv([make_env])

model = PPO(
    policy="CnnPolicy",
    env=vec_env,
    verbose=1,
    n_steps=128, 
    batch_size=64, 
    gamma=0.98, 
    learning_rate=2.5e-4,
    ent_coef=0.055, 
    clip_range=0.2, 
    n_epochs=5, 
    gae_lambda=0.95,
    max_grad_norm=1.2, 
    tensorboard_log=log_dir
)

model.learn(total_timesteps=100_000)
model.save("ppo_vrhanoi_stage2")
print("✅ Training complete — model saved to ppo_vrhanoi_stage2.zip")

# ─── Quick Final Evaluation ─────────────────────────────────────────────────
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
print("✅ Environment closed.")