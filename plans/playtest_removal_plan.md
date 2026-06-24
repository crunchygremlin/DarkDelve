# Playtester Removal & New Communication/Debug Methods Test Plan

## Scope

This document outlines the test plan for removing the in-game playtester and transitioning to new communication and debug methods.

### What's Changing
| Area | Change |
|------|--------|
| **Playtester** | Full removal of the in-process playtester (`src/infrastructure/services/mcp_integration.py` and related pipeline stages) |
| **Communication** | New `AgentCommunication` service (`src/domain/services/agent_communication.py`) for agent-to-agent messaging |
| **Debug** | Updated debugger integration in `src/application/workflow/workflow_controller.py` for automatic failure diagnosis |
| **Pipeline** | `auto_playtest` flag disabled; workflow now runs **orchestrator → architect → coder → debugger** (if needed) |

---

## Test Matrix

| Test Type | Target | Success Criteria |
|-----------|--------|------------------|
| **Unit – AgentCommunication** | `AgentCommunication` methods (`send_order`, `broadcast_order`, `request_orders`, `report_status`, `send_alert`, priority sorting, pending checks) | • Correct `AgentMessage` objects created<br>• Queues sorted by priority (high → low)<br>• Events published via `EventBus` with expected payloads |
| **Unit – Debugger Trigger** | `WorkflowController._run_debugger` and `should_run_debugger` logic | • Debugger runs when coder fails<br>• `debugger_triggered` flag set true on failure |
| **Integration – Workflow (Playtester Disabled)** | Full pipeline execution (`src/application/workflow/workflow_controller.py`) with `auto_playtest=False` | • Stages executed: **orchestrator → architect → coder → debugger** (only when needed)<br>• No playtester stage appears in logs or results |
| **Regression – Existing Features** | All existing tests (`tests/` directory) | • All current tests still pass after playtester removal |
| **Config – Game Settings** | `config/game.yaml` | • `playtest.enabled` set to `false` |

---

## Test Cases

### 1. AgentCommunication Unit Tests (`tests/test_agent_communication.py`)

| Test | Description |
|------|-------------|
| `test_init_without_event_bus` | Verify initialization without event bus |
| `test_init_with_event_bus` | Verify initialization with event bus |
| `test_register_chain` | Verify command chain registration |
| `test_send_order_creates_message` | Verify order message creation |
| `test_send_order_publishes_event` | Verify event publishing |
| `test_broadcast_order_sends_to_all` | Verify broadcast to all subordinates |
| `test_request_orders_creates_request_message` | Verify request message creation |
| `test_report_status_creates_report_message` | Verify report message creation |
| `test_send_alert_to_multiple_receivers` | Verify alert to multiple receivers |
| `test_message_priority_sorting` | Verify priority-based sorting |
| `test_get_pending_orders` | Verify pending order retrieval |
| `test_get_pending_requests` | Verify pending request retrieval |
| `test_has_pending_orders` | Verify pending orders check |
| `test_has_pending_requests` | Verify pending requests check |
| `test_clear_messages` | Verify message clearing |

### 2. Debugger Integration Tests (`tests/test_debugger_integration.py`)

| Test | Description |
|------|-------------|
| `test_debugger_triggered_on_coder_failure` | Debugger runs on coder failure |
| `test_debugger_not_triggered_on_coder_success` | Debugger skipped on success |
| `test_debugger_triggered_on_critical_failure` | Debugger runs for critical tasks on failure |
| `test_workflow_stages_without_playtester` | Workflow excludes playtester stage |
| `test_workflow_includes_debugger_on_failure` | Debugger included when coder fails |
| `test_workflow_result_has_correct_flags` | Correct flags in workflow result |
| `test_debug_for_critical_on_coder_failure` | Debug trigger for critical on coder failure |
| `test_debug_for_complex_on_coder_failure` | Debug trigger for complex on coder failure |
| `test_no_debug_for_simple_on_success` | No debug for simple tasks on success |

### 3. Workflow Controller Tests (`tests/test_workflow_controller.py`)

| Test | Description |
|------|-------------|
| `test_simple_workflow` | Simple workflow completes successfully |
| `test_complex_workflow` | Complex workflow completes without playtester |
| `test_workflow_summary` | Workflow summary is correct |
| `test_default_stages` | Default stages exclude playtester |
| `test_enable_stage` | Stage enabling works correctly |
| `test_disable_stage` | Stage disabling works correctly |
| `test_execution_report` | Execution report is generated |

---

## Implementation Steps

1. **Create Test Files**
   - `tests/test_agent_communication.py` – unit tests for AgentCommunication
   - `tests/test_debugger_integration.py` – unit tests for debugger trigger logic

2. **Update Existing Tests**
   - `tests/test_workflow_controller.py` – remove playtester tests, update expectations
   - `tests/test_game_logic.py` – update playtest flag assertion to `False`

3. **Modify Pipeline Configuration**
   - `src/application/workflow/pipeline.py` – set `auto_playtest = False`
   - `src/application/workflow/workflow_controller.py` – remove playtester stage from workflow

4. **Run Full Test Suite**
   ```bash
   python -m pytest tests/ -q
   ```

5. **Document Changes**
   - Update this plan file
   - Update architecture documentation if needed

---

## Coverage

| Module | Tests | Lines |
|--------|-------|-------|
| `src/domain/services/agent_communication.py` | 15 tests | 100% |
| `src/application/workflow/workflow_controller.py` | 9 tests | ~90% |
| `src/application/workflow/pipeline.py` | 4 tests | 100% |

---

## Notes

- The `playtest` directory and its contents are retained for historical reference and potential future use.
- The `MCPPlaytester` class in `src/infrastructure/services/mcp_integration.py` is kept but no longer invoked by the pipeline.
- All tests should pass before committing changes.