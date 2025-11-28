"""
VALORA AI Agent Base Classes
Foundational reinforcement learning infrastructure for economic agents
"""

import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import random
import json
import logging
from collections import deque

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of economic agents"""
    CONSUMER = "consumer"
    FIRM = "firm"
    BANK = "bank"
    REGULATOR = "regulator"


@dataclass
class AgentState:
    """Base state representation for all agents"""
    agent_id: str
    agent_type: AgentType
    wealth: float = 0.0
    income: float = 0.0
    utility: float = 0.0
    is_active: bool = True
    creation_tick: int = 0
    last_action_tick: int = 0
    custom_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentAction:
    """Represents an action taken by an agent"""
    agent_id: str
    action_type: str
    parameters: Dict[str, float]
    tick: int
    reasoning: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Experience:
    """Experience tuple for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Experience replay buffer for stable learning"""
    
    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, experience: Experience):
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)


class NeuralNetwork:
    """
    Lightweight neural network implementation for agent learning
    Uses numpy for portability (can be replaced with PyTorch for GPU)
    """
    
    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.001):
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.weights = []
        self.biases = []
        
        # Xavier initialization
        for i in range(len(layer_sizes) - 1):
            w = np.random.randn(layer_sizes[i], layer_sizes[i+1]) * np.sqrt(2.0 / layer_sizes[i])
            b = np.zeros((1, layer_sizes[i+1]))
            self.weights.append(w)
            self.biases.append(b)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass with ReLU activations"""
        self.activations = [x]
        self.z_values = []
        
        for i in range(len(self.weights) - 1):
            z = np.dot(self.activations[-1], self.weights[i]) + self.biases[i]
            self.z_values.append(z)
            a = np.maximum(0, z)  # ReLU
            self.activations.append(a)
        
        # Output layer (linear)
        z = np.dot(self.activations[-1], self.weights[-1]) + self.biases[-1]
        self.z_values.append(z)
        self.activations.append(z)
        
        return z
    
    def backward(self, target: np.ndarray) -> float:
        """Backward pass with gradient descent"""
        m = target.shape[0]
        delta = self.activations[-1] - target
        loss = np.mean(delta ** 2)
        
        for i in range(len(self.weights) - 1, -1, -1):
            dw = np.dot(self.activations[i].T, delta) / m
            db = np.sum(delta, axis=0, keepdims=True) / m
            
            if i > 0:
                delta = np.dot(delta, self.weights[i].T)
                delta = delta * (self.z_values[i-1] > 0)  # ReLU derivative
            
            # Update weights
            self.weights[i] -= self.learning_rate * dw
            self.biases[i] -= self.learning_rate * db
        
        return loss
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)
    
    def get_weights(self) -> Dict:
        return {
            'weights': [w.tolist() for w in self.weights],
            'biases': [b.tolist() for b in self.biases]
        }
    
    def set_weights(self, weights_dict: Dict):
        self.weights = [np.array(w) for w in weights_dict['weights']]
        self.biases = [np.array(b) for b in weights_dict['biases']]


class BaseAgent(ABC):
    """
    Abstract base class for all economic agents
    Implements core RL infrastructure
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        # Epsilon-greedy parameters
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # Experience replay
        self.replay_buffer = ReplayBuffer()
        self.batch_size = 64
        
        # Q-Network (main and target for DQN)
        hidden_size = 128
        self.q_network = NeuralNetwork(
            [state_dim, hidden_size, hidden_size, action_dim],
            learning_rate
        )
        self.target_network = NeuralNetwork(
            [state_dim, hidden_size, hidden_size, action_dim],
            learning_rate
        )
        self._update_target_network()
        
        # Training stats
        self.total_reward = 0.0
        self.episode_rewards = []
        self.losses = []
        self.training_steps = 0
        
        # State tracking
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type
        )
        self.action_history: List[AgentAction] = []
        
        # Explainability
        self.decision_explanations: List[Dict] = []
    
    @abstractmethod
    def observe(self, macro_state: Dict) -> np.ndarray:
        """Convert macro state to agent's observation vector"""
        pass
    
    @abstractmethod
    def get_action_space(self) -> List[Dict]:
        """Define possible actions for this agent type"""
        pass
    
    @abstractmethod
    def calculate_reward(self, macro_state: Dict, action: int) -> float:
        """Calculate reward based on economic outcomes"""
        pass
    
    @abstractmethod
    def interpret_action(self, action_idx: int) -> Dict:
        """Convert action index to interpretable action dict"""
        pass
    
    def select_action(self, state: np.ndarray, training: bool = True) -> Tuple[int, Dict]:
        """
        Epsilon-greedy action selection with explanation
        """
        explanation = {
            'agent_id': self.agent_id,
            'state': state.tolist(),
            'epsilon': self.epsilon if training else 0,
            'method': None,
            'q_values': None,
            'selected_action': None,
            'reasoning': None
        }
        
        if training and random.random() < self.epsilon:
            # Exploration
            action = random.randrange(self.action_dim)
            explanation['method'] = 'exploration'
            explanation['reasoning'] = f"Random exploration (ε={self.epsilon:.3f})"
        else:
            # Exploitation
            state_tensor = state.reshape(1, -1)
            q_values = self.q_network.predict(state_tensor)[0]
            action = int(np.argmax(q_values))
            
            explanation['method'] = 'exploitation'
            explanation['q_values'] = q_values.tolist()
            explanation['reasoning'] = self._generate_reasoning(state, q_values, action)
        
        explanation['selected_action'] = action
        self.decision_explanations.append(explanation)
        
        return action, explanation
    
    def _generate_reasoning(self, state: np.ndarray, q_values: np.ndarray, action: int) -> str:
        """Generate human-readable reasoning for action selection"""
        action_info = self.interpret_action(action)
        
        # Find top 3 actions
        sorted_actions = np.argsort(q_values)[::-1][:3]
        
        reasoning = f"Selected action: {action_info.get('name', action)}\n"
        reasoning += f"Expected value: {q_values[action]:.4f}\n"
        reasoning += "Top alternatives:\n"
        
        for i, alt_action in enumerate(sorted_actions):
            if alt_action != action:
                alt_info = self.interpret_action(alt_action)
                reasoning += f"  {i+1}. {alt_info.get('name', alt_action)}: {q_values[alt_action]:.4f}\n"
        
        return reasoning
    
    def learn(self, experience: Experience):
        """
        DQN learning update with experience replay
        """
        self.replay_buffer.push(experience)
        
        if len(self.replay_buffer) < self.batch_size:
            return
        
        # Sample batch
        batch = self.replay_buffer.sample(self.batch_size)
        
        states = np.array([e.state for e in batch])
        actions = np.array([e.action for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_states = np.array([e.next_state for e in batch])
        dones = np.array([e.done for e in batch])
        
        # Current Q values
        current_q = self.q_network.predict(states)
        
        # Target Q values (Double DQN)
        next_q_main = self.q_network.predict(next_states)
        next_q_target = self.target_network.predict(next_states)
        
        best_next_actions = np.argmax(next_q_main, axis=1)
        next_q_values = next_q_target[np.arange(len(batch)), best_next_actions]
        
        # Bellman update
        targets = current_q.copy()
        for i in range(len(batch)):
            if dones[i]:
                targets[i, actions[i]] = rewards[i]
            else:
                targets[i, actions[i]] = rewards[i] + self.discount_factor * next_q_values[i]
        
        # Train
        loss = self.q_network.backward(targets)
        self.losses.append(loss)
        self.training_steps += 1
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        # Update target network periodically
        if self.training_steps % 100 == 0:
            self._update_target_network()
    
    def _update_target_network(self):
        """Copy weights to target network"""
        self.target_network.set_weights(self.q_network.get_weights())
    
    def get_policy_summary(self) -> Dict:
        """Get summary of learned policy for explainability"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'training_steps': self.training_steps,
            'total_reward': self.total_reward,
            'epsilon': self.epsilon,
            'avg_loss': np.mean(self.losses[-100:]) if self.losses else 0,
            'recent_decisions': self.decision_explanations[-10:]
        }
    
    def save(self) -> Dict:
        """Serialize agent for persistence"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'epsilon': self.epsilon,
            'training_steps': self.training_steps,
            'total_reward': self.total_reward,
            'q_network_weights': self.q_network.get_weights(),
            'target_network_weights': self.target_network.get_weights(),
            'state': {
                'wealth': self.state.wealth,
                'income': self.state.income,
                'utility': self.state.utility,
                'custom_state': self.state.custom_state
            }
        }
    
    def load(self, data: Dict):
        """Restore agent from serialized data"""
        self.epsilon = data.get('epsilon', self.epsilon)
        self.training_steps = data.get('training_steps', 0)
        self.total_reward = data.get('total_reward', 0)
        
        if 'q_network_weights' in data:
            self.q_network.set_weights(data['q_network_weights'])
        if 'target_network_weights' in data:
            self.target_network.set_weights(data['target_network_weights'])
        
        if 'state' in data:
            self.state.wealth = data['state'].get('wealth', 0)
            self.state.income = data['state'].get('income', 0)
            self.state.utility = data['state'].get('utility', 0)
            self.state.custom_state = data['state'].get('custom_state', {})


class PPOAgent(BaseAgent):
    """
    Proximal Policy Optimization agent for continuous control
    Used by regulators for policy optimization
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.0003,
        clip_epsilon: float = 0.2,
        entropy_coeff: float = 0.01,
        value_coeff: float = 0.5
    ):
        super().__init__(
            agent_id, agent_type, state_dim, action_dim, learning_rate
        )
        
        self.clip_epsilon = clip_epsilon
        self.entropy_coeff = entropy_coeff
        self.value_coeff = value_coeff
        
        # Actor network (policy)
        self.actor = NeuralNetwork(
            [state_dim, 128, 128, action_dim],
            learning_rate
        )
        
        # Critic network (value function)
        self.critic = NeuralNetwork(
            [state_dim, 128, 128, 1],
            learning_rate
        )
        
        # Trajectory buffer
        self.trajectories = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Sample action from policy distribution
        Returns continuous action values
        """
        state_tensor = state.reshape(1, -1)
        
        # Get action mean from actor
        action_mean = self.actor.predict(state_tensor)[0]
        
        # Add exploration noise during training
        if training:
            noise = np.random.normal(0, 0.1, size=action_mean.shape)
            action = action_mean + noise
        else:
            action = action_mean
        
        # Clip actions to valid range
        action = np.clip(action, -1, 1)
        
        explanation = {
            'agent_id': self.agent_id,
            'state': state.tolist(),
            'action_mean': action_mean.tolist(),
            'action': action.tolist(),
            'method': 'ppo_policy',
            'reasoning': self._generate_ppo_reasoning(state, action)
        }
        
        return action, explanation
    
    def _generate_ppo_reasoning(self, state: np.ndarray, action: np.ndarray) -> str:
        """Generate reasoning for PPO action"""
        # Get value estimate
        value = self.critic.predict(state.reshape(1, -1))[0, 0]
        
        return f"Policy action with estimated state value: {value:.4f}"
    
    def store_transition(self, state, action, reward, next_state, done, log_prob):
        """Store trajectory for PPO update"""
        self.trajectories.append({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'log_prob': log_prob
        })
    
    def update(self):
        """PPO update using collected trajectories"""
        if len(self.trajectories) < 64:
            return
        
        # Compute advantages and returns
        states = np.array([t['state'] for t in self.trajectories])
        actions = np.array([t['action'] for t in self.trajectories])
        rewards = np.array([t['reward'] for t in self.trajectories])
        
        # Compute returns (simple cumulative)
        returns = np.zeros_like(rewards)
        running_return = 0
        for t in reversed(range(len(rewards))):
            running_return = rewards[t] + self.discount_factor * running_return
            returns[t] = running_return
        
        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # Get value estimates
        values = self.critic.predict(states).flatten()
        advantages = returns - values
        
        # PPO update (simplified)
        # In production, would do multiple epochs with minibatches
        
        # Update critic
        self.critic.forward(states)
        critic_loss = self.critic.backward(returns.reshape(-1, 1))
        
        # Update actor (policy gradient with clipping)
        # Simplified - full PPO would compute ratio and clip
        self.actor.forward(states)
        actor_target = actions * advantages.reshape(-1, 1)
        actor_loss = self.actor.backward(actor_target)
        
        self.losses.append(critic_loss + actor_loss)
        self.training_steps += 1
        
        # Clear trajectories
        self.trajectories = []
