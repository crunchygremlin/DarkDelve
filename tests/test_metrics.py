import time
from main import llm_request_queue, llm_response_queue, llm_metrics, get_llm_metrics, process_llm_responses


def test_llm_metrics_update():
    # reset metrics
    llm_metrics["requests"] = 0
    llm_metrics["responses"] = 0
    llm_metrics["total_latency_ms"] = 0.0

    # simulate a request
    req = {"commander_id": "M", "prompt": "{}", "ts": time.time()}
    llm_request_queue.put(req)
    llm_metrics["requests"] += 1

    # simulate a response arriving later
    response = {"commander_id": "M", "commander_shout": "Hi", "command": "ATTACK_PLAYER", "request_ts": req["ts"], "response_ts": time.time() + 0.05}
    llm_response_queue.put(response)

    process_llm_responses([])

    metrics = get_llm_metrics()
    assert metrics["requests"] >= 1
    assert metrics["responses"] >= 1
    assert metrics["avg_latency_ms"] > 0
