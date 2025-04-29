"""
-------------------------------------------------------
Runs a DQN agent on the tower of Hanoi environment.
-------------------------------------------------------
Author:  Alon Florentin
Email:   abf38@nyu.edu
__updated__ = "4/29/25"
-------------------------------------------------------
"""

# Imports
import time
import gymnasium as gym
from gymnasium.wrappers import RecordEpisodeStatistics as Monitor
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import DummyVecEnv
from gymnasium_env.envs import TowerOfHanoiEnv
from stable_baselines3.her.her_replay_buffer import HerReplayBuffer

# Constants
num_disks = 4
total_timesteps = 1_000_000
max_steps = 6000
eval_episodes = 5


# === Environment ===
def make_env():
    return Monitor(TowerOfHanoiEnv(num_disks=num_disks, max_steps=max_steps, render_mode="human"))

# Create the environment
vec_env = DummyVecEnv([make_env])

# === DQN Agent ===
model = DQN(
    policy="MlpPolicy",
    env=vec_env,
    learning_rate=1e-4,  # ⬅️ Slower learning to handle longer episodes and sparse rewards
    buffer_size=36_000,  # ⬅️ Larger buffer to retain longer, varied episodes
    learning_starts=1_200,  # ⬅️ Slight delay to avoid learning from noise
    train_freq=100,  # ⬅️ Train less frequently to stabilize learning
    batch_size=96,  # ⬅️ Slightly larger batch for stable updates
    gamma=0.5,  # ⬅️ Discourage longer episodes
    target_update_interval=500,  # ⬅️ Slightly more frequent target sync
    exploration_fraction=0.5,  # ⬅️ More time spent exploring
    exploration_initial_eps=1,  # ⬅️ Explore a bit more aggressively early on
    exploration_final_eps=0.0092,  # ⬅️ Still allow rare exploration late
    verbose=2,
    seed=4,
    # replay_buffer_class=HerReplayBuffer,
    tensorboard_log="./dqn_hanoi_tensorboard/"
)

# === Train ===
model.learn(total_timesteps=total_timesteps)
model.save(f"./nn_models/dqn_hanoi_{num_disks}_disks")
print(f"\n✅ Training complete. Model saved.\n")

# === Evaluate ===
success_count = 0
for ep in range(eval_episodes):
    obs = vec_env.reset()
    done = False
    total_reward = 0
    steps = 0

    while not done and steps < max_steps:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _ = vec_env.step(action)
        total_reward += reward[0]
        steps += 1

    print(f"Episode {ep + 1}: Reward = {total_reward:.1f}, Steps = {steps}")
    if reward[0] >= 100:
        success_count += 1

print(f"\n✅ Success rate: {success_count}/{eval_episodes}")

# === Final Run Visualization ===
obs = vec_env.reset()
done = False
steps = 0
print("\n🎬 Final Render:\n")
while not done and steps < max_steps:
    print(f"Step {steps}")
    vec_env.envs[0].render()
    time.sleep(0.3)
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, _ = vec_env.step(action)
    done = done[0]
    steps += 1

print("\n🏁 Final run complete.")
