"""
-------------------------------------------------------
Tower of Hanoi Environment
Source: https://github.com/Alonerism/TOH_RL
Modified to use state matrix observation and no reward for invalid actions.
-------------------------------------------------------
Author:  Alon Florentin, Einstein Oyewole
Email:   abf38@nyu.edu, eo2233@nyu.edu
__updated__ = "4/28/25"
-------------------------------------------------------
"""

# Imports
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from copy import deepcopy

# Constants


class HanoiEnv(gym.Env):
    """
    -------------------------------------------------------
    Tower of Hanoi Environment
    -------------------------------------------------------
    Parameters:
        num_disks - number of disks (int > 0)
        max_steps - maximum number of steps (int > 0)
        render_mode - rendering mode (str)
        num_pegs - number of pegs (int > 0)
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, num_disks=4, max_steps=3000, render_mode=None, num_pegs=3, seed=0):
        super().__init__()
        self.num_disks = num_disks
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.num_pegs = num_pegs
        self.min_moves = 2 ** self.num_disks - 1

        # Action lookup table
        self.ACTION_LOOKUP = {
            0: (0, 1),
            1: (1, 0),
            2: (1, 2),
            3: (2, 1),
            4: (0, 2),  # ✅ Allow move from peg 0 to peg 2
            5: (2, 0),  # ✅ Allow move from peg 2 to peg 0
        }

        # Define action and observation spaces
        self.action_space = spaces.Discrete(6)
        # self.observation_space = spaces.Box(low=0, high=2, shape=(self.num_disks,), dtype=np.int32)
        self.observation_space = spaces.MultiBinary([self.num_pegs, self.num_disks], seed=seed)
        self.goal_state = self.num_disks * (2,)
        self.current_state = None
        self.towers = None
        self.move_count = 0
        self.optimal_states = get_optimal_states(self.num_disks)
        self.len_optimal_states = len(self.optimal_states)
        self.reward_flags = set()

    def reset(self, *, seed=None, options=None):
        """
        -------------------------------------------------------
        Resets the environment to its initial state.
        -------------------------------------------------------
        Parameters:
           seed - random seed (int)
           options - additional options (dict)
        Returns:
            current_state - initial state of the environment (np.ndarray)
            info - additional information (dict)
        -------------------------------------------------------
        """
        super().reset(seed=seed)
        self.towers = [[i for i in range(self.num_disks)], [], []]
        self.current_state = self._get_state()
        self.move_count = 0
        self.reward_flags = set()
        return self.observation_to_state_matrix(self.current_state), {}

    def step(self, action):
        """
        -------------------------------------------------------
        Executes the action in the environment.
        -------------------------------------------------------
        Parameters:
            action - action to be executed (int)
        Returns:
            current_state - current state of the environment (tuple)
            reward - reward received (float)
            terminated - whether the episode has terminated (bool)
            truncated - whether the episode has been truncated (bool)
            info - additional information (dict)
        -------------------------------------------------------
        """
        assert action in self.ACTION_LOOKUP.keys(), f"{action} ({type(action)}) invalid"
        action = int(action)

        # Check if action is valid, if not, return a 0 reward
        # Note: negative rewards are propagated to previous states
        valid_actions = self.get_valid_actions()
        if action not in valid_actions:
            self.move_count += 1
            return self.observation_to_state_matrix(self.current_state), 0, False, False, {}

        # Perform the action
        move = self.ACTION_LOOKUP[action]
        top_disk = min(self.disks_on_peg(move[0]))  # Get the top disk on the source peg
        next_state = list(self.current_state)  # Convert tuple to list for modification
        next_state[top_disk] = move[1]  # Move the disk to the destination peg
        self.current_state = tuple(next_state)  # Convert back to tuple
        self.move_count += 1

        # Final reward for solving the puzzle
        if self.current_state == self.goal_state:
            reward = 100
            terminated = True
        elif self.current_state in self.optimal_states and self.current_state not in self.reward_flags:
            index = self.optimal_states.index(self.current_state)
            print(f"Optimal state {index + 1} reached")
            reward = 5 * (index + 1) / self.len_optimal_states
            self.reward_flags.add(self.current_state)
            terminated = False
        else:
            reward = 0
            terminated = False

        truncated = self.move_count >= self.max_steps
        return self.observation_to_state_matrix(self.current_state), reward, terminated, truncated, {}

    def get_valid_actions(self):
        """
        -------------------------------------------------------
        Returns a list of valid actions based on the current state.
        -------------------------------------------------------
        Returns:
           actions - list of valid actions (list of int)
        -------------------------------------------------------
        """
        return [a for a, m in self.ACTION_LOOKUP.items() if self.move_allowed(m)]

    def disks_on_peg(self, peg):
        """
        -------------------------------------------------------
        Returns the disks on a given peg.
        -------------------------------------------------------
        Parameters:
           peg - peg number (int)
        Returns:
           disks - list of disks on the peg (list of int)
        -------------------------------------------------------
        """
        assert 0 <= peg < self.num_pegs, f"Invalid peg: {peg}"
        return [d for d in range(self.num_disks) if self.current_state[d] == peg]

    def move_allowed(self, move):
        """
        -------------------------------------------------------
        Checks if a move is allowed based on the current state.
        i.e. if the disk on the source peg is smaller than the disk on the destination peg.
        -------------------------------------------------------
        Parameters:
           move - move to be checked (tuple)
        Returns:
           allowed - whether the move is allowed (bool)
        -------------------------------------------------------
        """
        assert move in self.ACTION_LOOKUP.values(), f"Invalid move: {move}"
        from_peg = self.disks_on_peg(move[0])
        to_peg = self.disks_on_peg(move[1])
        if not from_peg:
            return False
        return (not to_peg) or min(to_peg) > min(from_peg)

    def _get_state(self):
        """
        -------------------------------------------------------
        Returns the current state of the environment.
        -------------------------------------------------------
        Returns:
              state - current state of the environment (tuple)
                where the index of the tuple represents the disk number (smallest disk = 0)
                and the value represents the peg number (int)
        -------------------------------------------------------
        """
        # Initialize state with zeros
        state = [0] * self.num_disks
        # Fill the state with the peg numbers
        for peg_index, tower in enumerate(self.towers):
            for disk in tower:
                state[disk] = peg_index
        return tuple(state)

    def observation_to_state_matrix(self, observation):
        """
        -------------------------------------------------------
        Converts the observation from the environment to a state matrix.
        -------------------------------------------------------
        Parameters:
           observation - the observation from the environment (tuple)
        Returns:
             state_matrix - the state matrix (numpy array)
        -------------------------------------------------------
        """
        assert len(observation) == self.num_disks, f"Invalid observation length: {len(observation)}"
        # Initialize a zero matrix of shape (num_disks, num_pegs)
        state_matrix = np.zeros((self.num_pegs, self.num_disks))

        # Set the appropriate column for each disk
        for disk, peg in enumerate(observation):
            state_matrix[peg, disk] = 1

        return state_matrix

    def render(self):
        """
        -------------------------------------------------------
        Prints the current state of the environment.
        -------------------------------------------------------
        """
        if self.render_mode != "human":
            return

        pegs = {0: [], 1: [], 2: []}
        for i, peg in enumerate(self.current_state):
            pegs[peg].append(i)
        for k in pegs:
            pegs[k].sort(reverse=True)

        max_height = self.num_disks
        peg_width = self.num_disks * 2 + 1
        print("\n🏗️ TOWERS OF HANOI")
        for level in range(max_height - 1, -1, -1):
            row = ""
            for peg in range(3):
                if level < len(pegs[peg]):
                    disk = pegs[peg][level]
                    disk_str = "=" * (2 * (disk + 1) - 1)
                    pad = " " * (self.num_disks - disk)
                    row += f"{pad}{disk_str}{pad}".center(peg_width) + "   "
                else:
                    row += " " * self.num_disks + "|" + " " * self.num_disks + "   "
            print(row)
        print("=" * (peg_width * 3 + 6))


def get_optimal_moves(num_disks, src=0, aux=1, dst=2):
    """
    -------------------------------------------------------
    Computes a trajectory of optimal moves for solving
    the Tower of Hanoi problem.
    -------------------------------------------------------
    Parameters:
         num_disks - number of disks (int > 0)
         src - source peg (int)
         aux - auxiliary peg (int)
         dst - destination peg (int)
    Returns:
       moves - list of moves (list of tuples)
    -------------------------------------------------------
    """
    moves = []
    if num_disks == 1:
        moves.append((src, dst))
    else:
        moves += get_optimal_moves(num_disks - 1, src, dst, aux)
        moves.append((src, dst))
        moves += get_optimal_moves(num_disks - 1, aux, src, dst)
    return moves


def get_optimal_states(num_disks):
    """
    -------------------------------------------------------
    Computes a trajectory of optimal states for solving
    the Tower of Hanoi problem.
    -------------------------------------------------------
    Parameters:
        num_disks - number of disks (int > 0)
    Returns:
       states - list of states (list of tuples)
    -------------------------------------------------------
    """
    assert num_disks > 0 and isinstance(num_disks, int), f"Invalid number of disks: {num_disks}"

    def disks_on_peg(peg, st):
        return [d for d in range(num_disks) if st[d] == peg]

    states = []
    # Get the optimal moves
    optimal_moves = get_optimal_moves(num_disks)
    # Initialize the initial state
    initial_state = tuple([0] * num_disks)
    states.append(initial_state)
    # Iterate through the optimal moves and update the states
    for move in optimal_moves:
        next_state = deepcopy(list(states[-1]))
        top_disk = min(disks_on_peg(move[0], next_state))  # Get the top disk on the source peg
        next_state[top_disk] = move[1]  # Move the disk to the destination peg
        states.append(tuple(next_state))

    return states
