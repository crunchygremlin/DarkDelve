#!/usr/bin/env python3
import json
import datetime
import sys

# Read the telemetry file
with open('playtest/playtest_telemetry.json', 'r') as f:
    data = json.load(f)

print(f'Total entries: {len(data)}')

# Extract key metrics
session_duration = 0
error_logs = 0
issues = 0
fps_min = None
player_frustration_score = None

# Track timestamps for duration calculation
timestamps = []

for entry in data:
    # Collect timestamps for duration calculation
    if 'timestamp' in entry:
        timestamps.append(entry['timestamp'])
    
    # Count error logs and issues
    if 'error_message' in entry:
        error_logs += 1
    
    if 'issues' in entry:
        issues += len(entry['issues'])
    
    # Check for fps_min and player_frustration_score (if they exist)
    if 'fps_min' in entry:
        fps_min = entry['fps_min']
    
    if 'player_frustration_score' in entry:
        player_frustration_score = entry['player_frustration_score']

# Calculate session duration if we have timestamps
if timestamps:
    # Parse timestamps to datetime objects
    dt_objects = [datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
    duration = max(dt_objects) - min(dt_objects)
    session_duration = int(duration.total_seconds())

print(f'Session duration: {session_duration} seconds')
print(f'Error logs: {error_logs}')
print(f'Issues: {issues}')
print(f'FPS min: {fps_min}')
print(f'Player frustration score: {player_frustration_score}')

# Check for critical failures
critical_failures_found = False
failed_assertions = []

# Check for critical bugs (crashes, errors)
for entry in data:
    if entry.get('event_type') in ['crash', 'error']:
        critical_failures_found = True
        failed_assertions.append(f'Critical bug: {entry.get("error_message", "Unknown error")}')
    
    # Check for game breaking metrics
    if 'stats' in entry:
        stats = entry['stats']
        if stats.get('turn', 0) > 600:  # Player completion time > 600 seconds
            critical_failures_found = True
            failed_assertions.append(f'Game breaking metric: Player completion time > 600 seconds (turn {stats.get("turn")})')
        
        if stats.get('hp', 100) >= 100:  # Player health never dropping below 100%
            critical_failures_found = True
            failed_assertions.append(f'Game breaking metric: Player health never dropping below 100% (hp {stats.get("hp")})')

# Check for soft lock
input_count = 0
for entry in data:
    if 'history' in entry:
        for action_entry in entry['history']:
            if action_entry.get('action') == 's':
                input_count += 1

if input_count > 5000:
    critical_failures_found = True
    failed_assertions.append(f'Soft lock: Input count > 5000 with zero progress (input count: {input_count})')

print(f'Critical failures found: {critical_failures_found}')
print(f'Failed assertions: {failed_assertions}')

# Determine performance status
if not critical_failures_found and session_duration <= 600 and error_logs == 0:
    performance_status = 'EXCELLENT'
elif not critical_failures_found and session_duration <= 600:
    performance_status = 'ACCEPTABLE'
else:
    performance_status = 'UNACCEPTABLE'

print(f'Performance status: {performance_status}')

# Generate final JSON
result = {
    'session_id': 'playtest_session_001',
    'evaluation': {
        'passed': not critical_failures_found,
        'critical_failures_found': critical_failures_found,
        'performance_status': performance_status
    },
    'metrics_summary': {
        'final_duration_seconds': session_duration,
        'bug_count': error_logs + issues
    },
    'failed_assertions': failed_assertions
}

print('\nFinal JSON:')
print(json.dumps(result, indent=2))

# Write to file for reference
with open('playtest/playtest_evaluation.json', 'w') as f:
    json.dump(result, f, indent=2)

print('\nResults written to playtest/playtest_evaluation.json')