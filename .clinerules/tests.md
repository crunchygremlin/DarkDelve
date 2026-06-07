Since you are using pytest now, you can stick entirely to the simpler, cleaner syntax you prefer. For any new tests you write, you can go right back to using plain functions and standard assert statements:pythondef test_new_feature():
    # No classes needed, no self.assertEqual needed!
    result = calculate_something()
    assert result == expected_values