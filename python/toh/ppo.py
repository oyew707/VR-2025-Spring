"""
-------------------------------------------------------
IMplementation of PPO (Proximal Policy Optimization) algorithm
Source: https://github.com/nikhilbarhate99/PPO-PyTorch/blob/master/PPO.py
Modified to use MCTS in action selection
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo2233@nyu.edu
__updated__ = "4/29/25"
-------------------------------------------------------
"""

# Imports
import torch
import torch.nn as nn
from torch.distributions import MultivariateNormal, Bernoulli
from stable_baselines3 import DQN
from gymnasium_env.envs.towerOfHanoiSim import StateType
from planner import TowerOfHanoiPlanner, StateNode, CNNStateLearner
import torchvision.transforms as T

# Constants
NUM_DISKS = 4
NUM_PEGS = 3
device = torch.device('cpu')
if torch.cuda.is_available():
    device = torch.device('cuda:0')
    torch.cuda.empty_cache()
    print("Device set to : " + str(torch.cuda.get_device_name(device)))
else:
    print("Device set to : cpu")


class RolloutBuffer:
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.state_values = []
        self.is_terminals = []

    def clear(self):
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.state_values[:]
        del self.is_terminals[:]


class ActorCritic(nn.Module):
    """
    -------------------------------------------------------
    Actor-Critic network for PPO supporting hybrid action space:
    - Continuous vector (length 3)
    - Binary action (Bernoulli)
    -------------------------------------------------------
    Parameters:
        state_dim - Dimension of input state (int)
        cont_action_dim - Length of continuous action vector (int, should be 3)
        binary_action_dim - Length of binary action vector (int, should be 1)
        action_std_init - Initial std for continuous actions (float)
        feature_extractor - Feature extractor for images (nn.Module)
        pred_boundary - Prediction boundary for mean in cont (float)
    -------------------------------------------------------
    """
    image_transform = T.Compose([
        T.Resize(224),
        T.ToTensor(),
        T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

    def __init__(self, state_dim, cont_action_dim, binary_action_dim, action_std_init, feature_extractor, pred_boundary=0.1):
        super(ActorCritic, self).__init__()
        self.has_continuous_action_space = cont_action_dim > 0
        self.cont_action_dim = cont_action_dim
        self.action_dim = cont_action_dim + binary_action_dim
        self.pred_boundary = pred_boundary
        self.feature_extractor = feature_extractor
        self.action_var = torch.full((cont_action_dim,), action_std_init ** 2).to(device)

        self.shared = nn.Sequential(
            nn.Flatten(),
            nn.Linear(state_dim, 512),
            nn.Tanh(),
            nn.Linear(512, 256),
            nn.Tanh(),
            nn.Linear(256, 64),
            nn.Tanh(),
        )
        self.actor_head = nn.Linear(64, self.action_dim)
        self.critic_head = nn.Linear(64, 1)
        # Actor network: outputs 3 for continuous, 1 for binary
        self.cont_activation = nn.Tanh()
        self.binary_activation = nn.Sigmoid()

    def set_action_std(self, action_std):
        """
        -------------------------------------------------------
        Set the standard deviation for continuous actions.
        -------------------------------------------------------
        Parameters:
            action_std - Standard deviation for continuous actions (float)
        -------------------------------------------------------
        """
        if self.cont_action_dim > 0:
            self.action_var = torch.full((self.cont_action_dim,), action_std ** 2).to(device)

    def forward(self):
        """
        -------------------------------------------------------
        Forward pass through the network.
        -------------------------------------------------------
        """
        raise NotImplementedError("This method should not be called directly.")

    def hidden(self, state):
        """
        -------------------------------------------------------
        Get the hidden features from the shared network.
        -------------------------------------------------------
        Parameters:
            state - Current state (Image.image)
        Returns:
            features - Hidden features (torch.Tensor)
        -------------------------------------------------------
        """
        with torch.no_grad():
            x = self.image_transform(state).unsqueeze(0).to(device)
            x = self.feature_extractor(x)
        features = self.shared(x)
        return features

    def act(self, state):
        """
        -------------------------------------------------------
        Sample an action from the policy given a state.
        -------------------------------------------------------
        Parameters:
            state - Current state (Image.image)
        Returns:
            action - Sampled action (torch.Tensor, shape [4])
            action_logprob - Log probability of action (torch.Tensor)
            state_val - Estimated state value (torch.Tensor)
        -------------------------------------------------------
        """
        # Get action Mean (or probs) from actor network
        features = self.hidden(state)
        out = self.actor_head(features)
        cont_mean = self.cont_activation(out[..., :self.self.cont_action_dim]) * self.pred_boundary
        binary_probs = self.binary_activation(out[..., self.cont_action_dim:])
        # Sample from the distributions
        cont_dist = MultivariateNormal(cont_mean, torch.diag(self.action_var).unsqueeze(0))
        binary_dist = Bernoulli(probs=binary_probs)
        cont_action = cont_dist.sample()
        binary_action = binary_dist.sample()
        # concatenate the actions, log probs and state value
        action = torch.cat([cont_action, binary_action], dim=-1)
        action_logprob = cont_dist.log_prob(cont_action) + binary_dist.log_prob(binary_action)
        state_val = self.critic_head(features)
        return action.detach(), action_logprob.detach(), state_val.detach()

    def sample_actions(self, state, num_samples):
        """
        -------------------------------------------------------
        Sample multiple actions from the policy given a state.
        -------------------------------------------------------
        Parameters:
            state - Current observation at state (Image.image)
            num_samples - Number of samples to draw (int)
        Returns:
            actions - Sampled actions (torch.Tensor, shape [num_samples, action_dim])
        -------------------------------------------------------
        """
        # Get action Mean (or probs) from actor network
        features = self.hidden(state)
        out = self.actor_head(features)
        cont_mean = self.cont_activation(out[..., :self.cont_action_dim]) * self.pred_boundary
        binary_probs = self.binary_activation(out[..., self.cont_action_dim:])

        # Sample from the distributions
        cont_dist = MultivariateNormal(cont_mean, torch.diag(self.action_var).unsqueeze(0))
        binary_dist = Bernoulli(probs=binary_probs)

        cont_action = cont_dist.sample((num_samples,))
        binary_action = binary_dist.sample((num_samples,))

        # concatenate the actions, log probs and state value
        actions = torch.cat([cont_action, binary_action], dim=-1)
        return actions.detach().squeeze(dim=1)

    def evaluate(self, state, action):
        """
        -------------------------------------------------------
        returns log probability and distribution entropy of the action
        -------------------------------------------------------
        Parameters:
            state - Current observation at state (Image.image)
            action - Action taken (torch.Tensor)
        Returns:
            action_logprob - Log probability of action (torch.Tensor)
            dist_entropy - Distribution entropy (torch.Tensor)
            state_values - Estimated state values (torch.Tensor)
        -------------------------------------------------------
        """
        # Get action Mean (or probs) from actor network
        features = self.hidden(state)
        out = self.actor_head(features)
        cont_mean = self.cont_activation(out[..., :self.cont_action_dim]) * self.pred_boundary
        binary_probs = self.binary_activation(out[..., self.cont_action_dim:])

        # Sample from the distributions
        cont_dist = MultivariateNormal(cont_mean, torch.diag(self.action_var).unsqueeze(0))
        binary_dist = Bernoulli(probs=binary_probs)

        cont_action = action[..., :self.cont_action_dim]
        binary_action = action[..., self.cont_action_dim:]
        action_logprob = cont_dist.log_prob(cont_action) + binary_dist.log_prob(binary_action.float())

        print(f"{cont_dist.entropy()=}, {binary_dist.entropy()=}")
        dist_entropy = torch.cat([cont_dist.entropy().unsqueeze(-1), binary_dist.entropy()], dim=-1)
        state_values = self.critic_head(features)

        return action_logprob, torch.sum(dist_entropy, dim=-1), state_values


class PPO:
    """
    --------------------------------------------------------
    Proximal Policy Optimization (PPO) Algorithm with Planning
    --------------------------------------------------------
    Parameters:
        cont_action_dim (int): Dimension of the action space
        binary_action_dim (int): Dimension of the action space
        lr_actor (float): Learning rate for the actor (policy) network.
        lr_critic (float): Learning rate for the critic (value) network.
        gamma (float): Discount factor for future rewards (0 < gamma ≤ 1).
        K_epochs (int): Number of epochs to update the policy per PPO update.
        eps_clip (float): Clipping parameter for PPO objective (controls how far new policy deviate from old policy).
        action_std_init (float, optional): Initial standard deviation for continuous action distributions
        use_mcts (bool, optional): Whether to use MCTS for action selection.
        iterationLimit (int, optional): Maximum number of iterations for MCTS.
        num_samples (int, optional): Number of samples to draw from the policy.
    ---------------------------------------------------------
    """
    def __init__(self, cont_action_dim, binary_action_dim, lr_actor, lr_critic, gamma, K_epochs, eps_clip,
                 use_mcts=True, action_std_init=0.6, iterationLimit=15, num_samples=6):
        assert cont_action_dim > 0 or binary_action_dim > 0, "At least one action space (continuous or binary) must be defined."
        assert action_std_init > 0, "Initial action standard deviation must be positive."
        assert 0 < gamma <= 1, "Gamma must be in the range (0, 1]."
        assert K_epochs > 0, "Number of epochs must be positive."
        assert eps_clip > 0, "Epsilon clip must be positive."
        assert lr_actor > 0, "Learning rate for actor must be positive."
        assert lr_critic > 0, "Learning rate for critic must be positive."
        self.has_continuous_action_space = cont_action_dim > 0
        self.gamma = gamma
        self.K_epochs = K_epochs
        self.eps_clip = eps_clip
        self.action_std = action_std_init
        self.planner = None
        self.iterationLimit = iterationLimit
        self.brain = DQN.load('nn_models/dqn_hanoi_4_disks.zip')
        self.cnn_feature_extractor = CNNStateLearner(NUM_PEGS, NUM_DISKS)
        self.cnn_feature_extractor.load_state_dict(torch.load('nn_models/state_extractor.pth'))
        if use_mcts:
            self.planner = TowerOfHanoiPlanner(rolloutPolicy=self.brain, iterationLimit=iterationLimit)

        # Actor-Critic network
        self.policy = ActorCritic(64 * 28 * 62, cont_action_dim, binary_action_dim, action_std_init,
                                  feature_extractor=self.cnn_feature_extractor.cnn).to(device)
        self.optimizer = torch.optim.Adam([
            {'params': self.policy.shared.parameters(), 'lr': min(lr_actor, lr_critic)},
            {'params': self.policy.actor_head.parameters(), 'lr': lr_actor},
            {'params': self.policy.critic_head.parameters(), 'lr': lr_critic},
        ])
        self.policy_old = ActorCritic(64 * 28 * 62, cont_action_dim, binary_action_dim, action_std_init,
                                      feature_extractor=self.cnn_feature_extractor.cnn).to(device)
        self.policy_old.load_state_dict(self.policy.state_dict())
        # Rollout buffer
        self.buffer = RolloutBuffer()

        # Loss function
        self.MseLoss = nn.MSELoss()

    def set_action_std(self, new_action_std):
        """
        -------------------------------------------------------
        Set the standard deviation for continuous actions.
        -------------------------------------------------------
        Parameters:
            new_action_std - New standard deviation for continuous actions (float)
        -------------------------------------------------------
        """
        self.action_std = new_action_std
        self.policy.set_action_std(new_action_std)
        self.policy_old.set_action_std(new_action_std)

    def decay_action_std(self, action_std_decay_rate, min_action_std):
        """
        -------------------------------------------------------
        Decay the action standard deviation for exploration.
        -------------------------------------------------------
        Parameters:
            action_std_decay_rate - Rate of decay for action standard deviation (float)
            min_action_std - Minimum action standard deviation (float)
        -------------------------------------------------------
        """
        assert min_action_std >= 0, "Minimum action standard deviation must be positive."
        self.action_std = self.action_std - action_std_decay_rate
        self.action_std = min(round(self.action_std, 4), min_action_std)
        self.set_action_std(self.action_std)

    def select_action(self, observation, stateInfo, prev_action):
        """
        -------------------------------------------------------
        selects actions using the policy network or MCTS
        -------------------------------------------------------
        Parameters:
            observation - Current state (Image.image)
            stateInfo - information about the state i.e , disc, controller and headset (Dict)
            prev_action - Previous action taken (torch.tensor)
        Returns:
           action - Selected action (list)
           searchNode - Search node for MCTS (StateNode)
        -------------------------------------------------------
        """
        with torch.no_grad():
            if self.planner is not None:
                st: StateType = {
                    "reward": 0,
                    "observation": observation,
                    "isterminal": False,
                    "info": stateInfo,
                }
                sn = StateNode(st)
                sn.action = prev_action
                expectedNextNode = self.planner.search(sn, lambda x, sample: self.policy_old.sample_actions(x, sample))
                print(f"Result of MCTS {str(expectedNextNode)} {expectedNextNode.action}")
                action = expectedNextNode.action
                action_logprob, _, state_val = self.policy_old.evaluate(observation, action)
            else:
                action, action_logprob, state_val = self.policy_old.act(observation)

        self.buffer.states.append(observation)
        self.buffer.actions.append(action)
        self.buffer.logprobs.append(action_logprob)
        self.buffer.state_values.append(state_val)
        return action.tolist()

    def update(self):
        """
        -------------------------------------------------------
        Update the policy using the PPO algorithm.
        -------------------------------------------------------
        """
        # Monte Carlo estimate of returns
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(self.buffer.rewards), reversed(self.buffer.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.insert(0, discounted_reward)

        # Normalizing the rewards
        rewards = torch.tensor(rewards, dtype=torch.float32).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-7)

        # convert list to tensor
        old_states = torch.squeeze(torch.stack(self.buffer.states, dim=0)).detach().to(device)
        old_actions = torch.squeeze(torch.stack(self.buffer.actions, dim=0)).detach().to(device)
        old_logprobs = torch.squeeze(torch.stack(self.buffer.logprobs, dim=0)).detach().to(device)
        old_state_values = torch.squeeze(torch.stack(self.buffer.state_values, dim=0)).detach().to(device)

        # calculate advantages
        advantages = rewards.detach() - old_state_values.detach()

        # Optimize policy for K epochs
        for _ in range(self.K_epochs):
            # Evaluating old actions and values
            logprobs, state_values, dist_entropy = self.policy.evaluate(old_states, old_actions)

            # match state_values tensor dimensions with rewards tensor
            state_values = torch.squeeze(state_values)

            # Finding the ratio (pi_theta / pi_theta__old)
            ratios = torch.exp(logprobs - old_logprobs.detach())

            # Finding Surrogate Loss
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.eps_clip, 1 + self.eps_clip) * advantages

            # final loss of clipped objective PPO
            loss = -torch.min(surr1, surr2) + 0.5 * self.MseLoss(state_values, rewards) - 0.01 * dist_entropy

            # take gradient step
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()

        # Copy new weights into old policy
        self.policy_old.load_state_dict(self.policy.state_dict())

        # clear buffer
        self.buffer.clear()

    def save(self, checkpoint_path):
        """
        -------------------------------------------------------
        Save the model parameters to a checkpoint file.
        -------------------------------------------------------
        Parameters:
            checkpoint_path - Path to save the checkpoint (str)
        -------------------------------------------------------
        """
        torch.save(self.policy_old.state_dict(), checkpoint_path)

    def load(self, checkpoint_path):
        """
        -------------------------------------------------------
        Load the model parameters from a checkpoint file.
        -------------------------------------------------------
        Parameters:
            checkpoint_path - Path to load the checkpoint from (str)
        -------------------------------------------------------
        """
        self.policy_old.load_state_dict(torch.load(checkpoint_path, map_location=lambda storage, loc: storage))
        self.policy.load_state_dict(torch.load(checkpoint_path, map_location=lambda storage, loc: storage))
