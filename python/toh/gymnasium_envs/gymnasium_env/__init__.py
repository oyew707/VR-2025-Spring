from gymnasium.envs.registration import register

register(
    id="gymnasium_env/TowerOfHanoiEnvVR-v0",
    entry_point="gymnasium_env.envs:TowerOfHanoiEnvVR",
    max_episode_steps=10000,
)
register(
    id="gymnasium_env/TowerOfHanoiEnv-v0",
    entry_point="gymnasium_env.envs:TowerOfHanoiEnv",
    max_episode_steps=10000,
)