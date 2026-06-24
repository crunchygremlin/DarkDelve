"""Agent communication service for agent-to-agent messaging."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time
from src.application.event_system.event_bus import EventBus
from src.domain.value_objects.behavior_script import BehaviorScript
class MessageType(Enum):
    """Types of messages between agents."""
    ORDER = "order"           # Leader issuing an order
    REQUEST = "request"       # Subordinate requesting orders
    REPORT = "report"         # Subordinate reporting status
    ALERT = "alert"           # Alert about threat
    PLAN_UPDATE = "plan_update"  # Plan has been updated
@dataclass
class AgentMessage:
    """A message between agents."""
    message_type: MessageType
    sender_id: str
    receiver_id: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # 0=normal, 1=urgent, 2=critical
class AgentCommunication:
    """Manages agent-to-agent communication for command chains."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus
        self._message_queues: Dict[str, List[AgentMessage]] = {}  # receiver_id → messages
        self._command_chains: Dict[str, List[str]] = {}  # leader_id → [subordinate_ids]
    
    def register_chain(self, leader_id: str, subordinate_ids: List[str]):
        """Register a command chain (leader → subordinates)."""
        self._command_chains[leader_id] = subordinate_ids
        for sub_id in subordinate_ids:
            if sub_id not in self._message_queues:
                self._message_queues[sub_id] = []
    
    def send_order(self, leader_id: str, subordinate_id: str, order: BehaviorScript):
        """Send an order from leader to subordinate."""
        message = AgentMessage(
            message_type=MessageType.ORDER,
            sender_id=leader_id,
            receiver_id=subordinate_id,
            content={
                "order_type": "execute_plan",
                "plan_script": order.to_dict(),
                "reason": order.plan_name,
            },
            priority=1
        )
        self._deliver_message(message)
        
        # Publish event
        if self._event_bus:
            self._event_bus.publish_event("order_issued", {
                "leader_id": leader_id,
                "subordinate_id": subordinate_id,
                "order": order.plan_name,
            })
    
    def broadcast_order(self, leader_id: str, order: BehaviorScript):
        """Send an order to all subordinates."""
        subordinates = self._command_chains.get(leader_id, [])
        for sub_id in subordinates:
            self.send_order(leader_id, sub_id, order)
    
    def request_orders(self, subordinate_id: str, leader_id: str, reason: str = ""):
        """Subordinate requests orders from leader."""
        message = AgentMessage(
            message_type=MessageType.REQUEST,
            sender_id=subordinate_id,
            receiver_id=leader_id,
            content={"reason": reason},
            priority=0
        )
        self._deliver_message(message)
        
        # Publish event
        if self._event_bus:
            self._event_bus.publish_event("orders_requested", {
                "subordinate_id": subordinate_id,
                "leader_id": leader_id,
                "reason": reason,
            })
    
    def report_status(self, subordinate_id: str, leader_id: str, status: Dict[str, Any]):
        """Subordinate reports status to leader."""
        message = AgentMessage(
            message_type=MessageType.REPORT,
            sender_id=subordinate_id,
            receiver_id=leader_id,
            content={"status": status},
            priority=0
        )
        self._deliver_message(message)
        
        # Publish event
        if self._event_bus:
            self._event_bus.publish_event("status_reported", {
                "subordinate_id": subordinate_id,
                "leader_id": leader_id,
                "status": status,
            })
    
    def send_alert(self, sender_id: str, receiver_ids: List[str], alert_data: Dict[str, Any]):
        """Send an alert to multiple agents."""
        for receiver_id in receiver_ids:
            message = AgentMessage(
                message_type=MessageType.ALERT,
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=alert_data,
                priority=2  # High priority for alerts
            )
            self._deliver_message(message)
        
        # Publish event
        if self._event_bus:
            self._event_bus.publish_event("alert_sent", {
                "sender_id": sender_id,
                "receiver_ids": receiver_ids,
                "alert_data": alert_data,
            })
    
    def get_messages(self, receiver_id: str) -> List[AgentMessage]:
        """Get all pending messages for an agent."""
        return self._message_queues.get(receiver_id, [])
    
    def clear_messages(self, receiver_id: str):
        """Clear all messages for an agent."""
        self._message_queues[receiver_id] = []
    
    def _deliver_message(self, message: AgentMessage):
        """Deliver a message to the receiver's queue."""
        if message.receiver_id not in self._message_queues:
            self._message_queues[message.receiver_id] = []
        self._message_queues[message.receiver_id].append(message)
        # Sort by priority (higher first)
        self._message_queues[message.receiver_id].sort(key=lambda m: m.priority, reverse=True)
    
    def get_pending_orders(self, subordinate_id: str) -> List[AgentMessage]:
        """Get all pending order messages for a subordinate."""
        messages = self.get_messages(subordinate_id)
        return [m for m in messages if m.message_type == MessageType.ORDER]
    
    def get_pending_requests(self, leader_id: str) -> List[AgentMessage]:
        """Get all pending request messages for a leader."""
        messages = []
        for receiver_id, msgs in self._message_queues.items():
            if receiver_id == leader_id:
                messages.extend([m for m in msgs if m.message_type == MessageType.REQUEST])
        return messages
    
    def has_pending_orders(self, subordinate_id: str) -> bool:
        """Check if subordinate has pending orders."""
        return len(self.get_pending_orders(subordinate_id)) > 0
    
    def has_pending_requests(self, leader_id: str) -> bool:
        """Check if leader has pending requests."""
        return len(self.get_pending_requests(leader_id)) > 0