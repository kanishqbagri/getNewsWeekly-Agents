import os
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from events.event_bus import EventBus
from events.event_types import Event, EventType
from utils.logger import Logger
from utils.llm_client import ClaudeClient
from utils.storage import Storage
import uuid

class BaseAgent(ABC):
    """Base class for all agents with Ralf's Loop support"""
    
    def __init__(self, agent_id: str, event_bus: EventBus):
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.logger = Logger(agent_id)
        self.claude = ClaudeClient()
        self.storage = Storage()
        self.config = self._load_config()
        self._setup_event_listeners()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML"""
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    @abstractmethod
    def _setup_event_listeners(self):
        """Subscribe to relevant events - implement in subclass"""
        pass
    
    @abstractmethod
    async def process(self, event: Event):
        """Main processing logic - implement in subclass"""
        pass
    
    async def emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Publish an event to the event bus"""
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            agent_id=self.agent_id,
            correlation_id=str(uuid.uuid4())
        )
        await self.event_bus.publish(event)
        self.logger.info(f"Emitted event: {event_type.value}")
    
    # Ralf's Loop implementation
    async def run_ralfs_loop(
        self, 
        task: Any, 
        observe_func: callable,
        reflect_func: callable,
        act_func: callable,
        max_iterations: int = 3,
        confidence_threshold: float = 0.8
    ) -> Any:
        """
        Ralf's Loop: Observe -> Reflect -> Act -> Iterate
        
        Args:
            task: Initial task/data
            observe_func: Function to observe current state
            reflect_func: Function to reflect on observation
            act_func: Function to act on reflection
            max_iterations: Maximum refinement iterations
            confidence_threshold: Stop if reflection confidence above this
        """
        observation = await observe_func(task)
        
        for iteration in range(max_iterations):
            self.logger.debug(f"Ralf's Loop iteration {iteration + 1}")
            
            # Reflect on current state
            reflection = await reflect_func(observation)
            
            # Check if confident enough to stop
            if reflection.get('confidence', 0) >= confidence_threshold:
                self.logger.info(f"Ralf's Loop converged at iteration {iteration + 1}")
                break
            
            # Act on reflection
            action_result = await act_func(reflection)
            
            # Observe new state
            observation = await observe_func(action_result)
        
        return observation
