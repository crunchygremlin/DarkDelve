"""LLM worker thread for background processing of LLM requests."""

import time
import threading
from typing import Optional, Any
from queue import Queue, Empty

from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.agents.dungeon_master_agent import DungeonMasterAgent
from src.domain.value_objects.perception import PerceptionStatus


def llm_worker_func(
    request_queue: Queue,
    response_queue: Queue,
    dm_agent: DungeonMasterAgent,
    llm_logger: LLMLogger,
    max_calls_per_turn: int = 5,
):
    """Background worker that processes LLM requests from the queue.
    
    Args:
        request_queue: Queue to read LLM requests from
        response_queue: Queue to put LLM responses to
        dm_agent: DungeonMasterAgent for generating behavior scripts
        llm_logger: Logger for recording LLM calls
        max_calls_per_turn: Maximum calls allowed per game turn
    """
    calls_this_turn = 0
    last_turn = -1
    
    while True:
        try:
            # Get request with timeout to allow checking turn changes
            request = request_queue.get(timeout=0.5)
            
            if request is None:
                # Shutdown signal
                break
            
            # Reset call counter if turn changed
            current_turn = request.get('turn_number', 0)
            if current_turn != last_turn:
                calls_this_turn = 0
                last_turn = current_turn
            
            # Check throttle limit
            if calls_this_turn >= max_calls_per_turn:
                response_queue.put({
                    'entity_id': request.get('entity_id'),
                    'error': 'max_calls_exceeded',
                    'success': False,
                })
                request_queue.task_done()
                continue
            
            call_type = request.get('type', 'behavior')
            start_time = time.time()
            
            try:
                if call_type == 'behavior':
                    # Convert perception dict to PerceptionStatus object if needed
                    perception_data = request.get('perception', {})
                    perception = (
                        PerceptionStatus.from_dict(perception_data)
                        if isinstance(perception_data, dict)
                        else perception_data
                    )
                    result = dm_agent.generate_behavior_script(
                        entity_id=request.get('entity_id', ''),
                        mob_type=request.get('mob_type', 'default'),
                        perception=perception,
                        social_context=request.get('social_context', ''),
                        valid_conditions=request.get('valid_conditions', []),
                        valid_actions=request.get('valid_actions', []),
                    )
                    
                    response_queue.put({
                        'entity_id': request.get('entity_id'),
                        'behavior_script': result.to_dict() if result else None,
                        'success': result is not None,
                    })
                    
                    # Log the call
                    latency = (time.time() - start_time) * 1000
                    llm_logger.log_call(LLMCallLog(
                        call_id=f"behavior_{request.get('entity_id')}_{time.time()}",
                        timestamp=start_time,
                        context="behavior_generation",
                        entity_id=request.get('entity_id'),
                        prompt_summary=request.get('prompt_summary', '')[:200],
                        response_summary=str(result)[:200] if result else '',
                        latency_ms=latency,
                        tokens_used=0,
                        success=result is not None,
                        turn_number=current_turn,
                        call_type='behavior_generation',
                    ))
                    
                elif call_type == 'level_design':
                    # Level design call
                    result = dm_agent.design_level(
                        player_profile=request.get('player_profile'),
                        level_number=request.get('level_number', 1),
                        map_data=request.get('map_data'),
                    )
                    
                    response_queue.put({
                        'level_config': result,
                        'success': result is not None,
                    })
                    
                    latency = (time.time() - start_time) * 1000
                    llm_logger.log_call(LLMCallLog(
                        call_id=f"level_{time.time()}",
                        timestamp=start_time,
                        context="level_design",
                        entity_id=None,
                        prompt_summary=request.get('prompt_summary', '')[:200],
                        response_summary=str(result)[:200] if result else '',
                        latency_ms=latency,
                        tokens_used=0,
                        success=result is not None,
                        turn_number=current_turn,
                        call_type='level_design',
                    ))

                elif call_type == 'content_items':
                    result = dm_agent.generate_item_batch(
                        tags=request.get('tags', []),
                        count=request.get('count', 5),
                        player_summary=request.get('player_summary', 'Unknown'),
                    )
                    response_queue.put({
                        'content_type': 'items',
                        'data': result,
                        'success': result is not None,
                    })

                elif call_type == 'content_monsters':
                    result = dm_agent.generate_monster_batch(
                        tags=request.get('tags', []),
                        count=request.get('count', 4),
                        tier=request.get('tier', 3),
                        player_summary=request.get('player_summary', 'Unknown'),
                    )
                    response_queue.put({
                        'content_type': 'monsters',
                        'data': result,
                        'success': result is not None,
                    })

                elif call_type == 'evolved_roster':
                    # Evolved roster call
                    result = dm_agent.design_evolved_level(
                        context=request.get('evolution_context', {}),
                        level_number=request.get('depth', 1),
                    )
                    response_queue.put({
                        'content_type': 'evolved_roster',
                        'data': result,
                        'success': bool(result),
                    })

                elif call_type == 'behavior_with_context':
                    # Behavior with context call
                    # Convert perception dict to PerceptionStatus object if needed
                    perception_data = request.get('perception', {})
                    perception = (
                        PerceptionStatus.from_dict(perception_data)
                        if isinstance(perception_data, dict)
                        else perception_data
                    )
                    result = dm_agent.generate_behavior_script(
                        entity_id=request.get('entity_id', ''),
                        mob_type=request.get('mob_type', 'default'),
                        perception=perception,
                        social_context=f"original context\nDM Narrative: {request.get('dm_narrative_context', '')}",
                        valid_conditions=request.get('valid_conditions', []),
                        valid_actions=request.get('valid_actions', []),
                    )
                    response_queue.put({
                        'entity_id': request.get('entity_id'),
                        'behavior_script': result.to_dict() if result else None,
                        'success': result is not None,
                    })
                
                calls_this_turn += 1
                
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                response_queue.put({
                    'entity_id': request.get('entity_id'),
                    'error': str(e),
                    'success': False,
                })
                
                llm_logger.log_call(LLMCallLog(
                    call_id=f"error_{time.time()}",
                    timestamp=start_time,
                    context=call_type,
                    entity_id=request.get('entity_id'),
                    prompt_summary=request.get('prompt_summary', '')[:200],
                    response_summary='',
                    latency_ms=latency,
                    tokens_used=0,
                    success=False,
                    error=str(e),
                    turn_number=current_turn,
                    call_type=f'{call_type}_error',
                ))
            
            request_queue.task_done()
            
        except Empty:
            # No request available, continue loop
            continue
        except Exception as e:
            # Log unexpected errors but keep worker running
            print(f"LLM worker error: {e}")