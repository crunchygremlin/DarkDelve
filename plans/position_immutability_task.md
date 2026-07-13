Task ID: POS-001
Task: Fix Position immutability violation
Objective: Make the Position value object immutable by adding @dataclass(frozen=True) and modifying the translate method to return a new instance instead of mutating self.

Steps:
1. Review the current Position class in src/domain/value_objects/position.py
2. Plan the fix: add frozen=True to @dataclass and change translate to return new Position
3. Implement the fix
4. Run tests to ensure nothing breaks (especially tests that use Position.translate)
5. Update any code that relies on the mutability of Position (if any)

Deliverables:
- Modified src/domain/value_objects/position.py
- Updated any affected code
- Test results showing no regressions
