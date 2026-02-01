import asyncio
from collections import defaultdict, deque
from typing import Callable, List, Optional
from datetime import datetime
from .event_types import Event, EventType

class EventBus:
    """Thread-safe singleton event bus for agent communication"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.subscribers = defaultdict(list)
        self.event_history = deque(maxlen=10000)
        self._initialized = True
    
    async def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        async with self._lock:
            self.subscribers[event_type].append(callback)
    
    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        async with self._lock:
            self.event_history.append(event)
            
        # Call all subscribers
        for callback in self.subscribers.get(event.event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in subscriber: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Get event history, optionally filtered by type"""
        if event_type:
            return [e for e in self.event_history if e.event_type == event_type]
        return list(self.event_history)
