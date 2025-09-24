#!/usr/bin/env python3
"""
Test script for the isolated evaluation system.
"""

import asyncio
import os
import sys
from src.isolated_simulation_runner import IsolatedSimulationRunner
from src.personas import PREDEFINED_PERSONAS
from src.goals import PREDEFINED_GOALS
from src.types import SimulationConfig

async def test_isolated_environment():
    """Test that isolated environments work correctly."""

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    print("🧪 Testing Isolated Evaluation System")
    print("=" * 50)

    try:
        # Test with a simple configuration
        persona = PREDEFINED_PERSONAS['vague_communicator']
        goal = PREDEFINED_GOALS['specific_memory_recall']

        config = SimulationConfig(
            persona=persona,
            goal=goal,
            max_turns=3,  # Short test
            api_endpoint="",  # Will be set by isolated runner
            simulation_id="test-isolated"
        )

        runner = IsolatedSimulationRunner(openai_api_key)

        print("🚀 Starting isolated simulation...")
        result = await runner.run_simulation(config, "test-run")

        print("✅ Test completed successfully!")
        print(f"   Goal achieved: {result.metrics.goal_achieved}")
        print(f"   Total turns: {result.metrics.total_turns}")
        print(f"   Errors: {result.errors}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_isolated_environment())
    sys.exit(0 if success else 1)