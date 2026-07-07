"""LLM worker thread for background processing of LLM requests."""

import time
import threading
from typing import Optional, Any, Dict
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


class LLMWorker:
    """Extended LLM worker for player stats evaluation."""

    def __init__(self, ollama_service=None, dm_agent=None):
        """Initialize the LLM worker.

        Args:
            ollama_service: Optional OllamaService instance
            dm_agent: Optional DungeonMasterAgent instance
        """
        self.ollama_service = ollama_service
        self.dm_agent = dm_agent

    def evaluate_player_stats(
        self,
        player_stats: Dict[str, int],
        current_level: int
    ) -> Dict[str, Any]:
        """
        Evaluate player stats using DM LLM and return difficulty adjustment recommendations.
        
        Args:
            player_stats: Dictionary of player stats (health, attack, defense, etc.)
            current_level: Current level the player is on
            
        Returns:
            Dictionary containing difficulty adjustment recommendations
        """
        # Construct prompt for DM LLM
        prompt = self._build_evaluation_prompt(player_stats, current_level)

        # Query LLM (no caching as per requirements)
        response = self._query_llm(prompt, use_cache=False)

        # Parse and return response
        return self._parse_evaluation_response(response)

    def _build_evaluation_prompt(
        self,
        player_stats: Dict[str, int],
        current_level: int
    ) -> str:
        """Build prompt for DM LLM to evaluate player stats."""
        return f"""
        As the Dungeon Master, evaluate the player's current stats and recommend 
        difficulty adjustments for the next level.
        
        Player Stats:
        - Health: {player_stats.get('health', 0)}
        - Attack: {player_stats.get('attack', 0)}
        - Defense: {player_stats.get('defense', 0)}
        - Power Level: {player_stats.get('power_level', 0)}
        - Current Level: {current_level}
        
        Provide your assessment in JSON format with the following structure:
        {{
            "difficulty_modifier": float,  // Overall difficulty multiplier (0.5 to 2.0)
            "specific_adjustments": {{
                "spawn_rate": float,       // Monster spawn rate multiplier (0.5 to 2.0)
                "monster_health": float,   // Monster health multiplier (0.5 to 2.0)
                "monster_damage": float    // Monster damage multiplier (0.5 to 2.0)
            }},
            "reasoning": "string"          // Brief explanation of your assessment
        }}
        
        Base your assessment on:
        - If player stats are significantly above average for their level, increase difficulty
        - If player stats are significantly below average for their level, decrease difficulty
        - If player stats are appropriate for their level, maintain current difficulty
        """

    def _query_llm(self, prompt: str, use_cache: bool = False) -> str:
        """Query the LLM with the given prompt."""
        # Implementation would call the actual LLM service
        # use_cache=False ensures no caching as per requirements
        if self.ollama_service:
            return self.ollama_service.generate(prompt)
        return ""

    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            import json
            # Find JSON object in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception:
            pass

        # Return default adjustment if parsing fails
        return {
            "difficulty_modifier": 1.0,
            "specific_adjustments": {
                "spawn_rate": 1.0,
                "monster_health": 1.0,
                "monster_damage": 1.0
            },
            "reasoning": "Failed to parse LLM response, using default difficulty"
        }