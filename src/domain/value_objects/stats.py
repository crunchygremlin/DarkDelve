from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Stats:
    """Character stats value object"""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    def __post_init__(self) -> None:
        """Validate stat values"""
        for stat_name, value in self.__dict__.items():
            if not isinstance(value, int):
                raise TypeError(f"Stat {stat_name} must be an integer")
            if value < 0:
                raise ValueError(f"Stat {stat_name} cannot be negative")
                
    def get_modifier(self, stat_name: str) -> int:
        """Get ability modifier for a stat"""
        stat_value = getattr(self, stat_name, 0)
        return (stat_value - 10) // 2
        
    def get_strength_modifier(self) -> int:
        """Get strength modifier"""
        return self.get_modifier("strength")
        
    def get_dexterity_modifier(self) -> int:
        """Get dexterity modifier"""
        return self.get_modifier("dexterity")
        
    def get_constitution_modifier(self) -> int:
        """Get constitution modifier"""
        return self.get_modifier("constitution")
        
    def get_intelligence_modifier(self) -> int:
        """Get intelligence modifier"""
        return self.get_modifier("intelligence")
        
    def get_wisdom_modifier(self) -> int:
        """Get wisdom modifier"""
        return self.get_modifier("wisdom")
        
    def get_charisma_modifier(self) -> int:
        """Get charisma modifier"""
        return self.get_modifier("charisma")
        
    def get_max_health(self) -> int:
        """Calculate max health based on constitution"""
        base_health = 10
        return base_health + self.get_constitution_modifier() * 2
        
    def get_max_mana(self) -> int:
        """Calculate max mana based on intelligence"""
        base_mana = 10
        return base_mana + self.get_intelligence_modifier() * 2
        
    def get_armor_class(self) -> int:
        """Calculate armor class based on dexterity"""
        base_ac = 10
        return base_ac + self.get_dexterity_modifier()
        
    def get_attack_bonus(self) -> int:
        """Calculate attack bonus based on strength"""
        return self.get_strength_modifier()
        
    def get_damage_bonus(self) -> int:
        """Calculate damage bonus based on strength"""
        return self.get_strength_modifier()
        
    def increase_stat(self, stat_name: str, amount: int = 1) -> None:
        """Increase a stat by amount"""
        if stat_name in self.__dict__:
            current_value = getattr(self, stat_name)
            new_value = current_value + amount
            setattr(self, stat_name, new_value)
            
    def decrease_stat(self, stat_name: str, amount: int = 1) -> None:
        """Decrease a stat by amount"""
        if stat_name in self.__dict__:
            current_value = getattr(self, stat_name)
            new_value = max(0, current_value - amount)
            setattr(self, stat_name, new_value)
            
    def set_stat(self, stat_name: str, value: int) -> None:
        """Set a stat to a specific value"""
        if stat_name in self.__dict__:
            setattr(self, stat_name, max(0, value))
            
    def get_total_stats(self) -> int:
        """Get sum of all stats"""
        return sum(self.__dict__.values())
        
    def get_average_stat(self) -> float:
        """Get average of all stats"""
        return self.get_total_stats() / len(self.__dict__)
        
    def copy(self) -> 'Stats':
        """Create a copy of this stats object"""
        return Stats(
            strength=self.strength,
            dexterity=self.dexterity,
            constitution=self.constitution,
            intelligence=self.intelligence,
            wisdom=self.wisdom,
            charisma=self.charisma
        )
        
    def __eq__(self, other: object) -> bool:
        """Check if stats are equal"""
        if not isinstance(other, Stats):
            return False
        return self.__dict__ == other.__dict__
        
    def __hash__(self) -> int:
        """Hash stats for use in sets/dictionaries"""
        return hash(tuple(self.__dict__.items()))
        
    def __str__(self) -> str:
        """String representation"""
        return (f"Str:{self.strength} Dex:{self.dexterity} Con:{self.constitution} "
                f"Int:{self.intelligence} Wis:{self.wisdom} Cha:{self.charisma}")
        
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Stats(strength={self.strength}, dexterity={self.dexterity}, "
                f"constitution={self.constitution}, intelligence={self.intelligence}, "
                f"wisdom={self.wisdom}, charisma={self.charisma})")
        
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for serialization"""
        return {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Stats':
        """Create stats from dictionary"""
        return cls(
            strength=data.get("strength", 10),
            dexterity=data.get("dexterity", 10),
            constitution=data.get("constitution", 10),
            intelligence=data.get("intelligence", 10),
            wisdom=data.get("wisdom", 10),
            charisma=data.get("charisma", 10)
        )