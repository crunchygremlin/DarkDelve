# GPU Persistence Verification Report

**Task:** T-2026-0629-004 — LLM Model GPU Persistence  
**Date:** 2026-06-29T04:15:00Z  
**Tester:** Playtester (automated)  
**Verdict:** ✅ PASS

---

## 1. Test Results

### New Tests: `tests/test_ollama_gpu_persistence.py`
```
15 passed in 0.14s
```

| Test | Status |
|------|--------|
| `test_default_keep_alive_is_2h` | ✅ PASSED |
| `test_custom_keep_alive_in_constructor` | ✅ PASSED |
| `test_generate_includes_keep_alive_in_payload` | ✅ PASSED |
| `test_generate_keep_alive_override_via_kwargs` | ✅ PASSED |
| `test_generate_keep_alive_none_omits_from_payload` | ✅ PASSED |
| `test_generate_sets_model_loaded_flag` | ✅ PASSED |
| `test_purge_skips_if_not_started` | ✅ PASSED |
| `test_purge_skips_if_model_not_loaded` | ✅ PASSED |
| `test_purge_sends_keep_alive_zero` | ✅ PASSED |
| `test_purge_clears_model_loaded_flag` | ✅ PASSED |
| `test_purge_handles_error_gracefully` | ✅ PASSED |
| `test_purge_handles_non_200_response` | ✅ PASSED |
| `test_stop_calls_purge_before_terminate` | ✅ PASSED |
| `test_default_keep_alive_is_2h` (EmbeddedOllama) | ✅ PASSED |
| `test_config_keep_alive_read_from_yaml` | ✅ PASSED |

### Full Test Suite
```
1057 passed, 3 warnings, 18 subtests passed in 14.32s
```
**No regressions.** All pre-existing tests continue to pass.

---

## 2. Code Inspection

### 2.1 `OllamaService.generate()` — keep_alive in payload
**File:** [`src/infrastructure/external/ollama_service.py:81-107`](../src/infrastructure/external/ollama_service.py:81)

- `keep_alive` defaults to `"2h"` in constructor (line 22)
- `generate()` reads `kwargs.get("keep_alive", self.keep_alive)` (line 93)
- If not `None`, adds `payload["keep_alive"]` (lines 94-95)
- If `None`, omits from payload (backward compatible)

**Verdict:** ✅ Correct

### 2.2 `OllamaService.purge()` — sends `keep_alive: "0"`
**File:** [`src/infrastructure/external/ollama_service.py:123-150`](../src/infrastructure/external/ollama_service.py:123)

- Guard: skips if `not self._started or not self._model_loaded` (line 130)
- Payload: `{"model": ..., "prompt": "", "stream": False, "keep_alive": "0"}` (lines 133-138)
- On success: sets `self._model_loaded = False` (line 145)
- On exception: swallows error, returns `False` (lines 147-149)

**Verdict:** ✅ Correct

### 2.3 `OllamaService.stop()` — calls `purge()` first
**File:** [`src/infrastructure/external/ollama_service.py:152-158`](../src/infrastructure/external/ollama_service.py:152)

- Calls `self.purge()` before `self._process.terminate()` (line 155)

**Verdict:** ✅ Correct

### 2.4 `EmbeddedOllama` (darkdelve.py) — same pattern
**File:** [`darkdelve.py:86-249`](../darkdelve.py:86)

- Constructor accepts `keep_alive: str = "2h"` (line 89)
- `generate()` includes keep_alive in payload (lines 184-187)
- `purge()` sends `keep_alive: "0"` (lines 214-241)
- `stop()` calls `purge()` first (lines 243-249)

**Verdict:** ✅ Correct — mirrors `OllamaService` exactly

### 2.5 `config/game.yaml` — keep_alive configured
**File:** [`config/game.yaml:133`](../config/game.yaml:133)

```yaml
llm:
  keep_alive: "2h"
```

**Verdict:** ✅ Correct

### 2.6 `ApplicationFactory.create_ollama_service()` — passes keep_alive from config
**File:** [`src/application_factory.py:36-41`](../src/application_factory.py:36)

```python
def create_ollama_service(self) -> OllamaService:
    config = self.load_config()
    model = config.get('llm.model', 'qwen2.5-coder:7b-instruct')
    keep_alive = config.get('llm.keep_alive', '2h')
    return OllamaService(model=model, keep_alive=keep_alive)
```

**Verdict:** ✅ Correct — reads from config with fallback default

---

## 3. Behavior Summary

| Scenario | Expected | Actual | Status |
|----------|----------|--------|--------|
| Default keep_alive | `"2h"` | `"2h"` | ✅ |
| Custom keep_alive via constructor | `"1h"` | `"1h"` | ✅ |
| keep_alive in generate payload | present | present | ✅ |
| keep_alive override per-call | `"30m"` | `"30m"` | ✅ |
| keep_alive=None omits from payload | absent | absent | ✅ |
| _model_loaded set after generate | True | True | ✅ |
| purge() sends keep_alive="0" | `"0"` | `"0"` | ✅ |
| purge() clears _model_loaded | False | False | ✅ |
| purge() on error returns False | False | False | ✅ |
| purge() on non-200 returns False | False | False | ✅ |
| stop() calls purge before terminate | yes | yes | ✅ |
| Config has keep_alive: "2h" | yes | yes | ✅ |
| Factory passes keep_alive from config | yes | yes | ✅ |

---

## 4. Conclusion

All 15 new tests pass. Full suite (1057 tests) passes with zero failures. Code inspection confirms:

1. `keep_alive` is correctly threaded through `OllamaService`, `EmbeddedOllama`, config, and factory
2. `purge()` correctly sends `keep_alive: "0"` to unload the model from GPU
3. `stop()` calls `purge()` before terminating the subprocess
4. Error handling is graceful — no exceptions escape during cleanup

**Result: PASS** — GPU persistence implementation is verified and regression-free.
