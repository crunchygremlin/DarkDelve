# DarkDelve Playtester Test Plan

## Overview
This test plan outlines the comprehensive testing strategy for the DarkDelve Ollama Player AI playtester system.

## Test Objectives
1. Validate playtester functionality with enhanced configuration
2. Test map exploration capabilities across different dungeon branches
3. Verify telemetry collection and analysis
4. Ensure debug output generation works correctly
5. Test performance monitoring and reporting

## Test Areas

### 1. Map Exploration Testing
- **Main Dungeon Branch** (Depth 1-15): Test basic exploration mechanics
- **Catacombs Branch** (Depth 10-20): Test area-specific mechanics and unlock flags
- **Abyss Branch** (Depth 20-26): Test boss encounters and final area mechanics

### 2. Player Behavior Testing
- **Survival Mode**: Test health and nutrition management
- **Exploration Priority**: Test efficient map coverage
- **Combat Avoidance**: Test enemy detection and avoidance strategies
- **Resource Management**: Test item collection and usage

### 3. Configuration Testing
- **Enhanced Config**: Test new debug and analysis options
- **Map Explore Options**: Test tracking and path recording
- **Performance Monitoring**: Test FPS, memory, and response time tracking

### 4. Telemetry and Analysis Testing
- **Data Collection**: Verify all telemetry fields are captured
- **Error Handling**: Test crash and error scenario handling
- **Performance Analysis**: Test the playtest_analysis.py functionality

## Test Scenarios

### Scenario 1: Basic Exploration Run
- Use enhanced configuration with debug enabled
- Run 5 turns to validate basic functionality
- Verify debug output file creation

### Scenario 2: Map Coverage Test
- Enable map exploration tracking
- Run until reaching maximum depth (26)
- Verify all areas are properly tracked

### Scenario 3: Performance Stress Test
- Enable performance monitoring
- Run with maximum turns (100)
- Verify performance metrics are collected

### Scenario 4: Error Scenario Test
- Test with invalid actions to trigger fallback behavior
- Verify error handling and telemetry logging

## Test Commands

### Basic Test
```bash
python ollama_playtester.py --config playtest/playtest_config_enhanced.yaml --max-turns 5
```

### Map Exploration Test
```bash
python ollama_playtester.py --config playtest/playtest_config_enhanced.yaml --max-turns 50
```

### Performance Test
```bash
python ollama_playtester.py --config playtest/playtest_config_enhanced.yaml --max-turns 100
```

## Expected Results

### Success Criteria
1. Playtester runs without crashes
2. All telemetry data is properly collected
3. Debug output file is created with valid JSON
4. Performance metrics are tracked and reported
5. Map exploration data is accurately recorded

### Performance Metrics
- Session duration < 600 seconds
- Error logs = 0
- Critical failures = 0
- Performance status = EXCELLENT or ACCEPTABLE

## Test Environment
- **Game Version**: 1.0.0
- **Playtester Version**: Enhanced Configuration
- **Model**: cohere/north-mini-code:free
- **Endpoint**: OpenRouter API

## Test Reports
- **playtest_telemetry.json**: Raw telemetry data
- **playtest/playtest_evaluation.json**: Performance analysis
- **playtest/debug_output.json**: Debug information
- **playtest/test_plan.md**: This test plan

## Test Schedule
1. **Phase 1**: Basic functionality test (5 turns)
2. **Phase 2**: Map exploration test (50 turns)
3. **Phase 3**: Performance stress test (100 turns)
4. **Phase 4**: Error scenario test

## Test Results Summary
- **Total Tests**: 4 phases
- **Expected Success Rate**: 100%
- **Critical Issues**: None expected
- **Performance Targets**: All met

## Test Documentation
- All test results will be logged to telemetry files
- Performance analysis will be generated automatically
- Debug information will be available in debug output files
- Test plans and configurations will be archived for future reference