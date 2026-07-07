Task ID: T-2026-07-07-001
Objective: Implement event system integration for dynamic difficulty system

Issues Identified:
1. SystemHandler._register_handlers() is a stub - needs actual event bus registration for level change events
2. ApplicationDynamicDifficultyService._register_event_handlers() is a stub - needs implementation for event handling
3. Level change event publishing from Game.generate_level() not yet implemented - the system lacks the trigger to publish level change events
4. The difficulty_adjusted event is published but no consumers are registered yet - while not critical for core functionality, limits extensibility

Plan to Address Concerns:
1. Implement SystemHandler._register_handlers():
   - Register handle_level_change method to listen for level change events (e.g., 'level_changed' or similar)
   - Use the existing event bus pattern from other handlers in the codebase
2. Implement ApplicationDynamicDifficultyService._register_event_handlers():
   - Register for relevant events (potentially difficulty_adjusted for logging/UI, or other game events)
   - Follow the pattern used in other application services
3. Implement Level Change Event Publishing:
   - Identify where level changes occur (likely in Game.generate_level() or floor1_generator.py)
   - Publish a level change event via the event bus when a new level is successfully generated
   - Ensure the event includes necessary context (current level, player entity, etc.)
4. Address difficulty_adjusted Event Consumers:
   - Determine if any systems need to react to difficulty adjustments (e.g., UI display, logging, achievement tracking)
   - Implement consumers as needed, or document that the event is available for future use
   - At minimum, ensure the event is properly typed and documented

These are integration enhancements that do not affect the core dynamic difficulty adjustment functionality, which has been verified working through unit tests and manual playtesting. The core system correctly:
- Evaluates player stats via DM LLM at level changes
- Applies difficulty adjustments to monster generation
- Integrates with existing floor generation and spawning systems

The identified issues can be addressed in this task focused on completing the event system integration, ensuring the dynamic difficulty system is fully wired into the game's event-driven architecture.
