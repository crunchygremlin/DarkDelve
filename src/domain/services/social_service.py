"""Social service for managing social structures, loyalty, and wealth distribution."""

from typing import Dict, List, Optional, Tuple, Any
import time
import uuid

from src.domain.value_objects.social import (
    SocialStructure, SocialRelationship, LoyaltyState,
    SocialStructureType, RelationshipType
)


__all__ = ["SocialService"]


class SocialService:
    """
    Service for managing social structures, loyalty, and wealth distribution.
    
    This service maintains in-memory state of all social structures and loyalty,
    and provides methods for modifying relationships and processing social events.
    """
    
    def __init__(self):
        """Initialize the SocialService with empty state."""
        self._structures: Dict[str, SocialStructure] = {}
        self._loyalty_states: Dict[str, LoyaltyState] = {}
        self._relationships: Dict[str, List[SocialRelationship]] = {}
    
    def create_structure(
        self,
        structure_type: str,
        leader_id: str,
        member_ids: List[str]
    ) -> SocialStructure:
        """
        Create a new social structure.
        
        Args:
            structure_type: Type of the social structure
            leader_id: ID of the leader entity
            member_ids: List of member entity IDs
            
        Returns:
            SocialStructure: The created structure
        """
        structure_id = f"{structure_type}_{uuid.uuid4().hex[:8]}"
        
        structure = SocialStructure(
            structure_id=structure_id,
            structure_type=structure_type,
            leader_id=leader_id,
            member_ids=member_ids,
            hierarchy={leader_id: 0},
            shared_goals=[],
            wealth_pool=0.0,
            relationships=[]
        )
        
        # Set hierarchy for members
        for i, member_id in enumerate(member_ids):
            structure.hierarchy[member_id] = i + 1
        
        self._structures[structure_id] = structure
        
        # Initialize loyalty for members
        for member_id in member_ids:
            self._loyalty_states[member_id] = LoyaltyState(
                minion_id=member_id,
                leader_id=leader_id,
                loyalty_score=0.5,
                base_loyalty=0.5
            )
        
        return structure
    
    def add_member(self, structure_id: str, entity_id: str, rank: int = 99) -> bool:
        """
        Add a member to a social structure.
        
        Args:
            structure_id: ID of the structure
            entity_id: ID of the entity to add
            rank: Rank in the hierarchy (0 = leader, higher = lower)
            
        Returns:
            bool: True if member was added
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return False
        
        if entity_id in structure.member_ids:
            return False
        
        structure.member_ids.append(entity_id)
        structure.hierarchy[entity_id] = rank
        
        # Initialize loyalty
        self._loyalty_states[entity_id] = LoyaltyState(
            minion_id=entity_id,
            leader_id=structure.leader_id,
            loyalty_score=0.5,
            base_loyalty=0.5
        )
        
        return True
    
    def remove_member(self, structure_id: str, entity_id: str) -> bool:
        """
        Remove a member from a social structure.
        
        Args:
            structure_id: ID of the structure
            entity_id: ID of the entity to remove
            
        Returns:
            bool: True if member was removed
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return False
        
        if entity_id not in structure.member_ids:
            return False
        
        structure.member_ids.remove(entity_id)
        structure.hierarchy.pop(entity_id, None)
        
        # Remove loyalty state
        self._loyalty_states.pop(entity_id, None)
        
        return True
    
    def get_structure(self, structure_id: str) -> Optional[SocialStructure]:
        """
        Get a social structure by ID.
        
        Args:
            structure_id: ID of the structure
            
        Returns:
            Optional[SocialStructure]: The structure or None
        """
        return self._structures.get(structure_id)
    
    def get_structure_for_entity(self, entity_id: str) -> Optional[SocialStructure]:
        """
        Get the social structure that an entity belongs to.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            Optional[SocialStructure]: The structure or None
        """
        for structure in self._structures.values():
            if entity_id in structure.member_ids or entity_id == structure.leader_id:
                return structure
        return None
    
    def get_leader(self, structure_id: str) -> Optional[str]:
        """
        Get the leader ID of a social structure.
        
        Args:
            structure_id: ID of the structure
            
        Returns:
            Optional[str]: Leader ID or None
        """
        structure = self._structures.get(structure_id)
        return structure.leader_id if structure else None
    
    def get_members(self, structure_id: str) -> List[str]:
        """
        Get all member IDs of a social structure.
        
        Args:
            structure_id: ID of the structure
            
        Returns:
            List[str]: List of member IDs
        """
        structure = self._structures.get(structure_id)
        return structure.member_ids if structure else []
    
    def get_rank(self, structure_id: str, entity_id: str) -> int:
        """
        Get the rank of an entity in a social structure.
        
        Args:
            structure_id: ID of the structure
            entity_id: ID of the entity
            
        Returns:
            int: Rank (0 = leader, higher = lower)
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return 99
        return structure.hierarchy.get(entity_id, 99)
    
    def seed_loyalty(self, structure_id: str, base_loyalty: float = 0.5) -> None:
        """
        Set initial loyalty for all minions in a structure.
        
        Args:
            structure_id: ID of the structure
            base_loyalty: Base loyalty value (0.0 to 1.0)
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return
        
        for member_id in structure.member_ids:
            if member_id in self._loyalty_states:
                self._loyalty_states[member_id].base_loyalty = base_loyalty
                self._loyalty_states[member_id].loyalty_score = base_loyalty
    
    def get_loyalty(self, minion_id: str) -> Optional[LoyaltyState]:
        """
        Get the loyalty state for a minion.
        
        Args:
            minion_id: ID of the minion
            
        Returns:
            Optional[LoyaltyState]: The loyalty state or None
        """
        return self._loyalty_states.get(minion_id)
    
    def modify_loyalty(
        self,
        minion_id: str,
        amount: float,
        source: str,
        reason: str,
        tick: int
    ) -> bool:
        """
        Modify loyalty for a minion.
        
        Args:
            minion_id: ID of the minion
            amount: Amount to modify loyalty (can be negative)
            source: Source of the modification
            reason: Reason for the modification
            tick: Current game tick
            
        Returns:
            bool: True if loyalty was modified
        """
        loyalty = self._loyalty_states.get(minion_id)
        if not loyalty:
            return False
        
        loyalty.apply_modifier(source, amount, reason, tick)
        return True
    
    def process_gift(
        self,
        giver_id: str,
        receiver_id: str,
        item_value: float,
        tick: int
    ) -> Dict[str, Any]:
        """
        Process a gift from one entity to another.
        
        Args:
            giver_id: ID of the giver
            receiver_id: ID of the receiver
            item_value: Value of the gift
            tick: Current game tick
            
        Returns:
            Dict[str, Any]: Result with loyalty_change and success
        """
        loyalty = self._loyalty_states.get(receiver_id)
        if not loyalty:
            return {"loyalty_change": 0.0, "success": False}
        
        # Gift value affects loyalty (scaled down)
        loyalty_change = min(0.2, item_value * 0.01)
        
        self.modify_loyalty(
            receiver_id,
            loyalty_change,
            "gift",
            f"Received gift from {giver_id}",
            tick
        )
        
        return {
            "loyalty_change": loyalty_change,
            "success": True
        }
    
    def process_combat_alongside(
        self,
        ally_id: str,
        tick: int
    ) -> None:
        """
        Process loyalty boost for fighting alongside ally's leader.
        
        Args:
            ally_id: ID of the ally
            tick: Current game tick
        """
        loyalty = self._loyalty_states.get(ally_id)
        if not loyalty:
            return
        
        # Small loyalty boost for fighting together
        self.modify_loyalty(
            ally_id,
            0.01,
            "combat",
            "Fought alongside leader",
            tick
        )
    
    def process_leader_fled(
        self,
        leader_id: str,
        tick: int
    ) -> None:
        """
        Process loyalty penalty for all minions when leader flees.
        
        Args:
            leader_id: ID of the leader who fled
            tick: Current game tick
        """
        # Find all structures where this leader is in charge
        for structure in self._structures.values():
            if structure.leader_id == leader_id:
                for member_id in structure.member_ids:
                    self.modify_loyalty(
                        member_id,
                        -0.1,
                        "leader_fled",
                        "Leader abandoned the group",
                        tick
                    )
    
    def process_promotion(
        self,
        structure_id: str,
        entity_id: str,
        new_rank: int,
        tick: int
    ) -> Dict[str, Any]:
        """
        Process a promotion for a minion.
        
        Args:
            structure_id: ID of the structure
            entity_id: ID of the promoted entity
            new_rank: New rank in hierarchy
            tick: Current game tick
            
        Returns:
            Dict[str, Any]: Result with loyalty_change and success
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return {"loyalty_change": 0.0, "success": False}
        
        old_rank = structure.hierarchy.get(entity_id, 99)
        structure.hierarchy[entity_id] = new_rank
        
        # Large loyalty boost for promotion
        loyalty_change = 0.15
        self.modify_loyalty(
            entity_id,
            loyalty_change,
            "promotion",
            f"Promoted from rank {old_rank} to {new_rank}",
            tick
        )
        
        return {
            "loyalty_change": loyalty_change,
            "success": True
        }
    
    def distribute_wealth(
        self,
        structure_id: str,
        total_wealth: float,
        distribution: Dict[str, float],
        tick: int
    ) -> Dict[str, Any]:
        """
        Distribute wealth to minions and return loyalty changes.
        
        Args:
            structure_id: ID of the structure
            total_wealth: Total wealth to distribute
            distribution: Dict mapping entity_id to wealth share
            tick: Current game tick
            
        Returns:
            Dict[str, Any]: Result with loyalty_changes and success
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return {"loyalty_changes": {}, "success": False}
        
        structure.wealth_pool += total_wealth
        
        loyalty_changes = {}
        for entity_id, share in distribution.items():
            if entity_id in self._loyalty_states:
                # Wealth distribution affects loyalty
                loyalty_change = min(0.1, share * 0.001)
                self.modify_loyalty(
                    entity_id,
                    loyalty_change,
                    "wealth",
                    f"Received wealth share of {share}",
                    tick
                )
                loyalty_changes[entity_id] = loyalty_change
        
        return {
            "loyalty_changes": loyalty_changes,
            "success": True
        }
    
    def check_desertion(self, minion_id: str) -> bool:
        """
        Check if a minion should desert.
        
        Args:
            minion_id: ID of the minion
            
        Returns:
            bool: True if minion should desert
        """
        loyalty = self._loyalty_states.get(minion_id)
        return loyalty.will_desert() if loyalty else False
    
    def check_betrayal(self, minion_id: str) -> bool:
        """
        Check if a minion should betray their leader.
        
        Args:
            minion_id: ID of the minion
            
        Returns:
            bool: True if minion should betray
        """
        loyalty = self._loyalty_states.get(minion_id)
        return loyalty.will_betray() if loyalty else False
    
    def get_structure_summary(self, structure_id: str) -> Dict[str, Any]:
        """
        Get a summary of a social structure for LLM consumption.
        
        Args:
            structure_id: ID of the structure
            
        Returns:
            Dict[str, Any]: Summary of the structure
        """
        structure = self._structures.get(structure_id)
        if not structure:
            return {}
        
        # Get loyalty stats
        loyalty_scores = []
        for member_id in structure.member_ids:
            loyalty = self._loyalty_states.get(member_id)
            if loyalty:
                loyalty_scores.append(loyalty.loyalty_score)
        
        avg_loyalty = sum(loyalty_scores) / len(loyalty_scores) if loyalty_scores else 0.5
        
        return {
            "structure_id": structure_id,
            "structure_type": structure.structure_type,
            "leader_id": structure.leader_id,
            "member_count": len(structure.member_ids),
            "average_loyalty": avg_loyalty,
            "wealth_pool": structure.wealth_pool,
            "hierarchy": structure.hierarchy
        }
    
    def get_social_context_for_llm(self, entity_id: str) -> str:
        """
        Get text summary of social context for LLM prompt.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            str: Text summary for LLM
        """
        structure = self.get_structure_for_entity(entity_id)
        if not structure:
            return "No social structure."
        
        leader_id = structure.leader_id
        is_leader = entity_id == leader_id
        rank = self.get_rank(structure.structure_id, entity_id)
        
        loyalty = self._loyalty_states.get(entity_id)
        loyalty_str = f"{loyalty.loyalty_score:.2f}" if loyalty else "unknown"
        
        lines = [
            f"Social Context:",
            f"  Structure: {structure.structure_type}",
            f"  Leader: {leader_id}",
            f"  Your Status: {'Leader' if is_leader else f'Member (rank {rank})'}",
            f"  Loyalty: {loyalty_str}",
            f"  Members: {len(structure.member_ids)}"
        ]
        
        return "\n".join(lines)