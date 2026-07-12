# DarkDelve DM Improvement — Implementation Design (SYSTEM)

> Produced by Architect for the Coder. Design ONLY. No source edits here.
> Maps 1:1 to [`plans/dm_improvements_plan.md`](plans/dm_improvements_plan.md:13) and
> [`plans/task_description.md`](plans/task_description.md:14).

## 0. Context Map (tight, ~256-window)

```
src/domain/agents/dungeon_master_agent.py   # DM brain: behavior/level/content/evolution; hardcoded "gpt-oss"
src/application/services/llm_worker.py       # bg thread; has DEAD evaluate_player_stats(); max_calls=5
src/domain/services/llm_map_generator.py     # map_generation LLM call (NOT handled by worker yet)
src/domain/services/behavior_script_service.py  # eval trees; create_default_script() = safe fallback
src/domain/services/plan_generator.py        # MOB_BEHAVIOR_CATALOG validation; _get_fallback_plan()
src/domain/value_objects/llm_logging.py      # LLMLogger/check_headroom/ContextWindowDiagnostics
src/domain/components/behavior_component.py  # current_script persists => LLM NOT called every tick
src/domain/services/entity_ai_orchestrator.py # scripts reused until None; event_bus.publish(str, dict)
config/game.yaml                             # dungeon_master.model = "gpt-oss" (must become qwen2.5-coder:7b-instruct)
src/infrastructure/services/mcp_toolkit.py   # create_mob/add_item/modify_stat/request_map_section/list_entities
ollama_playtester.py / player_agent.py       # playtester drives game via Ollama (must become MCP)
architecture/agent_system.md, system_overview.md, gotchas.md
```

Key facts the Coder must honor:
- `DungeonMasterAgent.__init__` is built at [`darkdelve.py`](darkdelve.py:2360) with `(ollama_service, level_design, self.llm_logger)`.
- `LLMWorker.evaluate_player_stats` is DEAD code (only referenced by `Mock(spec=LLMWorker)` in tests, never called in game flow). Safe to move.
- `DynamicDifficultyService` is deterministic (no LLM). Keep it unchanged; DM agent just *hosts* the LLM difficulty logic.
- `entity_ai_orchestrator` uses `event_bus.publish("topic", {dict})` (string-topic bus), NOT `Event` objects. Leader commands reuse this shape.
- `behavior_component.current_script` proves LLM is only called when script is `None` (see [`entity_ai_orchestrator.py`](src/domain/services/entity_ai_orchestrator.py:66)).
- `MOB_BEHAVIOR_CATALOG` lives in [`behavior_script.py`](src/domain/value_objects/behavior_script.py:135).

## 1. Goal

Evolve the local-LLM Dungeon Master into one cohesive, context-aware, throttled "single mind": a unified
`DungeonMasterAgent` owning behavior/level/map/content/difficulty/memory, a global throttled poetic memory,
swarm behavior templates with leader commands, one model config, prompt truncation with logging, a
behavior library with fallback, a cache-miss tracker (pre-cache), and an MCP-driven playtester.

## 2. Files to Create

- `src/domain/value_objects/dm_memory.py` — `DMGlobalMemory` value object (global poetic memory, headroom-bounded).
- `src/domain/services/behavior_library.py` — `BehaviorLibrary` (select/author/fallback, persisted).
- `src/domain/services/swarm_template_service.py` — `SwarmTemplateService` (templates by intelligence tier + leader bark).
- `src/domain/services/cache_miss_tracker.py` — `CacheMissTracker` (>=75% similarity, telemetry only, no caching yet).
- `src/domain/value_objects/truncation_info.py` — `TruncationInfo` dataclass for truncation logging.
- `tests/test_dm_memory.py` — memory throttle tests.
- `tests/test_truncation_logging.py` — truncation logging tests.
- `tests/test_cache_miss_tracker.py` — cache-miss tracker tests.
- `tests/test_behavior_library.py` — library fallback tests.
- `tests/test_swarm_template.py` — swarm template + leader command tests.
- `tests/test_mcp_playtester.py` — MCP playtester tests (fake `PlayerAgent`/game).

## 3. Files to Modify

- [`src/domain/agents/dungeon_master_agent.py`](src/domain/agents/dungeon_master_agent.py:29) — constructor + new methods (memory, library, swarm, map, difficulty eval, truncation, cache-miss).
- [`src/application/services/llm_worker.py`](src/application/services/llm_worker.py:13) — remove `LLMWorker.evaluate_player_stats*`; add `map_generation` branch; add cache-miss hook.
- [`src/domain/value_objects/llm_logging.py`](src/domain/value_objects/llm_logging.py:73) — add `TruncationInfo` logging, truncation helper, cache-miss metric, new `LLMCallLog` fields.
- [`config/game.yaml`](config/game.yaml:171) — `dungeon_master.model` -> `qwen2.5-coder:7b-instruct`; add `max_prompt_chars`, `dm_model`, `dm_temperature`.
- [`darkdelve.py`](darkdelve.py:2357) — pass model/temperature/max_prompt_chars + memory/library/swarm/tracker to `DungeonMasterAgent`; refresh memory at level boundary.
- [`src/domain/services/entity_ai_orchestrator.py`](src/domain/services/entity_ai_orchestrator.py:33) — inject `swarm_template_service`; select group template; route leader commands via event_bus.
- [`ollama_playtester.py`](ollama_playtester.py:202) — add `MCPPlaytester` in-process driver (no Ollama).
- [`player_agent.py`](player_agent.py:165) — add `MCPPlayerAgent` (decides via `MCPToolkit`, no LLM).
- `architecture/agent_system.md`, `architecture/system_overview.md`, `architecture/gotchas.md` — doc updates (see §9).

## 4. Per-Item Design

### Item 1 — One DM Mind (unified agent)

**Purpose:** `DungeonMasterAgent` owns behavior, level design, map generation, content, difficulty, memory.

**New methods on `DungeonMasterAgent`:**
- `evaluate_player_stats(player_stats: Dict[str, int], current_level: int) -> Dict[str, Any]` — MOVED from `LLMWorker` (logic identical: build prompt, call `self.ollama.generate`, parse JSON, default to 1.0 modifiers on failure). Uses `self._model_name`/`self._temperature`.
- `generate_map(description: str, width: int = 60, height: int = 40, depth: int = 1) -> Optional["MapBuilder"]` — delegates to injected `LLMMapGenerator` (owns the `map_generation` call type). On failure returns `None` (caller falls back to procedural).
- `set_swarm_template_service(svc)`, `set_behavior_library(lib)`, `set_cache_miss_tracker(tracker)`, `set_memory(mem)` — injectors (keeps constructor backward compatible with existing tests that call `DungeonMasterAgent(ollama, level_design, logger)`).

**Constructor change** (keep positional args, add keyword args with safe defaults):
```
def __init__(self, ollama_service, level_design_service, llm_logger,
             social_service=None, content_repository=None,
             model_name: str = "qwen2.5-coder:7b-instruct",
             temperature: float = 0.7,
             max_prompt_chars: int = 8000):
    ...
    self._model_name = model_name          # was hardcoded "gpt-oss"
    self._temperature = temperature
    self._max_prompt_chars = max_prompt_chars
    self._llm_map_generator = LLMMapGenerator(ollama_service, llm_logger)
    self._memory = DMGlobalMemory(max_tokens=llm_logger.metrics.max_context_tokens)
    self._behavior_library = BehaviorLibrary(content_repository)
    self._swarm_template_service = SwarmTemplateService()
    self._cache_miss_tracker = CacheMissTracker(similarity_threshold=0.75)
```

**`llm_worker.py` changes:**
- DELETE `class LLMWorker.evaluate_player_stats`, `_build_evaluation_prompt`, `_query_llm`, `_parse_evaluation_response` (lines 223-323). Keep `LLMWorker` class + `llm_worker_func`.
- ADD `map_generation` branch in `llm_worker_func` (after the `content_monsters` branch):
```
elif call_type == 'map_generation':
    result = dm_agent.generate_map(
        description=request.get('description', ''),
        width=request.get('width', 60),
        height=request.get('height', 40),
        depth=request.get('depth', 1),
    )
    response_queue.put({'map_data': result.to_map_data() if result else None, 'success': result is not None})
```
- In every branch, before `dm_agent.*` call, call `dm_agent.track_prompt(prompt)` (cache-miss) — see Item 7. For branches that build prompt internally (behavior/level), the agent tracks inside its own methods, so worker needs no change there.

**Data flow:** `darkdelve.py` builds `DungeonMasterAgent(ollama, level_design, logger, model_name=dm_config['model'], temperature=dm_config['temperature'], max_prompt_chars=dm_config.get('max_prompt_chars', 8000))`.

**Telemetry:** none new for Item 1 itself (reuses existing `LLMCallLog`).

**Integration:** `LLMMapGenerator.generate_map_async` already enqueues `type:"map_generation"`; worker now handles it via the agent. `DynamicDifficultyService` stays deterministic and unchanged.

**Risks/gotchas:** Removing `evaluate_player_stats` from `LLMWorker` — verify no caller. Search confirmed only `Mock(spec=LLMWorker)` in tests; safe. Keep `LLMWorker` import of `DungeonMasterAgent` (already present).

**Test plan:** `tests/test_dungeon_master_agent.py` add:
```
def test_evaluate_player_stats_default_on_failure(self):
    agent = DungeonMasterAgent(ollama=Mock(), level_design=Mock(), llm_logger=Mock())
    agent.ollama.generate.side_effect = RuntimeError("boom")
    out = agent.evaluate_player_stats({"health":10,"attack":5}, 1)
    assert out["difficulty_modifier"] == 1.0
```
`tests/test_llm_worker.py` add: assert `hasattr(LLMWorker, 'evaluate_player_stats') is False`.

---

### Item 2 — Global Throttled Poetic DM Memory

**New value object** `src/domain/value_objects/dm_memory.py`:
```
@dataclass
class DMGlobalMemory:
    summary: str = ""                 # condensed poetic-prose dungeon state
    max_tokens: int = 8192
    version: int = 0
    last_updated_level: int = 0

    def refresh(self, narrative: str, headroom_tokens: int) -> None:
        # Combine old summary + new narrative, then bound to headroom.
        combined = f"{self.summary}\n{narrative}".strip()
        est = estimate_tokens(combined)
        if est > headroom_tokens:
            # Keep the most recent ~headroom_tokens worth (poetic tail).
            allowed_chars = max(0, headroom_tokens * 4)
            self.summary = combined[-allowed_chars:]
        else:
            self.summary = combined
        self.version += 1

    def context_string(self) -> str:
        return self.summary

    def truncate_to_headroom(self, headroom_tokens: int) -> str:
        if estimate_tokens(self.summary) <= headroom_tokens:
            return self.summary
        return self.summary[-(headroom_tokens * 4):]
```

**`DungeonMasterAgent` changes:**
- Hold `self._memory: DMGlobalMemory`.
- `refresh_memory(level_number: int, narrative: str) -> None`:
```
def refresh_memory(self, level_number: int, narrative: str) -> None:
    diag = self.logger.check_headroom(narrative, system_prompt=self._memory.summary)
    headroom = diag.headroom_tokens
    self._memory.refresh(narrative, headroom)
    self._memory.last_updated_level = level_number
    self.logger.log_memory_refresh(level_number, len(self._memory.summary), headroom)
```
- `get_memory_context() -> str` returns `self._memory.truncate_to_headroom(diag.headroom_tokens)` and is prepended to EVERY DM prompt (behavior/level/map/content/difficulty) via `_prepare_prompt`.
- Memory is GLOBAL (one instance), NOT per-monster. Injected into `generate_behavior_script` prompt as a `DM MEMORY:` section.

**`darkdelve.py` change:** at level generation (after `_generate_standard_level` / `_generate_floor1`), call:
```
if self.dm_enabled:
    self.dm_agent.refresh_memory(self.state.level, narrative_text)
```
where `narrative_text` is a short poetic summary built from level theme + performance.

**Config keys:** none new (uses `check_headroom` + `max_context_tokens`).

**Telemetry schema addition** (`llm_logger`):
```
{"event_type":"dm_memory_refresh","timestamp":<iso>,"level_number":int,
 "summary_chars":int,"headroom_tokens":int,"version":int}
```

**Integration:** `check_headroom` already exists in [`llm_logging.py`](src/domain/value_objects/llm_logging.py:288). Memory feeds `generate_behavior_script` (proves not per-monster — single store).

**Risks/gotchas:** Memory must never exceed headroom or it defeats the throttle. Always call `truncate_to_headroom` before injecting. Keep summary bounded to `headroom_tokens*4` chars (4 chars/token per `estimate_tokens`).

**Test plan:** `tests/test_dm_memory.py`:
```
def test_memory_bounded_by_headroom():
    mem = DMGlobalMemory(max_tokens=100)
    mem.refresh("A"*1000, headroom_tokens=20)   # 20 tokens ~ 80 chars
    assert estimate_tokens(mem.summary) <= 20
def test_refresh_at_level_boundary():
    logger = Mock(); logger.check_headroom.return_value = SimpleNamespace(headroom_tokens=500)
    agent = DungeonMasterAgent(Mock(), Mock(), logger)
    agent.refresh_memory(2, "The crypt deepens.")
    assert "crypt" in agent.get_memory_context()
```

---

### Item 3 — Swarm / Formation Templates + Leader Commands

**New service** `src/domain/services/swarm_template_service.py`:
```
INTELLIGENCE_TIERS = {1:"bestial",2:"simple",3:"tactical",4:"cunning",5:"brilliant"}

@dataclass
class SwarmTemplate:
    template_id: str
    tier: int
    description: str
    root_node: BehaviorNode   # built from catalog-valid conditions/actions

class SwarmTemplateService:
    def __init__(self):
        self._templates = self._build_default_templates()   # tier -> [SwarmTemplate]

    def select_template(self, mob_type: str, intelligence_tier: int) -> SwarmTemplate:
        tier = max(1, min(5, intelligence_tier))
        pool = self._templates.get(tier, self._templates[1])
        return pool[0]

    def build_script(self, template: SwarmTemplate, entity_id: str) -> BehaviorScript:
        # Deep-copy template.root_node, tag entity_id, is_plan=True
        ...

    def issue_leader_command(self, leader_id: str, command: str,
                             subordinate_ids: List[str], event_bus) -> None:
        if event_bus:
            event_bus.publish("leader_command", {
                "leader_id": leader_id, "command": command,
                "subordinate_ids": subordinate_ids})
```

Default templates (examples, all catalog-valid):
- tier1 "surround_player": selector[attack(can_see_player), move_to(player_last_known), patrol]
- tier3 "flee_to_pack": selector[flee(health_below 0.3), follow_leader, patrol]
- tier4 "flee_to_stronger_mob": selector[flee, move_to(strongest_ally), patrol]
- tier5 "coordinate_ambush": selector[call_allies, attack, follow_leader]

**`entity_ai_orchestrator.py` change:** add `swarm_template_service` param; in `tick()`, after perception, for each social structure with a leader, call `swarm_template_service.select_template(mob_type, tier)` ONCE per group and assign the resulting script to all members' `BehaviorComponent` (via `set_script`) only when their `current_script is None`. Leader mobs call `issue_leader_command` when player detected.

**Leader command handling:** a handler subscribes to `"leader_command"` and sets `orders` on subordinate `BehaviorComponent.state["orders"]` so `BehaviorScriptService` `has_orders` condition fires. (Reuse existing `has_orders` condition in [`behavior_script_service.py`](src/domain/services/behavior_script_service.py:322).)

**Data flow:** AI picks template per GROUP (not per monster) → scripts reused until `None` (per `behavior_component`). Leader barks via event_bus → subordinates get orders.

**Config keys:** none (tiers derived from mob intelligence; optionally `swarm_templates_path` later).

**Telemetry schema additions:**
```
{"event_type":"swarm_template_selected","timestamp":<iso>,"mob_type":str,"tier":int,"template_id":str}
{"event_type":"leader_command","timestamp":<iso>,"leader_id":str,"command":str,"subordinate_count":int}
```

**Integration:** Uses `SocialService` structures (leader/members) from [`social_service.py`](src/domain/services/social_service.py:149). Event bus is the string-topic bus already used by orchestrator.

**Risks/gotchas:** Templates MUST only use conditions/actions present in `MOB_BEHAVIOR_CATALOG` for the mob type or `BehaviorScriptService.validate_script` will strip them. Build templates from the catalog. Do NOT micro-manage per monster — one template per group.

**Test plan:** `tests/test_swarm_template.py`:
```
def test_select_template_tier_clamped():
    svc = SwarmTemplateService()
    t = svc.select_template("goblin", 99)
    assert t.tier == 5
def test_leader_command_published():
    bus = Mock()
    svc = SwarmTemplateService()
    svc.issue_leader_command("L1","flee_to_pack",["m1","m2"], bus)
    bus.publish.assert_called_once_with("leader_command", {"leader_id":"L1","command":"flee_to_pack","subordinate_ids":["m1","m2"]})
```

---

### Item 4 — Single Model Config

**`config/game.yaml`** change at [`config/game.yaml`](config/game.yaml:171):
```
dungeon_master:
  enabled: true
  model: "qwen2.5-coder:7b-instruct"   # was "gpt-oss"
  temperature: 0.7
  ollama_endpoint: "http://localhost:11434"
  log_path: "logs/llm_activity.json"
  max_calls_per_turn: 5
  enable_behavior_generation: true
  enable_level_design: false
  max_prompt_chars: 8000               # NEW (Item 5 default)
  dm_model: "qwen2.5-coder:7b-instruct"   # NEW single source alias
  dm_temperature: 0.7                     # NEW
```

**`DungeonMasterAgent` change:** remove hardcoded `"gpt-oss"` default (line 44). Constructor takes `model_name`/`temperature` (Item 1). `set_model` unchanged.

**`darkdelve.py` change:** pass `model_name=dm_config.get('model','qwen2.5-coder:7b-instruct')`, `temperature=dm_config.get('temperature',0.7)`, `max_prompt_chars=dm_config.get('max_prompt_chars',8000)`.

**`player_agent.py`** (`DEFAULT_MODEL="qwen2.5:7b-instruct"`) is the PLAYTESTER model, changed by Item 8 to MCP (no model needed). Leave as-is for now; Item 8 removes Ollama usage.

**Data flow:** `game.yaml` → `dm_config` → `DungeonMasterAgent(model_name=...)`. No other model string anywhere.

**Telemetry:** none new.

**Integration:** `LLMLogger` already records `model`/`temperature` per call (fields exist in [`llm_logging.py`](src/domain/value_objects/llm_logging.py:93)).

**Risks/gotchas:** Grep for `"gpt-oss"` — only in `dungeon_master_agent.py:44` and `config/game.yaml:173`. Remove both. Tests `test_set_model` (in [`test_dungeon_master_agent.py`](tests/test_dungeon_master_agent.py:319)) sets model explicitly, still passes.

**Test plan:**
```
def test_default_model_is_qwen(tmp_path):
    logger = LLMLogger(log_dir=tmp_path)
    agent = DungeonMasterAgent(Mock(), Mock(), logger)
    assert agent._model_name == "qwen2.5-coder:7b-instruct"
```


---

### Item 5 — Truncation + Truncation Logging

**New value object** `src/domain/value_objects/truncation_info.py`:
```
@dataclass
class TruncationInfo:
    original_chars: int
    truncated_chars: int
    dropped_sections: List[str]
    was_truncated: bool
```

**`llm_logging.py` changes:**
- Add `TruncationInfo` to `__all__`.
- Add method to `LLMLogger`:
```
def truncate_prompt(self, prompt: str, max_chars: int = 8000) -> Tuple[str, TruncationInfo]:
    original = len(prompt)
    if original <= max_chars:
        return prompt, TruncationInfo(original, original, [], False)
    # Drop from the middle, keep head (system/instructions) + tail (current state).
    keep = max_chars
    head = prompt[: int(keep * 0.7)]
    tail = prompt[-int(keep * 0.3):]
    dropped = ["<middle truncated>"]
    return head + "\n...[truncated]...\n" + tail, TruncationInfo(original, keep, dropped, True)

def log_truncation(self, call_id: str, context: str, info: TruncationInfo) -> None:
    entry = {"event_type":"prompt_truncation","timestamp":time.time(),"call_id":call_id,
             "context":context,"original_chars":info.original_chars,
             "truncated_chars":info.truncated_chars,"dropped_sections":info.dropped_sections}
    # append to a truncation telemetry file playtest/telemetry/truncation.jsonl
    path = os.path.join(self.log_dir, "truncation.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
```
- Add to `LLMCallLog` (dataclass fields, lines ~96): `truncated: bool = False`, `truncated_chars: int = 0`, `truncation_sections: List[str] = field(default_factory=list)`. Update `to_dict()` accordingly.

**`DungeonMasterAgent` change — single helper applied to ALL prompts:**
```
def _prepare_prompt(self, prompt: str, context: str, call_id: str) -> str:
    truncated, info = self.logger.truncate_prompt(prompt, self._max_prompt_chars)
    if info.was_truncated:
        self.logger.log_truncation(call_id, context, info)
    # inject global memory context at top
    memory = self.get_memory_context()
    if memory:
        truncated = f"DM MEMORY:\n{memory}\n\n{truncated}"
    return truncated
```
Replace direct `self.ollama.generate(prompt)` calls in `generate_behavior_script`, `design_level`, `generate_map`, `generate_item_batch`, `generate_monster_batch`, `_call_llm_json`, `evaluate_player_stats` with `self.ollama.generate(self._prepare_prompt(prompt, context, call_id))` and set `truncated`/`truncated_chars` on the `LLMCallLog`.

**Config key:** `dungeon_master.max_prompt_chars` (default 8000).

**Telemetry schema addition:**
```
{"event_type":"prompt_truncation","timestamp":float,"call_id":str,"context":str,
 "original_chars":int,"truncated_chars":int,"dropped_sections":[str]}
```

**Integration:** Every DM prompt path funnels through `_prepare_prompt` → memory injection + truncation + logging. `check_headroom` still used for context diagnostics.

**Risks/gotchas:** Truncation must preserve the JSON-format instruction at the tail (behavior/level/map prompts end with "Respond with ONLY JSON"). Keep tail 30% so the format directive survives. Never truncate below the point the parser needs.

**Test plan:** `tests/test_truncation_logging.py`:
```
def test_truncate_logs_when_over_limit(tmp_path):
    logger = LLMLogger(log_dir=tmp_path)
    big = "x" * 9000
    out, info = logger.truncate_prompt(big, max_chars=8000)
    assert info.was_truncated and info.original_chars == 9000
    logger.log_truncation("c1","behavior",info)
    assert (tmp_path/"truncation.jsonl").exists()
def test_no_truncation_under_limit(tmp_path):
    logger = LLMLogger(log_dir=tmp_path)
    out, info = logger.truncate_prompt("small", 8000)
    assert not info.was_truncated
```

---

### Item 6 — Behavior Library + Fallback

**New service** `src/domain/services/behavior_library.py`:
```
class BehaviorLibrary:
    def __init__(self, content_repository=None, persist_path: str = "cache/behavior_library.json"):
        self._repo = content_repository
        self._persist_path = persist_path
        self._entries: Dict[str, BehaviorScript] = self._load()

    def select_script(self, mob_type: str, situation: str) -> Optional[BehaviorScript]:
        # exact mob_type match, else "default"
        for key in (mob_type, "default"):
            if key in self._entries:
                return self._entries[key]
        return None

    def author_script(self, dm_agent, mob_type: str, situation: str) -> Optional[BehaviorScript]:
        # dm_agent generates a new BehaviorScript; validate vs MOB_BEHAVIOR_CATALOG;
        # store under mob_type key; persist.
        ...

    def get_fallback(self, mob_type: str) -> BehaviorScript:
        # NEVER let monsters freeze: return BehaviorScriptService.create_default_script(mob_type, mob_type)
        svc = BehaviorScriptService(action_dispatcher=None)
        return svc.create_default_script(mob_type, f"{mob_type}_fallback")

    def _load(self) -> Dict[str, BehaviorScript]: ...   # read persist_path JSON -> BehaviorScript
    def _persist(self) -> None: ...                      # write entries to persist_path
```

**`DungeonMasterAgent.generate_behavior_script` rewrite (decision order):**
```
1. template = self._behavior_library.select_script(mob_type, situation)
   if template: return template            # library hit, no LLM call
2. script = self._generate_via_llm(...)    # existing LLM path (now via _prepare_prompt)
   if script:
       self._behavior_library.author_store(mob_type, script)  # cache new entry
       return script
3. return self._behavior_library.get_fallback(mob_type)   # monsters never freeze
```

**Data flow:** library select (no LLM) → LLM author (on miss) → fallback (on LLM failure). Persisted to `cache/behavior_library.json`.

**Config keys:** none (persist path constant; could add `behavior_library_path`).

**Telemetry schema additions:**
```
{"event_type":"behavior_library_hit","timestamp":<iso>,"mob_type":str,"script_id":str}
{"event_type":"behavior_library_miss","timestamp":<iso>,"mob_type":str}
{"event_type":"behavior_library_fallback","timestamp":<iso>,"mob_type":str,"script_id":str}
```

**Integration:** Uses `BehaviorScriptService.create_default_script` ([`behavior_script_service.py`](src/domain/services/behavior_script_service.py:417)) as the safe fallback. Validated against `MOB_BEHAVIOR_CATALOG`.

**Risks/gotchas:** Fallback must ALWAYS return a valid script even if LLM and repo are down — `create_default_script` is pure (no I/O). Ensure `get_fallback` has no LLM/network dependency.

**Test plan:** `tests/test_behavior_library.py`:
```
def test_fallback_never_none():
    lib = BehaviorLibrary()
    assert lib.get_fallback("goblin") is not None
def test_select_then_author():
    lib = BehaviorLibrary()
    agent = Mock(); agent.generate_behavior_script.return_value = None
    assert lib.select_script("slime","x") is None
    # author path returns fallback when LLM fails
    assert lib.get_fallback("slime") is not None
```

---

### Item 7 — Cache-Miss Tracker (prerequisite to caching)

**New service** `src/domain/services/cache_miss_tracker.py`:
```
import difflib, time, json, os

class CacheMissTracker:
    def __init__(self, similarity_threshold: float = 0.75,
                 telemetry_path: str = "playtest/telemetry/cache_miss.jsonl"):
        self._threshold = similarity_threshold
        self._telemetry_path = telemetry_path
        self._last_prompt: Optional[str] = None

    def track_prompt(self, prompt: str, context: str = "behavior") -> bool:
        # Returns True if this is a CACHE MISS (not similar enough to last).
        # ONLY logs telemetry. Does NOT serve cached responses (caching later).
        is_miss = True
        similarity = 0.0
        if self._last_prompt is not None:
            similarity = difflib.SequenceMatcher(None, self._last_prompt, prompt).ratio()
            is_miss = similarity < self._threshold
        self._emit(context, similarity, is_miss, prompt)
        self._last_prompt = prompt
        return is_miss

    def _emit(self, context, similarity, is_miss, prompt) -> None:
        entry = {"event_type":"cache_miss","timestamp":time.time(),"context":context,
                 "similarity":round(similarity,3),"is_miss":is_miss,
                 "prompt_hash":hash(prompt) % (10**8)}
        os.makedirs(os.path.dirname(self._telemetry_path), exist_ok=True)
        with open(self._telemetry_path,"a") as f:
            f.write(json.dumps(entry)+"\n")
```

**`DungeonMasterAgent` change:** hold `self._cache_miss_tracker`; call `self._cache_miss_tracker.track_prompt(prompt, context)` at the START of every LLM method (before `_prepare_prompt`). This is the single hook the worker relies on (Item 1) — agent owns it so both sync and async paths log.

**Data flow:** prompt → `track_prompt` (logs similarity/miss) → `_prepare_prompt` → LLM. No cache serving yet.

**Config keys:** none (threshold constant 0.75; could add `cache_similarity_threshold`).

**Telemetry schema addition:**
```
{"event_type":"cache_miss","timestamp":float,"context":str,"similarity":float,"is_miss":bool,"prompt_hash":int}
```

**Integration:** Pure pre-cache instrumentation. Later caching stage will read these logs. No change to `LLMLogger` required (separate jsonl file).

**Risks/gotchas:** `difflib.SequenceMatcher.ratio()` on very long prompts is O(n^2); cap compared length to first 4000 chars to stay cheap. Do NOT block on it. Must never return a cached response (that is a later phase).

**Test plan:** `tests/test_cache_miss_tracker.py`:
```
def test_similar_prompt_is_hit(tmp_path):
    t = CacheMissTracker(telemetry_path=str(tmp_path/"c.jsonl"))
    t.track_prompt("generate behavior for goblin at 5,5")
    miss = t.track_prompt("generate behavior for goblin at 5,5")  # identical
    assert miss is False   # >=0.75 similar => not a miss
def test_different_prompt_is_miss(tmp_path):
    t = CacheMissTracker(telemetry_path=str(tmp_path/"c.jsonl"))
    t.track_prompt("attack the player")
    assert t.track_prompt("flee to pack now") is True
```

---

### Item 8 — Playtester Uses MCP, Not Local LLM

**`player_agent.py` change — add `MCPPlayerAgent`:**
```
class MCPPlayerAgent(PlayerAgent):
    """Decides player actions via MCPToolkit state reads (no Ollama/LLM)."""
    def __init__(self, toolkit: "MCPToolkit", game=None, safe_action: str = "e"):
        self.toolkit = toolkit
        self.game = game
        self.safe_action = safe_action
        self.history = []

    def decide(self, map_text="", stats=None, history=None, instruction_text=None) -> PlayerDecision:
        # Inspect world via MCP toolkit (no LLM).
        ents = self.toolkit.list_entities()
        # Deterministic safe policy: if a monster is adjacent -> attack toward it,
        # else move toward stairs (request_map_section), else wait.
        action = self._safe_policy(ents)
        decision = PlayerDecision(macro_goal="MCP auto-play", reasoning="MCP toolkit policy",
                                  action=action, telemetry_notes="no-LLM")
        self.record_turn(decision)
        return decision

    def _safe_policy(self, entities) -> str:
        # simple: return safe_action ("e") by default; real policy can use
        # request_map_section to find stairs and step toward them.
        return self.safe_action
```

**`ollama_playtester.py` change — add `MCPPlaytester`:**
```
class MCPPlaytester:
    """In-process playtester driving Game via MCPToolkit + Game.process_action (no Ollama)."""
    def __init__(self, game, toolkit=None, agent=None, telemetry_store=None,
                 instruction_bus=None, max_turns=200):
        self.game = game
        self.toolkit = toolkit or MCPToolkit(game=game)
        self.agent = agent or MCPPlayerAgent(self.toolkit, game=game)
        self.telemetry_store = telemetry_store or TelemetryStore()
        self.instruction_bus = instruction_bus
        self.max_turns = max_turns

    def run(self) -> PlaytestResult:
        # render -> decide (MCPPlayerAgent) -> game.process_action(action) -> telemetry
        turns = 0
        while turns < self.max_turns and not self.game.state.game_over:
            frame_text = self._render_frame()
            decision = self.agent.decide(frame_text, self._stats())
            self.game.process_action(decision.action)   # uses Game.process_action
            entry = self._turn_entry(turns, frame_text, decision)
            self.telemetry_store.append(self.config_telemetry_path, entry)
            turns += 1
        return PlaytestResult(status="done", returncode=0, turns=turns, ...)
```
- Keep `OllamaPlaytester` for the LLM-driven path; default playtest entrypoint (`main`) switches to `MCPPlaytester` when `playtest.mode == "mcp"` (new config key under `playtest:`).
- `Game.process_action` already exists ([`darkdelve.py`](darkdelve.py:2112)); pass `render_to_stdout=False`. Construct `Game` with `auto_initialize=False` when caller already initialized (per gotchas [`gotchas.md`](architecture/gotchas.md:95)).

**Config key** (add to `config/game.yaml` `playtest:` section): `mode: "mcp"` (options: `mcp` | `ollama`).

**Data flow:** `MCPPlaytester` → `MCPPlayerAgent.decide` reads `MCPToolkit.list_entities()`/`request_map_section()` → returns action → `Game.process_action(action)` → telemetry. No second Ollama instance, no `requests` call.

**Telemetry schema:** reuses existing `turn` entries from `OllamaPlaytester._turn_entry` (copy helper into `MCPPlaytester`).

**Integration:** Uses `MCPToolkit` ([`mcp_toolkit.py`](src/infrastructure/services/mcp_toolkit.py:22)) — the SAME toolkit the DM uses. `Game.process_action` per gotchas. Removes `player_agent.py` Ollama/`requests` dependency for the default playtest.

**Risks/gotchas:** `MCPPlayerAgent._safe_policy` must NEVER return an action outside `VALID_ACTIONS` (validated by `PlayerAgent.validate_response` parent). Default to `SAFE_FALLBACK_ACTION = "e"`. In-process loop must follow `render -> decide -> process_action -> telemetry` order (gotchas). Keep `playtest.enabled` disabled for normal human play.

**Test plan:** `tests/test_mcp_playtester.py`:
```
def test_mcp_playtester_runs_with_fake_game():
    game = Mock(); game.state = SimpleNamespace(game_over=False)
    game.process_action = Mock()
    agent = Mock(); agent.decide.return_value = PlayerDecision("g","r","e","n")
    pt = MCPPlaytester(game, agent=agent, max_turns=3)
    res = pt.run()
    assert res.turns == 3
    assert game.process_action.call_count == 3
def test_mcp_player_agent_returns_valid_action():
    tk = Mock(); tk.list_entities.return_value = []
    agent = MCPPlayerAgent(tk)
    d = agent.decide()
    assert d.action in ("w","a","s","d","e","i","m","up","down","enter","escape")
```

## 5. Consolidated Import Statements

```python
# src/domain/agents/dungeon_master_agent.py
from src.domain.value_objects.dm_memory import DMGlobalMemory
from src.domain.services.behavior_library import BehaviorLibrary
from src.domain.services.swarm_template_service import SwarmTemplateService
from src.domain.services.cache_miss_tracker import CacheMissTracker
from src.domain.services.llm_map_generator import LLMMapGenerator
from src.domain.value_objects.truncation_info import TruncationInfo
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog, estimate_tokens

# src/domain/value_objects/llm_logging.py
from src.domain.value_objects.truncation_info import TruncationInfo

# src/application/services/llm_worker.py
from src.domain.services.cache_miss_tracker import CacheMissTracker  # optional local use

# src/domain/services/entity_ai_orchestrator.py
from src.domain.services.swarm_template_service import SwarmTemplateService

# player_agent.py
from src.infrastructure.services.mcp_toolkit import MCPToolkit
from src.domain.value_objects.behavior_script import BehaviorScript  # for PlayerDecision typing

# ollama_playtester.py
from src.infrastructure.services.mcp_toolkit import MCPToolkit
from player_agent import MCPPlayerAgent, PlayerDecision, SAFE_FALLBACK_ACTION
```

## 6. Consolidated Test Plan (new files)

All new test files live under `tests/` and use `src.` imports. Exact assertions shown per item above
(§4 Items 1-8). Run with: `python -m pytest tests/test_dm_memory.py tests/test_truncation_logging.py
tests/test_cache_miss_tracker.py tests/test_behavior_library.py tests/test_swarm_template.py
tests/test_mcp_playtester.py -v`. Acceptance: all 86+ existing tests stay green + these new tests pass.

## 7. Integration Notes (cross-cutting)

- `DungeonMasterAgent` becomes the single owner of: behavior, level design, map generation
  (`LLMMapGenerator`), content batches, difficulty eval (moved from `LLMWorker`), global memory,
  behavior library, swarm templates, cache-miss tracking.
- `darkdelve.py` is the ONLY wiring point: it reads `dungeon_master` config, builds the agent with
  model/temperature/max_prompt_chars, and calls `refresh_memory` at each level boundary.
- `llm_worker_func` now handles `map_generation` (delegates to agent) and no longer owns difficulty eval.
- `EntityAIOrchestrator` gains `swarm_template_service`; picks ONE template per social group and assigns
  to members only when `current_script is None` (respects `behavior_component` persistence).
- Leader commands flow through the EXISTING string-topic `event_bus.publish("leader_command", {...})`.
- Playtester default path switches from Ollama to `MCPPlaytester`+`MCPPlayerAgent` (same `MCPToolkit` as DM).
- All new telemetry is appended as line-delimited JSON to `playtest/telemetry/*.jsonl` (memory refresh,
  truncation, cache_miss, behavior_library_*, swarm_template_selected, leader_command) — separate from
  `LLMCallLog` flush to avoid breaking existing `llm_performance.json` consumers.

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Removing `LLMWorker.evaluate_player_stats` breaks a test | Only `Mock(spec=LLMWorker)` references it; no live caller. Keep `DynamicDifficultyService` deterministic & unchanged. |
| Memory exceeds context headroom | Always call `truncate_to_headroom(headroom_tokens)` before injecting; bound to `headroom*4` chars. |
| Truncation drops JSON format directive | Keep tail 30% of prompt (format instruction lives at tail). |
| Swarm template uses invalid condition/action | Build templates strictly from `MOB_BEHAVIOR_CATALOG`; run `BehaviorScriptService.validate_script`. |
| Behavior library fallback depends on LLM/repo | `get_fallback` uses pure `BehaviorScriptService.create_default_script` (no I/O). |
| Cache-miss `SequenceMatcher` O(n^2) on huge prompts | Compare only first 4000 chars; never block; telemetry-only (no serving). |
| MCPPlayerAgent returns invalid action | Default to `SAFE_FALLBACK_ACTION="e"`; parent `validate_response` re-validates. |
| In-process playtester double-inits game | Construct `Game(auto_initialize=False)` when already initialized (gotchas). |
| Hardcoded `"gpt-oss"` lingers | Grep both `dungeon_master_agent.py` and `config/game.yaml`; replace with `qwen2.5-coder:7b-instruct`. |

## 9. Architecture Doc Updates

- `architecture/agent_system.md`: add section "Unified DungeonMasterAgent" describing memory/library/swarm/
  difficulty ownership; note `LLMWorker.evaluate_player_stats` removed; add `MCPPlaytester` to the
  "Implemented Features" list (replaces Ollama-only playtester).
- `architecture/system_overview.md`: update "Local Ollama Player AI Playtest Data Flow" → note MCP-driven
  playtester option (`playtest.mode: mcp`); mark Phase 6 still In Progress; add DM memory/throttle note.
- `architecture/gotchas.md`: add "DM Single Model Config" gotcha (never hardcode model; read
  `dungeon_master.model` from `game.yaml`); add "Global DM Memory is not per-monster" note; add
  "Cache-Miss Tracker is pre-cache (telemetry only)" note.
- `architecture/INDEX.md`: add new files `dm_memory.py`, `behavior_library.py`, `swarm_template_service.py`,
  `cache_miss_tracker.py`, `truncation_info.py` to the inventory.
