#!/usr/bin/env python3
"""
Playtest runner - executes the in-process MCP playtester.
Usage: python playtest/run_playtest.py [--levels N] [--turns N] [--difficulty DIFF] [--hideui]
"""

import sys
import os
import argparse
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.services.mcp_integration import MCPPlaytester


def main():
    parser = argparse.ArgumentParser(description="Run DarkDelve in-process playtest")
    parser.add_argument("--levels", type=int, default=5, help="Max levels to play (unused, for CLI compat)")
    parser.add_argument("--turns", type=int, default=500, help="Max turns")
    parser.add_argument("--difficulty", default="normal", help="Difficulty mode (unused, for CLI compat)")
    parser.add_argument("--output", default="playtest/telemetry", help="Output directory")
    parser.add_argument("--config", default="playtest/playtest_config.yaml", help="Playtest config YAML path")
    parser.add_argument("--hideui", action="store_true", help="Hide UI/map rendering (for faster AI testing)")
    args = parser.parse_args()

    print(f"Starting DarkDelve in-process playtest: max {args.turns} turns")
    if args.hideui:
        print("UI hidden - faster AI testing mode")

    tester = MCPPlaytester(config_path=args.config, render_to_stdout=not args.hideui)
    result = tester.run()

    print(f"\nPlaytest completed: status={result.status}, turns={result.turns}")
    if result.error_message:
        print(f"Error: {result.error_message}")

    # Print the full result as JSON
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))

    return 0 if result.status in ("max_turns", "exit") else 1


if __name__ == "__main__":
    sys.exit(main())
