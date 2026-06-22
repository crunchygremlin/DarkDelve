#!/usr/bin/env python3
"""
Playtest runner - executes the multi-level playtester.
Usage: python playtest/run_playtest.py [--levels N] [--turns N] [--difficulty DIFF]
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playtest.multi_level_playtester import MultiLevelPlaytester
from playtest.playtest_analyzer import PlaytestAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Run DarkDelve multi-level playtest")
    parser.add_argument("--levels", type=int, default=5, help="Max levels to play")
    parser.add_argument("--turns", type=int, default=500, help="Max turns")
    parser.add_argument("--difficulty", default="normal", help="Difficulty mode")
    parser.add_argument("--output", default="playtest/telemetry", help="Output directory")
    args = parser.parse_args()
    
    print(f"Starting DarkDelve playtest: {args.levels} levels, {args.difficulty} difficulty")
    
    tester = MultiLevelPlaytester()
    session = tester.run_session(max_levels=args.levels, max_turns=args.turns)
    
    tester.print_summary(session)
    tester.save_telemetry(args.output)
    
    # Run analysis
    analyzer = PlaytestAnalyzer(session)
    report = analyzer.generate_full_report()
    print("\n" + report)
    analyzer.save_report(os.path.join(args.output, f"report_{session.session_id}.txt"))
    
    return 0 if session.final_status in ("won", "max_levels") else 1

if __name__ == "__main__":
    sys.exit(main())