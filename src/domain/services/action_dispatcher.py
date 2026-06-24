"""Action dispatcher for executing behavior actions."""

from typing import Any, Dict, List, Optional
from src.domain.services.combat_service import CombatService
from src.domain.services.movement_service import MovementService
from src.domain.services.social_service import SocialService
from src.application.event_system.event_bus import EventBus
from src.domain.value_objects.behavior_script import BehaviorAction, ActionType
from src.domain.value_objects.position import Position
from src.domain.value_objects.combat_event import CombatEventType
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
    
    def _get_handler(self, action_type: str):
        """Get the handler method for an action type."""
        handlers = {
            ActionType.ATTACK.value: self._handle_attack,
            ActionType.FLEE.value: self._handle_flee,
            ActionType.PATROL.value: self._handle_patrol,
            ActionType.MOVE_TO.value: self._handle_move_to,
            ActionType.CALL_ALLIES.value: self._handle_call_allies,
            ActionType.FOLLOW_LEADER.value: self._handle_follow_leader,
            ActionType.GUARD_POSITION.value: self._handle_guard_position,
            ActionType.PICKUP_ITEM.value: self._handle_pickup_item,
            ActionType.GIFT_ITEM.value: self._handle_gift_item,
            ActionType.GIVE_ORDERS.value: self._handle_give_orders,
            ActionType.WAIT.value: self._handle_wait,
            ActionType.SEARCH.value: self._handle_search,
            ActionType.HIDE.value: self._handle_hide,
            ActionType.USE_ITEM.value: self._handle_use_item,
            ActionType.TRADE.value: self._handle_trade,
            ActionType.PROMOTE_MINION.value: self._handle_promote_minion,
        }
        return handlers.get(action_type, self._handle_unknown)
    
    def _handle_attack(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Attack a target."""
        target_id = action.target
        if not target_id:
            return {"success": False, "message": "No target specified for attack"}
        
        # Find target entity
        target = None
        for e in all_entities:
            if e.id == target_id and hasattr(e, 'is_alive') and e.is_alive():
                target = e
                break
        
        if not target:
            return {"success": False, "message": f"Target {target_id} not found or not alive"}
        
        # Check if target is in range (simplified - assumes adjacent)
        if hasattr(entity, 'position') and hasattr(target, 'position'):
            distance = entity.position.distance_to(target.position)
            if distance > 1:
                return {"success": False, "message": f"Target too far away ({distance:.1f} units)"}
        
        # Execute attack
        try:
            result = self.combat_service.execute_attack(entity, target)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event(CombatEventType.HIT if result.get("hit") else CombatEventType.MISS)
            
            return {
                "success": True,
                "message": f"Attacked {target.name} for {result.get('damage', 0)} damage",
                "damage": result.get("damage", 0),
                "hit": result.get("hit", False),
                "critical": result.get("critical", False),
                "target_health": result.get("target_health", 0)
            }
        except Exception as e:
            return {"success": False, "message": f"Attack failed: {str(e)}"}
    
    def _handle_flee(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Flee from threat."""
        # Find threat (target or nearest enemy)
        threat = None
        threat_distance = float('inf')
        
        for e in all_entities:
            if e.id == entity.id:
                continue
            if hasattr(e, 'is_alive') and not e.is_alive():
                continue
            if hasattr(e, 'position') and hasattr(entity, 'position'):
                distance = entity.position.distance_to(e.position)
                if distance < threat_distance:
                    threat_distance = distance
                    threat = e
        
        if not threat:
            return {"success": False, "message": "No threat to flee from"}
        
        # Calculate flee position (opposite direction from threat)
        if hasattr(entity, 'position') and hasattr(threat, 'position'):
            dx = entity.position.x - threat.position.x
            dy = entity.position.y - threat.position.y
            
            # Normalize to unit vector
            distance = (dx**2 + dy**2)**0.5
            if distance > 0:
                dx = (dx / distance) * 5  # Flee distance
                dy = (dy / distance) * 5
            
            flee_pos = Position(int(entity.position.x + dx), int(entity.position.y + dy))
            
            # Validate position
            if self.movement_service.can_move_to(entity, flee_pos):
                # Move entity
                success = self.movement_service.move_entity(entity, flee_pos)
                if success:
                    return {
                        "success": True,
                        "message": f"Fled from {threat.name} to {flee_pos.x},{flee_pos.y}",
                        "from_position": {"x": entity.position.x, "y": entity.position.y},
                        "to_position": {"x": flee_pos.x, "y": flee_pos.y}
                    }
                else:
                    return {"success": False, "message": "Could not move to flee position"}
            else:
                return {"success": False, "message": "Flee position is blocked or out of bounds"}
        
        return {"success": False, "message": "Cannot calculate flee position"}
    
    def _handle_patrol(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Follow patrol route."""
        # Get patrol points from AI component
        ai_comp = entity.get_component("ai") if hasattr(entity, 'get_component') else None
        patrol_points = []
        if ai_comp and hasattr(ai_comp, 'patrol_points'):
            patrol_points = ai_comp.patrol_points
        
        if not patrol_points:
            # No patrol points, wander randomly
            return self._handle_wander(entity, action, all_entities)
        
        # Move to next patrol point
        current_pos = entity.position if hasattr(entity, 'position') else None
        if not current_pos:
            return {"success": False, "message": "Entity has no position"}
        
        # Find closest patrol point
        next_point = None
        min_distance = float('inf')
        for point in patrol_points:
            distance = current_pos.distance_to(point)
            if distance < min_distance:
                min_distance = distance
                next_point = point
        
        if next_point and min_distance < 1.0:
            # Reached patrol point, remove it
            if ai_comp and hasattr(ai_comp, 'patrol_points'):
                ai_comp.patrol_points.remove(next_point)
            return {"success": True, "message": f"Reached patrol point {next_point.x},{next_point.y}", "completed": True}
        
        # Move towards patrol point
        if self.movement_service.can_move_to(entity, next_point):
            success = self.movement_service.move_entity(entity, next_point)
            if success:
                return {
                    "success": True,
                    "message": f"Moving to patrol point {next_point.x},{next_point.y}",
                    "target_position": {"x": next_point.x, "y": next_point.y}
                }
            else:
                return {"success": False, "message": "Could not move to patrol point"}
        
        return {"success": False, "message": "Patrol point is blocked or out of bounds"}
    
    def _handle_move_to(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Move to specific position."""
        if not action.parameters or "position" not in action.parameters:
            return {"success": False, "message": "No target position specified for move_to"}
        
        target_pos = action.parameters["position"]
        if isinstance(target_pos, dict):
            target_pos = Position(target_pos.get("x", 0), target_pos.get("y", 0))
        elif isinstance(target_pos, (list, tuple)):
            target_pos = Position(target_pos[0], target_pos[1])
        
        if self.movement_service.can_move_to(entity, target_pos):
            success = self.movement_service.move_entity(entity, target_pos)
            if success:
                return {
                    "success": True,
                    "message": f"Moved to {target_pos.x},{target_pos.y}",
                    "target_position": {"x": target_pos.x, "y": target_pos.y}
                }
            else:
                return {"success": False, "message": "Could not move to target position"}
        
        return {"success": False, "message": "Target position is blocked or out of bounds"}
    
    def _handle_call_allies(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Call for help from nearby allies."""
        # Find nearby allies
        allies = []
        for e in all_entities:
            if e.id == entity.id:
                continue
            if hasattr(e, 'is_alive') and not e.is_alive():
                continue
            # Check if entity is an ally (same social structure or neutral)
            if self._is_ally(entity, e):
                allies.append(e)
        
        if not allies:
            return {"success": False, "message": "No allies nearby to call"}
        
        # Publish event
        if self.event_bus:
            self.event_bus.publish_event("ally_called", {
                "caller_id": entity.id,
                "ally_ids": [a.id for a in allies]
            })
        
        return {
            "success": True,
            "message": f"Called {len(allies)} allies for help",
            "ally_ids": [a.id for a in allies]
        }
    
    def _handle_follow_leader(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Follow leader."""
        # Find leader (entity with is_leader=True or social component)
        leader = None
        for e in all_entities:
            if e.id == entity.id:
                continue
            if hasattr(e, 'is_leader') and e.is_leader:
                leader = e
                break
            # Check social component
            social_comp = e.get_component("social") if hasattr(e, 'get_component') else None
            if social_comp and hasattr(social_comp, 'is_leader') and social_comp.is_leader:
                leader = e
                break
        
        if not leader:
            return {"success": False, "message": "No leader found to follow"}
        
        # Move to position adjacent to leader
        if hasattr(entity, 'position') and hasattr(leader, 'position'):
            # Move to position next to leader
            target_pos = Position(leader.position.x + 1, leader.position.y + 1)
            
            if self.movement_service.can_move_to(entity, target_pos):
                success = self.movement_service.move_entity(entity, target_pos)
                if success:
                    return {
                        "success": True,
                        "message": f"Following leader {leader.name}",
                        "leader_id": leader.id,
                        "target_position": {"x": target_pos.x, "y": target_pos.y}
                    }
                else:
                    return {"success": False, "message": "Could not move to follow leader"}
            
            return {"success": False, "message": "Cannot move to follow leader position"}
        
        return {"success": False, "message": "Cannot determine leader position"}
    
    def _handle_guard_position(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Guard a specific position."""
        # Get guard position from AI component or action parameters
        guard_pos = None
        ai_comp = entity.get_component("ai") if hasattr(entity, 'get_component') else None
        if ai_comp and hasattr(ai_comp, 'guard_position'):
            guard_pos = ai_comp.guard_position
        
        if not guard_pos and action.parameters and "position" in action.parameters:
            pos_data = action.parameters["position"]
            guard_pos = Position(pos_data.get("x", 0), pos_data.get("y", 0))
        
        if not guard_pos:
            return {"success": False, "message": "No guard position specified"}
        
        # Check if already at guard position
        if hasattr(entity, 'position') and entity.position.distance_to(guard_pos) < 1.0:
            return {"success": True, "message": f"Already at guard position {guard_pos.x},{guard_pos.y}", "holding": True}
        
        # Move to guard position
        if self.movement_service.can_move_to(entity, guard_pos):
            success = self.movement_service.move_entity(entity, guard_pos)
            if success:
                return {
                    "success": True,
                    "message": f"Guarding position {guard_pos.x},{guard_pos.y}",
                    "guard_position": {"x": guard_pos.x, "y": guard_pos.y}
                }
            else:
                return {"success": False, "message": "Could not move to guard position"}
        
        return {"success": False, "message": "Guard position is blocked or out of bounds"}
    
    def _handle_pickup_item(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Pick up an item."""
        # Find item (could be in inventory or in world)
        item_id = action.target
        if not item_id:
            # Try to find item at entity's position
            if hasattr(entity, 'position'):
                for e in all_entities:
                    if e.id != entity.id and hasattr(e, 'position') and e.position.distance_to(entity.position) < 1.0:
                        if hasattr(e, 'item') and e.item:
                            item_id = e.item.id
                            break
        
        if not item_id:
            return {"success": False, "message": "No item found to pick up"}
        
        # Find item entity
        item_entity = None
        for e in all_entities:
            if e.id == item_id and hasattr(e, 'item') and e.item:
                item_entity = e
                break
        
        if not item_entity:
            return {"success": False, "message": f"Item {item_id} not found"}
        
        # Add item to entity inventory
        if hasattr(entity, 'add_item_to_inventory'):
            entity.add_item_to_inventory(item_entity.item)
            
            # Remove item from world
            if hasattr(entity, 'remove_item_from_world'):
                entity.remove_item_from_world(item_id)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event("item_picked_up", {
                    "entity_id": entity.id,
                    "item_id": item_id
                })
            
            return {
                "success": True,
                "message": f"Picked up item {item_entity.item.name}",
                "item_id": item_id
            }
        
        return {"success": False, "message": "Entity cannot pick up items"}
    
    def _handle_gift_item(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Give item to another entity."""
        target_id = action.target
        if not target_id:
            return {"success": False, "message": "No target specified for gift"}
        
        # Find target entity
        target = None
        for e in all_entities:
            if e.id == target_id and hasattr(e, 'is_alive') and e.is_alive():
                target = e
                break
        
        if not target:
            return {"success": False, "message": f"Target {target_id} not found or not alive"}
        
        # Find item in entity's inventory
        item_id = action.target_item_id
        if not item_id and hasattr(entity, 'inventory'):
            # Use first item in inventory
            items = entity.inventory.get_items()
            if items:
                item_id = items[0]
        
        if not item_id:
            return {"success": False, "message": "No item to give"}
        
        # Remove item from giver's inventory
        if hasattr(entity, 'remove_item_from_inventory'):
            entity.remove_item_from_inventory(item_id)
        
        # Add item to target's inventory
        if hasattr(target, 'add_item_to_inventory'):
            target.add_item_to_inventory(item_id)
            
            # Modify loyalty via social service
            self.social_service.process_gift(entity.id, target_id, 10.0, self._tick)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event("item_gifted", {
                    "giver_id": entity.id,
                    "receiver_id": target_id,
                    "item_id": item_id
                })
            
            return {
                "success": True,
                "message": f"Gave item {item_id} to {target.name}",
                "giver_id": entity.id,
                "receiver_id": target_id,
                "item_id": item_id
            }
        
        return {"success": False, "message": "Target cannot receive items"}
    
    def _handle_give_orders(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Give orders to another entity."""
        target_id = action.target
        if not target_id:
            return {"success": False, "message": "No target specified for orders"}
        
        # Find target entity
        target = None
        for e in all_entities:
            if e.id == target_id and hasattr(e, 'is_alive') and e.is_alive():
                target = e
                break
        
        if not target:
            return {"success": False, "message": f"Target {target_id} not found or not alive"}
        
        # Check if entity can give orders (is leader or has authority)
        if not self._can_give_orders(entity):
            return {"success": False, "message": "You cannot give orders to others"}
        
        # Create order from action parameters
        order_command = action.parameters.get("command", "WAIT") if action.parameters else "WAIT"
        order_target = action.parameters.get("target_id") if action.parameters else None
        order_position = action.parameters.get("target_position") if action.parameters else None
        
        # Store order in target's AI component
        target_ai = target.get_component("ai") if hasattr(target, 'get_component') else None
        if target_ai and hasattr(target_ai, 'set_order'):
            target_ai.set_order(order_command, order_target, order_position)
        
        # Publish event
        if self.event_bus:
            self.event_bus.publish_event("orders_given", {
                "giver_id": entity.id,
                "receiver_id": target_id,
                "command": order_command,
                "target_id": order_target,
                "target_position": order_position
            })
        
        return {
            "success": True,
            "message": f"Issued order '{order_command}' to {target.name}",
            "giver_id": entity.id,
            "receiver_id": target_id,
            "command": order_command
        }
    
    def _handle_wait(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Do nothing (wait)."""
        return {"success": True, "message": "Waiting"}
    
    def _handle_search(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Search area."""
        # Get last known player position from perception memory
        perception_comp = entity.get_component("perception") if hasattr(entity, 'get_component') else None
        last_known_pos = None
        if perception_comp and hasattr(perception_comp, 'get_last_known_player_pos'):
            last_known_pos = perception_comp.get_last_known_player_pos()
        
        if last_known_pos:
            # Move towards last known position
            if hasattr(entity, 'position'):
                target_pos = Position(last_known_pos.x, last_known_pos.y)
                if self.movement_service.can_move_to(entity, target_pos):
                    success = self.movement_service.move_entity(entity, target_pos)
                    if success:
                        return {
                            "success": True,
                            "message": f"Searching towards last known player position {last_known_pos.x},{last_known_pos.y}",
                            "target_position": {"x": target_pos.x, "y": target_pos.y}
                        }
        
        # No last known position, wander randomly
        return self._handle_wander(entity, action, all_entities)
    
    def _handle_hide(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Hide (reduce visibility)."""
        # Set entity state to hiding
        if hasattr(entity, 'set_state'):
            entity.set_state("hiding")
        
        # Publish event
        if self.event_bus:
            self.event_bus.publish_event("entity_hidden", {
                "entity_id": entity.id,
                "hidden": True
            })
        
        return {"success": True, "message": "Hiding (reduced visibility)"}
    
    def _handle_use_item(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Use an item from inventory."""
        item_id = action.target_item_id
        if not item_id:
            return {"success": False, "message": "No item specified to use"}
        
        # Find item in inventory
        if hasattr(entity, 'inventory'):
            items = entity.inventory.get_items()
            if item_id not in items:
                return {"success": False, "message": f"Item {item_id} not in inventory"}
            
            # Use item (simplified - just remove it for now)
            entity.inventory.remove_item(item_id)
            
            # Apply item effect (simplified)
            if hasattr(entity, 'apply_item_effect'):
                entity.apply_item_effect(item_id)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event("item_used", {
                    "entity_id": entity.id,
                    "item_id": item_id
                })
            
            return {
                "success": True,
                "message": f"Used item {item_id}",
                "item_id": item_id
            }
        
        return {"success": False, "message": "Entity has no inventory"}
    
    def _handle_trade(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Trade with another entity."""
        target_id = action.target
        if not target_id:
            return {"success": False, "message": "No target specified for trade"}
        
        # Find target entity
        target = None
        for e in all_entities:
            if e.id == target_id and hasattr(e, 'is_alive') and e.is_alive():
                target = e
                break
        
        if not target:
            return {"success": False, "message": f"Target {target_id} not found or not alive"}
        
        # Simplified trade - exchange items
        if hasattr(entity, 'inventory') and hasattr(target, 'inventory'):
            # Exchange first item from each inventory
            entity_items = entity.inventory.get_items()
            target_items = target.inventory.get_items()
            
            if not entity_items or not target_items:
                return {"success": False, "message": "One or both entities have no items to trade"}
            
            # Remove items from inventories
            entity_item = entity_items[0]
            target_item = target_items[0]
            
            entity.inventory.remove_item(entity_item)
            target.inventory.remove_item(target_item)
            
            # Add items to other inventories
            entity.inventory.add_item(target_item)
            target.inventory.add_item(entity_item)
            
            # Modify loyalty via social service
            self.social_service.process_gift(entity.id, target_id, 5.0, self._tick)
            
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event("trade_completed", {
                    "trader1_id": entity.id,
                    "trader2_id": target_id,
                    "item1_id": entity_item,
                    "item2_id": target_item
                })
            
            return {
                "success": True,
                "message": f"Traded {entity_item} with {target_item}",
                "trader1_id": entity.id,
                "trader2_id": target_id,
                "item1_id": entity_item,
                "item2_id": target_item
            }
        
        return {"success": False, "message": "Entities cannot trade"}
    
    def _handle_promote_minion(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Promote a minion to a higher rank."""
        target_id = action.target
        if not target_id:
            return {"success": False, "message": "No target specified for promotion"}
        
        # Find target entity
        target = None
        for e in all_entities:
            if e.id == target_id and hasattr(e, 'is_alive') and e.is_alive():
                target = e
                break
        
        if not target:
            return {"success": False, "message": f"Target {target_id} not found or not alive"}
        
        # Check if entity is a leader
        if not self._is_leader(entity):
            return {"success": False, "message": "Only leaders can promote minions"}
        
        # Promote minion via social service
        result = self.social_service.process_promotion(entity.id, target_id, 1, self._tick)
        
        if result.get("success"):
            # Publish event
            if self.event_bus:
                self.event_bus.publish_event("minion_promoted", {
                    "leader_id": entity.id,
                    "minion_id": target_id,
                    "new_rank": 1
                })
            
            return {
                "success": True,
                "message": f"Promoted {target.name} to rank 1",
                "leader_id": entity.id,
                "minion_id": target_id,
                "new_rank": 1
            }
        
        return {"success": False, "message": "Could not promote minion"}
    
    def _handle_wander(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Wander randomly."""
        import random
        
        # Generate random position within movement range
        if hasattr(entity, 'position'):
            current_x = entity.position.x
            current_y = entity.position.y
            
            # Random offset
            dx = random.randint(-3, 3)
            dy = random.randint(-3, 3)
            
            if dx == 0 and dy == 0:
                return {"success": True, "message": "Staying in place (random wander)"}
            
            target_pos = Position(current_x + dx, current_y + dy)
            
            if self.movement_service.can_move_to(entity, target_pos):
                success = self.movement_service.move_entity(entity, target_pos)
                if success:
                    return {
                        "success": True,
                        "message": f"Wandering to {target_pos.x},{target_pos.y}",
                        "target_position": {"x": target_pos.x, "y": target_pos.y}
                    }
                else:
                    return {"success": False, "message": "Could not move to random position"}
            
            return {"success": False, "message": "Random position is blocked or out of bounds"}
        
        return {"success": False, "message": "Entity has no position"}
    
    def _handle_unknown(self, entity: Any, action: BehaviorAction, all_entities: List[Any]) -> Dict[str, Any]:
        """Handle unknown action type."""
        return {"success": False, "message": f"Unknown action type: {action.action_type}"}
    
    def _is_ally(self, entity1: Any, entity2: Any) -> bool:
        """Check if two entities are allies."""
        # Check social component
        social1 = entity1.get_component("social") if hasattr(entity1, 'get_component') else None
        social2 = entity2.get_component("social") if hasattr(entity2, 'get_component') else None
        
        if social1 and social2:
            # Check if they share the same social structure
            if (hasattr(social1, 'structure_id') and hasattr(social2, 'structure_id') and
                social1.structure_id == social2.structure_id):
                return True
            
            # Check if one is leader of the other
            if (hasattr(social1, 'is_leader') and social1.is_leader and
                hasattr(social2, 'structure_id') and social2.structure_id == getattr(social1, 'structure_id', None)):
                return True
            
            if (hasattr(social2, 'is_leader') and social2.is_leader and
                hasattr(social1, 'structure_id') and social1.structure_id == getattr(social2, 'structure_id', None)):
                return True
        
        # Default to neutral if no social components
        return False
    
    def _is_leader(self, entity: Any) -> bool:
        """Check if entity is a leader."""
        social_comp = entity.get_component("social") if hasattr(entity, 'get_component') else None
        if social_comp and hasattr(social_comp, 'is_leader'):
            return social_comp.is_leader
        return False
    
    def _can_give_orders(self, entity: Any) -> bool:
        """Check if entity can give orders to others."""
        # Check if entity is a leader
        if self._is_leader(entity):
            return True
        
        # Check social component for authority
        social_comp = entity.get_component("social") if hasattr(entity, 'get_component') else None
        if social_comp and hasattr(social_comp, 'can_give_orders'):
            return social_comp.can_give_orders()
        
        return False
    
    @property
    def _tick(self) -> int:
        """Get current tick (simplified - would come from orchestrator)."""
        return 0  # This would be set by the orchestrator