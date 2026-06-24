"""Unit tests for AgentCommunication service."""

import pytest
from unittest.mock import Mock, MagicMock
from src.domain.services.agent_communication import (
    AgentCommunication,
    AgentMessage,
    MessageType,
)
from src.domain.value_objects.behavior_script import BehaviorScript, BehaviorNode, NodeType
from src.application.event_system.event_bus import EventBus


def create_test_script(plan_name: str = "test") -> BehaviorScript:
    """Helper to create a minimal valid BehaviorScript for testing."""
    node = BehaviorNode(
        node_id="root",
        node_type=NodeType.SEQUENCE.value,
        children=[]
    )
    return BehaviorScript(
        entity_id="test_entity",
        script_id="test_script",
        root_node=node,
        plan_name=plan_name
    )


class TestAgentCommunication:
    """Tests for AgentCommunication class."""

    def test_init_without_event_bus(self):
        """AgentCommunication can be initialized without an event bus."""
        comm = AgentCommunication()
        assert comm._event_bus is None
        assert comm._message_queues == {}
        assert comm._command_chains == {}

    def test_init_with_event_bus(self):
        """AgentCommunication can be initialized with an event bus."""
        bus = Mock(spec=EventBus)
        comm = AgentCommunication(event_bus=bus)
        assert comm._event_bus is bus

    def test_register_chain(self):
        """Register a command chain with leader and subordinates."""
        comm = AgentCommunication()
        comm.register_chain("leader1", ["sub1", "sub2"])
        
        assert "leader1" in comm._command_chains
        assert comm._command_chains["leader1"] == ["sub1", "sub2"]
        assert "sub1" in comm._message_queues
        assert "sub2" in comm._message_queues

    def test_send_order_creates_message(self):
        """send_order creates a message with correct attributes."""
        comm = AgentCommunication()
        comm.register_chain("leader", ["sub"])
        script = create_test_script("test_plan")
        
        comm.send_order("leader", "sub", script)
        
        messages = comm.get_messages("sub")
        assert len(messages) == 1
        msg = messages[0]
        assert msg.message_type == MessageType.ORDER
        assert msg.sender_id == "leader"
        assert msg.receiver_id == "sub"
        assert msg.priority == 1

    def test_send_order_publishes_event(self):
        """send_order publishes an event via the event bus."""
        bus = Mock(spec=EventBus)
        comm = AgentCommunication(event_bus=bus)
        comm.register_chain("leader", ["sub"])
        script = create_test_script("test_plan")
        
        comm.send_order("leader", "sub", script)
        
        bus.publish_event.assert_called_once_with(
            "order_issued",
            {"leader_id": "leader", "subordinate_id": "sub", "order": "test_plan"},
        )

    def test_broadcast_order_sends_to_all(self):
        """broadcast_order sends order to all subordinates."""
        comm = AgentCommunication()
        comm.register_chain("leader", ["sub1", "sub2"])
        script = create_test_script("test_plan")
        
        comm.broadcast_order("leader", script)
        
        assert len(comm.get_messages("sub1")) == 1
        assert len(comm.get_messages("sub2")) == 1

    def test_request_orders_creates_request_message(self):
        """request_orders creates a REQUEST message."""
        comm = AgentCommunication()
        comm.request_orders("sub", "leader", "need help")
        
        messages = comm.get_messages("leader")
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.REQUEST
        assert messages[0].sender_id == "sub"
        assert messages[0].receiver_id == "leader"

    def test_report_status_creates_report_message(self):
        """report_status creates a REPORT message."""
        comm = AgentCommunication()
        comm.report_status("sub", "leader", {"health": 100})
        
        messages = comm.get_messages("leader")
        assert len(messages) == 1
        assert messages[0].message_type == MessageType.REPORT

    def test_send_alert_to_multiple_receivers(self):
        """send_alert sends to multiple receivers."""
        comm = AgentCommunication()
        comm.send_alert("sender", ["rec1", "rec2"], {"threat": "dragon"})
        
        assert len(comm.get_messages("rec1")) == 1
        assert len(comm.get_messages("rec2")) == 1
        assert comm.get_messages("rec1")[0].message_type == MessageType.ALERT

    def test_message_priority_sorting(self):
            """Messages are sorted by priority (high to low)."""
            comm = AgentCommunication()
            comm.register_chain("leader", ["sub"])
            script = create_test_script("test")
            
            # Send messages with different priorities
            comm.send_order("leader", "sub", script)         # priority 1
            comm.send_alert("leader", ["sub"], {"alert": 1})  # priority 2, pass list of receivers
            
            messages = comm.get_messages("sub")
            # Both messages should be present
            assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}: {[m.message_type for m in messages]}"
            # Higher priority first (alert with priority 2 should be first)
            assert messages[0].message_type == MessageType.ALERT
            assert messages[1].message_type == MessageType.ORDER

    def test_get_pending_orders(self):
        """get_pending_orders returns only ORDER messages."""
        comm = AgentCommunication()
        comm.register_chain("leader", ["sub"])
        script = create_test_script("test")
        
        comm.send_order("leader", "sub", script)
        comm.report_status("sub", "leader", {"status": "ok"})
        
        orders = comm.get_pending_orders("sub")
        assert len(orders) == 1
        assert orders[0].message_type == MessageType.ORDER

    def test_get_pending_requests(self):
        """get_pending_requests returns only REQUEST messages for a leader."""
        comm = AgentCommunication()
        comm.request_orders("sub1", "leader")
        comm.request_orders("sub2", "leader")
        comm.send_order("leader", "sub1", create_test_script("t"))
        
        requests = comm.get_pending_requests("leader")
        assert len(requests) == 2

    def test_has_pending_orders(self):
        """has_pending_orders returns correct boolean."""
        comm = AgentCommunication()
        comm.register_chain("leader", ["sub"])
        
        assert comm.has_pending_orders("sub") is False
        comm.send_order("leader", "sub", create_test_script("t"))
        assert comm.has_pending_orders("sub") is True

    def test_has_pending_requests(self):
        """has_pending_requests returns correct boolean."""
        comm = AgentCommunication()
        
        assert comm.has_pending_requests("leader") is False
        comm.request_orders("sub", "leader")
        assert comm.has_pending_requests("leader") is True

    def test_clear_messages(self):
        """clear_messages removes all messages for a receiver."""
        comm = AgentCommunication()
        comm.register_chain("leader", ["sub"])
        comm.send_order("leader", "sub", create_test_script("t"))
        
        assert len(comm.get_messages("sub")) == 1
        comm.clear_messages("sub")
        assert len(comm.get_messages("sub")) == 0