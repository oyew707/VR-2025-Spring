# train_vr_hanoi.py
# Creates and trains a brand-new PPO model on the above environment

import os
import numpy as np
import gymnasium as gym
from gymnasium.wrappers import TimeLimit
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback

from gymnasium_envs.gymnasium_env.envs.testEnv import VRHanoiEnv  # Import your minimal env

# ─── Callback to periodically restart Chrome ─────────────────────────────────
class RestartChromeCallback(BaseCallback):
    def __init__(self, env, check_freq=10_000, verbose=1):
        super().__init__(verbose)
        self.env = env
        self.check_freq = check_freq

    def _on_step(self) -> bool:
        if self.num_timesteps % self.check_freq == 0:
            print(f"🌟 {self.num_timesteps} timesteps reached — restarting browser.")
            self.env.envs[0].restart_browser()
        return True

# ─── Flatten the Dict-action into a single Box for PPO ───────────────────────
class ActionFlattenWrapper(gym.Wrapper):
    def __init__(self, env):
        super().__init__(env)
        orig = env.action_space
        low_rm = orig["right_movement"].low.astype(np.float32)
        high_rm = orig["right_movement"].high.astype(np.float32)
        low_btn = np.zeros(orig["buttons"].shape, dtype=np.float32)
        high_btn = np.ones(orig["buttons"].shape, dtype=np.float32)
        low = np.concatenate([low_rm, low_btn], axis=0)
        high = np.concatenate([high_rm, high_btn], axis=0)
        self.action_space = gym.spaces.Box(low=low, high=high, dtype=np.float32)
        self.orig_action_space = orig

    def step(self, action_flat):
        rm = action_flat[:3]
        btn = action_flat[3:]
        dict_act = {
            "right_movement": rm,
            "buttons": (btn > 0.5).astype(np.int8),
        }
        return self.env.step(dict_act)

# ─── Build a single env with wrappers ────────────────────────────────────────
def make_env():
    base_env = VRHanoiEnv(render=True, height=128, width=128)
    env = TimeLimit(base_env, max_episode_steps=base_env.max_steps)
    env = ActionFlattenWrapper(env)
    env = Monitor(env, filename=None)
    env.restart_browser = base_env.restart_browser
    return env

# ─── Setup logging ───────────────────────────────────────────────────────────
log_dir = "./vr_hanoi_logs"
os.makedirs(log_dir, exist_ok=True)
vec_env = DummyVecEnv([make_env])

# ─── Instantiate a brand-new PPO model ──────────────────────────────────────
model = PPO(
    policy="CnnPolicy",
    env=vec_env,
    verbose=1,
    n_steps=256,
    batch_size=64,
    gamma=0.98,
    learning_rate=2e-4,
    ent_coef=0.062,
    clip_range=0.2,
    n_epochs=10,
    gae_lambda=0.95,
    max_grad_norm=0.5,
    tensorboard_log=log_dir
)

# ─── Train with safe-save on interrupt ───────────────────────────────────────
try:
    model.learn(total_timesteps=1_000_000, callback=RestartChromeCallback(vec_env))
except KeyboardInterrupt:
    print("\n⛔ Training interrupted by user!")
finally:
    model.save("ppo_vrhanoi_new")
    print("✅ Model saved to 'ppo_vrhanoi_new.zip'.")

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
