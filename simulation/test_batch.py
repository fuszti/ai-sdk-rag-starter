#!/usr/bin/env python3
"""
Test batch runner with minimal configuration
"""

import asyncio
import os
import sys
from batch_runner import BatchSimulationRunner

async def main():
    """Test batch runner with minimal config."""
    openai_api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    assistant_api_url = os.getenv('ASSISTANT_API_URL', 'http://localhost:3000/api/chat')

    # Minimal test configuration
    personas = ['vague_communicator']
    goals = ['specific_memory_recall']
    runs_per_combination = 1
    max_turns = 2

    runner = BatchSimulationRunner(
        openai_api_key=openai_api_key,
        personas=personas,
        goals=goals,
        runs_per_combination=runs_per_combination,
        api_endpoint=assistant_api_url,
        max_turns=max_turns
    )

    try:
        results = await runner.run_batch()
        print(f"\n\nBatch completed. Results collected: {len(runner.results)}")
        print(f"All results in aggregation: {results['all_results']}")
    except Exception as e:
        print(f"Batch simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())