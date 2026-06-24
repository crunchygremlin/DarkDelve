# Multi-Step Behavior Scripts with Agent-to-Agent Communication

## Problem Statement

The current behavior system has three gaps:

1. **No action execution**: `BehaviorScriptService.evaluate_script()` returns `BehaviorAction` objects, but nothing executes them.
2. **No multi-step planning**: Behavior scripts are single-decision trees — they can't express "if player is visible, attack; otherwise search last known position; if not found, return to patrol" as a coherent multi-step plan.
3. **No agent-to-agent communication**: Leaders can't issue orders to subordinates. There's no chain of command, no squad coordination, no commander-to-minion communication.

## Architecture Overview

The solution introduces three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: PLAN GENERATOR (LLM-based)                             │
│  - Takes PerceptionStatus + SocialContext                       │
│  - Generates multi-step BehaviorScript trees                     │
│  - Creates new plans dynamically based on situation             │
│  - Leaders generate plans for themselves AND their subordinates  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: BEHAVIOR ENGINE (tree walker)                          │
│  - Walks BehaviorScript trees each tick                         │
│  - Evaluates conditions against perception + player knowledge    │
│  - Returns BehaviorActions for execution                        │
│  - Supports SEQUENCE nodes for multi-step execution             │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: ACTION DISPATCHER (service router)                     │
│  - Executes BehaviorActions: attack, move, flee, etc.           │
│  - Routes to CombatService, MovementService, SocialService      │
│  - Publishes events via EventBus                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AGENT-TO-AGENT COMMUNICATION LAYER                             │
│  - CommanderAgent issues CommanderOrders to subordinates         │
│  - Orders are BehaviorScripts injected into subordinate          │
│    BehaviorComponent                                             │
│  - Chain of command: Overall Commander → Squad Leader → Minion   │
│  - Orders carry conditions: "attack if player visible,          │
│    otherwise hold position"                                      │
│  - Subordinates can request orders when they lack a plan         │
│  - Loyalty affects order compliance                             │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Create `ActionDispatcher` Service

**File:** `src/domain/services/action_dispatcher.py`

Routes `BehaviorAction` objects to the appropriate game service.

```python
class ActionDispatcher:
    """Executes BehaviorActions by routing to the appropriate service."""
    
    def __init__(
        self,
        combat_service: CombatService,
        movement_service: MovementService,
        social_service: SocialService,
        event_bus: Optional[EventBus] = None,
    ):
        self.combat_service = combat_service
        self.movement_service = movement_service
        self.social_service = social_service
        self.event_bus = event_bus
    
    def execute(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Execute a behavior action for an entity."""
        handler = self._get_handler(action.action_type)
        return handler(entity, action, all_entities)
```

**Action handlers:**

| Handler | Description | Key Logic |
|---------|-------------|-----------|
| `_handle_attack` | Attack a target | Find target → validate range → `combat_service.execute_attack()` |
| `_handle_flee` | Flee from threat | Calculate opposite direction → validate → `movement_service.move_entity()` |
| `_handle_patrol` | Follow patrol route | Get patrol points → move to next → advance index |
| `_handle_move_to` | Move to position | Parse position → validate → `movement_service.move_entity()` |
| `_handle_follow_leader` | Follow leader | Find leader → move adjacent |
| `_handle_guard_position` | Hold position | Move to guard point, then hold |
| `_handle_call_allies` | Call for help | Find nearby allies → publish `ally_called` event |
| `_handle_pickup_item` | Pick up item | Validate reach → add to inventory |
| `_handle_gift_item` | Give item to ally | Transfer item → `social_service.process_gift()` |
| `_handle_wait` | Do nothing | Record action only |
| `_handle_search` | Search area | Move to last known position or wander |
| `_handle_hide` | Hide | Set state to hiding, no movement |
| `_handle_use_item` | Use inventory item | Find item → apply effect |
| `_handle_trade` | Trade with entity | Exchange items |
| `_handle_promote_minion` | Promote subordinate | Verify leader → `social_service.process_promotion()` |
| `_handle_give_orders` | Issue orders to subordinate | Verify authority → inject BehaviorScript into subordinate |

### Step 2: Enhance BehaviorScript for Multi-Step Plans

**File:** `src/domain/value_objects/behavior_script.py`

Add support for multi-step plans with memory and persistent state:

```python
@dataclass
class BehaviorScript:
    """A complete behavior script for an entity."""
    entity_id: str
    script_id: str
    root_node: BehaviorNode
    valid_conditions: List[str] = field(default_factory=list)
    valid_actions: List[str] = field(default_factory=list)
    created_at: float = 0.0
    version: int = 1
    # NEW: Multi-step plan support
    is_plan: bool = False  # True if this is a multi-step plan vs single-decision
    plan_name: str = ""  # "attack_player", "defend_position", "search_and_destroy"
    plan_memory: Dict[str, Any] = field(default_factory=dict)
    # plan_memory stores: current_step, last_search_pos, attack_count, etc.
```

**File:** `src/domain/services/behavior_script_service.py`

Enhance the tree walker to support multi-step execution:

```python
class BehaviorScriptService:
    """Evaluates BehaviorScripts with multi-step plan support."""
    
    def evaluate_script(
        self,
        script: BehaviorScript,
        perception: PerceptionStatus,
        entity_state: Dict[str, Any]
    ) -> Optional[BehaviorAction]:
        """
        Evaluate a behavior script and return the next action.
        
        For multi-step plans (is_plan=True), this walks the tree and
        returns the appropriate action based on the current plan step.
        """
        if not script.root_node:
            return None
        
        # For plans, update plan_memory with current perception
        if script.is_plan:
            self._update_plan_memory(script, perception, entity_state)
        
        return self._evaluate_node(script.root_node, perception, entity_state, script.plan_memory)
    
    def _update_plan_memory(self, script: BehaviorScript, perception: PerceptionStatus, entity_state: Dict[str, Any]):
        """Update plan memory with current state for multi-step tracking."""
        memory = script.plan_memory
        
        # Track player sightings
        if perception.can_see_player and perception.player_last_known_position:
            memory["last_seen_player_pos"] = perception.player_last_known_position
            memory["last_seen_tick"] = entity_state.get("tick", 0)
            memory["player_seen_count"] = memory.get("player_seen_count", 0) + 1
        
        # Track health at decision points
        memory["last_health_pct"] = entity_state.get("health_pct", 1.0)
        
        # Track if we've already attacked this plan
        memory["has_attacked_this_plan"] = memory.get("has_attacked_this_plan", False)
```

### Step 3: Create Plan Generator (LLM-Based)

**File:** `src/domain/services/plan_generator.py`

This is the LLM-powered service that creates new plans dynamically:

```python
class PlanGenerator:
    """Generates multi-step behavior plans using LLM."""
    
    def __init__(self, llm_client: Any, behavior_script_service: BehaviorScriptService):
        self._llm = llm_client
        self._script_service = behavior_script_service
    
    def generate_plan(
        self,
        entity: Any,
        perception: PerceptionStatus,
        social_context: Dict[str, Any],
        goal: str,  # "attack_player", "defend_area", "escort_leader", etc.
        all_entities: List[Any]
    ) -> BehaviorScript:
        """
        Generate a multi-step behavior plan for an entity.
        
        The plan is a BehaviorScript with is_plan=True that encodes
        conditional multi-step logic like:
        1. If player visible → attack
        2. Else if heard player → move to last known position
        3. Else if health low → flee
        4. Else → patrol
        """
        # Build prompt with perception, social context, and goal
        prompt = self._build_plan_prompt(entity, perception, social_context, goal, all_entities)
        
        # Get LLM response (JSON tree)
        response = self._llm.generate(prompt)
        
        # Parse into BehaviorScript
        script = self._script_service.parse_script_from_json(response)
        script.is_plan = True
        script.plan_name = goal
        
        return script
    
    def _build_plan_prompt(
        self,
        entity: Any,
        perception: PerceptionStatus,
        social_context: Dict[str, Any],
        goal: str,
        all_entities: List[Any]
    ) -> str:
        """Build a prompt for plan generation."""
        return f"""You are generating a behavior plan for a {getattr(entity, 'mob_type', 'creature')} named {entity.name}.

GOAL: {goal}

CURRENT PERCEPTION:
- Can see player: {perception.can_see_player}
- Can hear player: {perception.can_hear_player}
- Player distance: {perception.player_distance_estimate}
- Player last known position: {perception.player_last_known_position}
- Visible threats: {len(perception.visible_threats)}
- Environment danger: {perception.environment_danger}

SOCIAL CONTEXT:
{social_context}

AVAILABLE ACTIONS: attack, flee, patrol, move_to, call_allies, follow_leader, guard_position, pickup_item, search, hide, wait

Generate a multi-step behavior plan as a JSON tree. The plan should handle:
1. Primary objective (the goal)
2. Fallback conditions (what to if primary fails)
3. Emergency conditions (low health, outnumbered, etc.)

Return JSON in this format:
{{
  "entity_id": "{entity.id}",
  "root_node": {{
    "node_id": "root",
    "node_type": "selector",
    "children": [
      {{
        "node_id": "emergency_flee",
        "node_type": "action",
        "conditions": [{{"condition_type": "health_below", "operator": "<", "value": 0.2}}],
        "action": {{"action_type": "flee", "target": "player"}}
      }},
      {{
        "node_id": "primary_attack",
        "node_type": "action",
        "conditions": [{{"condition_type": "can_see_player"}}],
        "action": {{"action_type": "attack", "target": "player"}}
      }},
      {{
        "node_id": "search_last_known",
        "node_type": "action",
        "conditions": [{{"condition_type": "can_hear_player"}}],
        "action": {{"action_type": "search"}}
      }},
      {{
        "node_id": "default_patrol",
        "node_type": "action",
        "action": {{"action_type": "patrol"}}
      }}
    ]
  }}
}}"""
```

### Step 4: Create Agent Communication System

**File:** `src/domain/services/agent_communication.py`

Handles agent-to-agent messaging for command chains:

```python
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
            self._event_bus.publish("order_issued", {
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
```

### Step 5: Enhance CommanderAgent for Chain of Command

**File:** `src/domain/agents/commander_agent.py`

Enhance the existing `CommanderAgent` to support chain of command:

```python
class CommanderAgent(Agent):
    """Agent for commanding NPCs in tactical combat."""
    
    def __init__(self, entity, agent_type=AgentType.COMMANDER, name=None, home_position=None):
        super().__init__(entity, agent_type, name)
        self.home_position = home_position or (entity.x, entity.y)
        self._subordinates: List[str] = []
        self._pending_orders: Dict[str, CommanderOrder] = {}
        # NEW: Chain of command
        self._superior_id: Optional[str] = None  # This commander's leader (if any)
        self._command_level: int = 0  # 0=overall commander, 1=squad leader, 2=unit leader
        self._plan_generator: Optional[PlanGenerator] = None
        self._communication: Optional[AgentCommunication] = None
    
    def set_chain_of_command(self, superior_id: Optional[str], command_level: int):
        """Set this commander's position in the chain of command."""
        self._superior_id = superior_id
        self._command_level = command_level
    
    def set_services(self, plan_generator: PlanGenerator, communication: AgentCommunication):
        """Inject required services."""
        self._plan_generator = plan_generator
        self._communication = communication
    
    def decide(self, perception: PerceptionResult) -> AgentAction:
        """
        Make a tactical decision.
        
        Overall commanders (level 0) generate plans and issue orders.
        Squad leaders (level 1) execute orders and adapt to local conditions.
        Unit leaders (level 2) execute orders with minimal adaptation.
        """
        # Check for orders from superior
        if self._communication and self._superior_id:
            messages = self._communication.get_messages(self.entity_id)
            for msg in messages:
                if msg.message_type == MessageType.ORDER:
                    self._execute_order(msg)
        
        # Generate or adapt plan based on command level
        if self._command_level == 0:
            return self._overall_commander_decision(perception)
        elif self._command_level == 1:
            return self._squad_leader_decision(perception)
        else:
            return self._unit_leader_decision(perception)
    
    def _overall_commander_decision(self, perception: PerceptionResult) -> AgentAction:
        """Overall commander: generate plans and issue orders to subordinates."""
        # Generate a new plan based on current situation
        if self._should_replan(perception):
            plan = self._plan_generator.generate_plan(
                entity=self.entity,
                perception=perception,
                social_context=self._get_social_context(),
                goal=self._determine_strategic_goal(perception),
                all_entities=self._get_all_entities()
            )
            
            # Broadcast plan to all subordinates
            if self._communication:
                self._communication.broadcast_order(self.entity.id, plan)
            
            # Set own script
            behavior_comp = self.entity.get_component("behavior")
            if behavior_comp:
                behavior_comp.set_script(plan)
        
        return AgentAction(action_type=ActionType.HOLD_POSITION)
    
    def _squad_leader_decision(self, perception: PerceptionResult) -> AgentAction:
        """Squad leader: execute orders with local adaptation."""
        # Check if current order is still valid
        current_order = self._get_current_order()
        if current_order and self._order_is_valid(current_order, perception):
            return self._execute_current_order(current_order, perception)
        
        # If order is invalid, adapt locally
        return self._adapt_locally(perception)
    
    def _should_replan(self, perception: PerceptionResult) -> bool:
        """Determine if a new plan is needed."""
        behavior_comp = self.entity.get_component("behavior")
        if not behavior_comp or not behavior_comp.current_script:
            return True
        
        current_script = behavior_comp.current_script
        if not current_script.is_plan:
            return True
        
        # Replan if situation has changed significantly
        if perception.can_see_player and not current_script.plan_memory.get("has_attacked_this_plan"):
            return True
        
        if perception.environment_danger > 0.7 and current_script.plan_name != "defend_position":
            return True
        
        return False
    
    def _determine_strategic_goal(self, perception: PerceptionResult) -> str:
        """Determine the strategic goal based on perception."""
        if perception.can_see_player:
            health_pct = perception.health_percent
            if health_pct > 0.7:
                return "attack_player"
            elif health_pct > 0.3:
                return "harass_player"
            else:
                return "retreat_and_regroup"
        
        if perception.visible_entities:
            return "defend_area"
        
        return "patrol_and_guard"
    
    def _execute_order(self, message: AgentMessage):
        """Execute an order received from superior."""
        order_data = message.content
        plan_script = BehaviorScript.from_dict(order_data["plan_script"])
        
        behavior_comp = self.entity.get_component("behavior")
        if behavior_comp:
            behavior_comp.set_script(plan_script)
        
        # Report receipt to superior
        if self._communication and self._superior_id:
            self._communication.report_status(
                self.entity.id,
                self._superior_id,
                {"status": "order_received", "order": plan_script.plan_name}
            )
```

### Step 6: Integrate into EntityAIOrchestrator

**File:** `src/domain/services/entity_ai_orchestrator.py`

```python
class EntityAIOrchestrator:
    """Orchestrates the full AI pipeline each game tick."""
    
    def __init__(
        self,
        perception_service: PerceptionService,
        behavior_service: BehaviorScriptService,
        social_service: SocialService,
        player_profile_service: PlayerProfileService,
        llm_logger: LLMLogger,
        action_dispatcher: ActionDispatcher,      # Layer 1
        plan_generator: PlanGenerator,             # Layer 3
        agent_communication: AgentCommunication,   # Agent-to-agent
        event_bus=None,
    ):
        self.perception_service = perception_service
        self.behavior_service = behavior_service
        self.social_service = social_service
        self.player_profile_service = player_profile_service
        self.llm_logger = llm_logger
        self.action_dispatcher = action_dispatcher
        self.plan_generator = plan_generator
        self.agent_communication = agent_communication
        self.event_bus = event_bus
        self._tick = 0
    
    def tick(self, entities, player, game_map, items):
        """Main AI tick — called each game frame."""
        self._tick += 1
        
        # 1. Update perception for all entities
        self._update_perception(entities, player, game_map, items)
        
        # 2. Process agent communication (deliver messages)
        self._process_communication(entities)
        
        # 3. Evaluate behavior scripts and execute actions
        results = self._evaluate_behaviors(entities)
        
        # 4. Check for desertions/betrayals
        self._check_social_events(entities)
        
        # 5. Generate new plans for leaders if needed
        self._generate_plans(entities, player, game_map)
        
        return results
    
    def _process_communication(self, entities):
        """Process agent-to-agent messages."""
        for entity in entities:
            agent = self._get_agent_for_entity(entity)
            if not agent:
                continue
            
            messages = self.agent_communication.get_messages(entity.id)
            for msg in messages:
                if msg.message_type == MessageType.ORDER:
                    self._apply_order_to_entity(entity, msg)
                elif msg.message_type == MessageType.REQUEST:
                    self._handle_request(entity, msg)
                elif msg.message_type == MessageType.ALERT:
                    self._handle_alert(entity, msg)
    
    def _apply_order_to_entity(self, entity: Any, order_msg: AgentMessage):
        """Apply an order (BehaviorScript) to an entity."""
        script_data = order_msg.content.get("plan_script")
        if not script_data:
            return
        
        script = BehaviorScript.from_dict(script_data)
        behavior_comp = entity.get_component("behavior")
        if behavior_comp:
            behavior_comp.set_script(script)
    
    def _generate_plans(self, entities, player, game_map):
        """Generate new plans for leader entities when needed."""
        for entity in entities:
            social_comp = entity.get_component("social")
            if not social_comp or not social_comp.is_leader:
                continue
            
            behavior_comp = entity.get_component("behavior")
            if not behavior_comp:
                continue
            
            # Check if current plan is stale or missing
            needs_new_plan = (
                not behavior_comp.current_script
                or not behavior_comp.current_script.is_plan
                or self._tick - behavior_comp.last_evaluated_tick > 50
            )
            
            if needs_new_plan:
                perception = self._get_perception(entity)
                if perception:
                    plan = self.plan_generator.generate_plan(
                        entity=entity,
                        perception=perception,
                        social_context=self._get_social_context(entity),
                        goal=self._determine_goal(entity, perception),
                        all_entities=entities
                    )
                    behavior_comp.set_script(plan)
                    
                    # Broadcast to subordinates
                    subordinates = self._get_subordinates(entity)
                    for sub_id in subordinates:
                        self.agent_communication.send_order(entity.id, sub_id, plan)
    
    def _evaluate_behaviors(self, entities) -> List[Dict[str, Any]]:
        """Evaluate behavior scripts and execute resulting actions."""
        results = []
        for entity in entities:
            behavior_comp = entity.get_component("behavior")
            perception_comp = entity.get_component("perception")
            social_comp = entity.get_component("social")

            if not behavior_comp or not behavior_comp.current_script:
                continue
            if not behavior_comp.should_evaluate(self._tick):
                continue

            perception = perception_comp.current_status if perception_comp else None
            if not perception:
                continue

            entity_state = self._build_entity_state(entity, social_comp)
            action = self.behavior_service.evaluate_script(
                behavior_comp.current_script, perception, entity_state
            )
            behavior_comp.record_evaluation(self._tick, action)
            
            if action:
                # Execute the action via dispatcher
                execution_result = self.action_dispatcher.execute(
                    entity, action, entities
                )
                results.append({
                    "entity": entity,
                    "action": action,
                    "result": execution_result
                })
        
        return results
```

### Step 7: Add Tests

**File:** `tests/test_action_dispatcher.py`

Test cases:
1. `test_attack_action_triggers_combat` — attack action calls combat service
2. `test_flee_action_moves_entity_away` — flee action moves entity away from threat
3. `test_patrol_action_moves_to_next_point` — patrol action advances along patrol route
4. `test_wait_action_no_op` — wait action does nothing
5. `test_unknown_action_returns_error` — unknown action type returns failure
6. `test_attack_target_not_found` — attack with invalid target returns failure
7. `test_flee_calculates_correct_position` — flee position is opposite direction from threat
8. `test_move_to_validates_position` — move_to validates bounds and blocking
9. `test_gift_item_modifies_loyalty` — gift action calls social service
10. `test_action_publishes_event` — successful actions publish events via bus

**File:** `tests/test_agent_communication.py`

Test cases:
1. `test_send_order_delivers_message` — order is delivered to subordinate
2. `test_broadcast_order_sends_to_all` — broadcast reaches all subordinates
3. `test_request_orders_delivers_to_leader` — request reaches leader
4. `test_message_priority_ordering` — urgent messages come first
5. `test_order_applies_script_to_entity` — applying order sets behavior script
6. `test_chain_of_command_registration` — chain registration works correctly

**File:** `tests/test_plan_generator.py`

Test cases:
1. `test_generate_attack_plan` — generates plan with attack action
2. `test_generate_defend_plan` — generates plan with defend action
3. `test_plan_has_is_plan_flag` — generated plans have is_plan=True
4. `test_plan_memory_tracks_state` — plan memory updates with perception
5. `test_multi_step_conditions` — plan has multiple conditional branches

### Step 8: Wire into GameSession

**File:** `src/application/game_session/game_session.py`

Add orchestrator integration:

```python
class GameSession:
    def __init__(self, player, session_id=None):
        # ... existing code ...
        
        # Initialize AI services
        self._init_ai_services()
    
    def _init_ai_services(self):
        """Initialize the AI service stack."""
        from src.domain.services.action_dispatcher import ActionDispatcher
        from src.domain.services.plan_generator import PlanGenerator
        from src.domain.services.agent_communication import AgentCommunication
        
        # Create services
        self.action_dispatcher = ActionDispatcher(
            combat_service=CombatService(),
            movement_service=MovementService(),
            social_service=SocialService(),
            event_bus=None  # TODO: inject event bus
        )
        
        self.agent_communication = AgentCommunication(event_bus=None)
        
        # Orchestrator will be created with proper dependencies
        # when game map and repositories are available
    
    def update(self, delta_time: float):
        """Update game state each frame."""
        # Update player
        self.player.update(delta_time)
        
        # Update entities via orchestrator
        if hasattr(self, 'ai_orchestrator') and self.ai_orchestrator:
            self.ai_orchestrator.tick(
                self.entities,
                self.player,
                self.game_map,
                self.items
            )
        
        # Update play time
        self.update_play_time(int(delta_time))
```

## Data Flow Diagram

```
Game Loop (tick)
    ↓
EntityAIOrchestrator.tick()
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. _update_perception()                                     │
│    PerceptionService.compute_perception() → PerceptionStatus│
├─────────────────────────────────────────────────────────────┤
│ 2. _process_communication()                                 │
│    Deliver AgentMessages (orders, requests, alerts)          │
│    Apply received orders to BehaviorComponent                │
├─────────────────────────────────────────────────────────────┤
│ 3. _generate_plans() [for leaders only]                     │
│    PlanGenerator.generate_plan() → BehaviorScript(is_plan)  │
│    Broadcast plan to subordinates via AgentCommunication     │
├─────────────────────────────────────────────────────────────┤
│ 4. _evaluate_behaviors()                                    │
│    BehaviorScriptService.evaluate_script() → BehaviorAction  │
│    ActionDispatcher.execute() → game state changes          │
├─────────────────────────────────────────────────────────────┤
│ 5. _check_social_events()                                   │
│    SocialService.check_desertion/betrayal()                  │
└─────────────────────────────────────────────────────────────┘
    ↓
EventBus.publish() → UI updates, sound, telemetry
```

## Command Chain Flow

```
Overall Commander (level 0)
    │
    ├── perceives battlefield
    ├── generates strategic plan via LLM
    ├── broadcasts plan to Squad Leaders
    │
    ├──→ Squad Leader A (level 1)
    │       │
    │       ├── receives plan from Commander
    │       ├── adapts to local conditions
    │       ├── executes or modifies plan
    │       │
    │       ├──→ Unit Leader A1 (level 2)
    │       │       └── executes order with minimal adaptation
    │       │
    │       └──→ Unit Leader A2 (level 2)
    │               └── executes order with minimal adaptation
    │
    └──→ Squad Leader B (level 1)
            │
            ├── receives plan from Commander
            ├── adapts to local conditions
            │
            └──→ Unit Leader B1 (level 2)
                    └── executes order with minimal adaptation
```

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/domain/services/action_dispatcher.py` | **CREATE** | Routes BehaviorActions to game services |
| `src/domain/services/plan_generator.py` | **CREATE** | LLM-based multi-step plan generation |
| `src/domain/services/agent_communication.py` | **CREATE** | Agent-to-agent messaging for command chains |
| `src/domain/services/behavior_script_service.py` | **MODIFY** | Add multi-step plan evaluation with plan_memory |
| `src/domain/value_objects/behavior_script.py` | **MODIFY** | Add is_plan, plan_name, plan_memory fields |
| `src/domain/agents/commander_agent.py` | **MODIFY** | Add chain of command, plan generation, communication |
| `src/domain/services/entity_ai_orchestrator.py` | **MODIFY** | Integrate all layers, add plan generation and communication |
| `src/application/game_session/game_session.py` | **MODIFY** | Initialize AI services, call orchestrator in update |
| `tests/test_action_dispatcher.py` | **CREATE** | Tests for ActionDispatcher |
| `tests/test_agent_communication.py` | **CREATE** | Tests for AgentCommunication |
| `tests/test_plan_generator.py` | **CREATE** | Tests for PlanGenerator |

## Dependencies

All dependencies already exist:
- `CombatService` (`src/domain/services/combat_service.py`)
- `MovementService` (`src/domain/services/movement_service.py`)
- `SocialService` (`src/domain/services/social_service.py`)
- `EventBus` (`src/application/event_system/event_bus.py`)
- `BehaviorScriptService` (`src/domain/services/behavior_script_service.py`)
- `BehaviorScript` / `BehaviorAction` (`src/domain/value_objects/behavior_script.py`)
- `CommanderAgent` (`src/domain/agents/commander_agent.py`)
- `LLMAgent` (`src/domain/agents/llm_agent.py`)

## Success Criteria

1. **Action execution**: When a behavior script returns `attack`, the target takes damage
2. **Multi-step plans**: Plans with conditional branches execute correctly based on perception
3. **Dynamic plan creation**: Leaders generate new plans when situation changes
4. **Agent communication**: Orders from leaders are received and applied by subordinates
5. **Chain of command**: Overall Commander → Squad Leader → Minion communication works
6. **Order compliance**: Subordinates follow orders based on loyalty level
7. **Event publishing**: All actions publish events via the event bus
8. **Backward compatibility**: Existing AI behavior works when no behavior script is set
9. **Tests**: All new code has passing tests
