from stable_baselines3 import DQN
import numpy as np

# Load pre-trained model
BRAIN_PATH = "/Users/alonflorentin/Downloads/gym-hanoi/gym_hanoi/dqn_hanoi_5_disks.zip"
brain_model = DQN.load(BRAIN_PATH)

def get_brain_action(state: np.ndarray) -> int:
    """
    Get the DQN's suggested action for a given Tower of Hanoi state.
    """
    state = np.array(state).reshape(1, -1)
    action, _ = brain_model.predict(state, deterministic=True)
    return 2 #int(action) - LATER
