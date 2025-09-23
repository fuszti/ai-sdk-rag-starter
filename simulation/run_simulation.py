#!/usr/bin/env python3
"""
Run a single simulation with specified persona and goal.
Usage: python run_simulation.py [persona] [goal]
"""

import os
import sys
import time
from dotenv import load_dotenv
from colorama import init, Fore, Style

from src.simulation_runner import SimulationRunner
from src.personas import PREDEFINED_PERSONAS
from src.goals import PREDEFINED_GOALS
from src.types import SimulationConfig

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


def main():
    """Main function to run a single simulation."""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    assistant_api_url = os.getenv('ASSISTANT_API_URL', 'http://localhost:3000/api/chat')

    if not openai_api_key:
        print(f"{Fore.RED}❌ OPENAI_API_KEY not found in environment variables")
        sys.exit(1)

    # Get persona and goal from command line args
    args = sys.argv[1:]
    persona_id = args[0] if len(args) > 0 else 'average_user'
    goal_id = args[1] if len(args) > 1 else 'learn_basic_concept'

    # Get persona and goal
    persona = PREDEFINED_PERSONAS.get(persona_id)
    goal = PREDEFINED_GOALS.get(goal_id)

    if not persona:
        print(f"{Fore.RED}❌ Unknown persona: {persona_id}")
        print(f"Available personas: {', '.join(PREDEFINED_PERSONAS.keys())}")
        sys.exit(1)

    if not goal:
        print(f"{Fore.RED}❌ Unknown goal: {goal_id}")
        print(f"Available goals: {', '.join(PREDEFINED_GOALS.keys())}")
        sys.exit(1)

    # Create simulation config
    config = SimulationConfig(
        persona=persona,
        goal=goal,
        max_turns=20,
        api_endpoint=assistant_api_url,
        simulation_id=f"{persona_id}-{goal_id}-{int(time.time() * 1000)}",
    )

    print(f"{Fore.CYAN}{Style.BRIGHT}\nAI Assistant Multi-Turn Evaluation System")
    print("=" * 50)

    # Run the simulation
    runner = SimulationRunner(config, openai_api_key)

    try:
        runner.run()
        print(f"{Fore.GREEN}\nSimulation completed successfully")
    except Exception as e:
        print(f"{Fore.RED}\nSimulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()