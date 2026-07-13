import pytest
from src.domain.value_objects.position import Position

def test_position_is_immutable():
    """Test that Position instances are immutable"""
    pos = Position(1, 2)
    # Attempt to modify attributes should raise FrozenInstanceError
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        pos.x = 5
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        pos.y = 10

def test_position_move_returns_new_instance():
    """Test that move method returns a new Position instance"""
    pos1 = Position(1, 2)
    pos2 = pos1.move(2, 3)
    
    # Original position should be unchanged
    assert pos1.x == 1
    assert pos1.y == 2
    
    # New position should have the moved values
    assert pos2.x == 3
    assert pos2.y == 5
    
    # They should be different objects
    assert pos1 is not pos2
    assert pos1 == Position(1, 2)  # Original unchanged
    assert pos2 == Position(3, 5)  # New position correct

def test_position_translate_removed():
    """Test that the translate method has been removed"""
    pos = Position(1, 2)
    # This should raise an AttributeError since we removed the method
    with pytest.raises(AttributeError):
        pos.translate(1, 1)

def test_position_other_methods_unchanged():
    """Test that other methods still work correctly"""
    pos1 = Position(1, 2)
    pos2 = Position(4, 6)
    
    # Test distance_to
    assert pos1.distance_to(pos2) == 5.0  # 3-4-5 triangle
    
    # Test manhattan_distance_to
    assert pos1.manhattan_distance_to(pos2) == 7  # |3| + |4|
    
    # Test is_adjacent_to
    assert pos1.is_adjacent_to(Position(2, 2)) is True   # horizontal neighbor
    assert pos1.is_adjacent_to(Position(1, 3)) is True   # vertical neighbor
    assert pos1.is_adjacent_to(Position(0, 2)) is True   # horizontal neighbor
    assert pos1.is_adjacent_to(Position(1, 1)) is True   # vertical neighbor
    
    # Test is_within_distance
    assert pos1.is_within_distance(pos2, 5) is True    # distance 5 <= 5
    assert pos1.is_within_distance(pos2, 6) is True    # distance 5 <= 6
    assert pos1.is_within_distance(pos2, 7) is True    # distance 5 <= 7
    
    # Test get_direction_to
    assert pos1.get_direction_to(Position(3, 2)) == (1, 0)   # right
    assert pos1.get_direction_to(Position(1, 4)) == (0, 1)   # up
    assert pos1.get_direction_to(Position(0, 2)) == (-1, 0)  # left
    assert pos1.get_direction_to(Position(1, 0)) == (0, -1)  # down
    assert pos1.get_direction_to(Position(3, 4)) == (1, 1)   # diagonal
    
    # Test equality and hash
    assert pos1 == Position(1, 2)
    assert pos1 != Position(2, 2)
    # Positions can be used in sets
    pos_set = {pos1, Position(1, 2), Position(2, 2)}
    assert len(pos_set) == 2  # duplicates removed
    
    # Test string representation
    assert str(pos1) == "(1, 2)"
    assert repr(pos1) == "Position(x=1, y=2)"
    
    # Test serialization
    pos_dict = pos1.to_dict()
    assert pos_dict == {"x": 1, "y": 2}
    pos_from_dict = Position.from_dict(pos_dict)
    assert pos_from_dict == pos1
    
    pos_from_tuple = Position.from_tuple((5, 6))
    assert pos_from_tuple == Position(5, 6)

def test_position_validation():
    """Test that Position validates input types"""
    # Valid integers should work
    pos = Position(1, 2)
    assert pos.x == 1
    assert pos.y == 2
    
    # Non-integer x should raise TypeError
    with pytest.raises(TypeError, match="Position x must be an integer"):
        Position(1.5, 2)
    
    # Non-integer y should raise TypeError
    with pytest.raises(TypeError, match="Position y must be an integer"):
        Position(1, 2.5)