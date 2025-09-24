#!/usr/bin/env python3
"""
Isolated Batch Runner that runs each simulation in a separate Docker environment
to ensure memory isolation between evaluation runs.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from colorama import init, Fore, Style

from src.isolated_simulation_runner import IsolatedSimulationRunner
from src.personas import PREDEFINED_PERSONAS
from src.goals import PREDEFINED_GOALS
from src.types import SimulationConfig, SimulationResult

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


class IsolatedBatchSimulationRunner:
    def __init__(
        self,
        openai_api_key: str,
        personas: List[str],
        goals: List[str],
        runs_per_combination: int,
        max_turns: int
    ):
        self.openai_api_key = openai_api_key
        self.personas = personas
        self.goals = goals
        self.runs_per_combination = runs_per_combination
        self.max_turns = max_turns
        self.results: List[SimulationResult] = []
        self.isolated_runner = IsolatedSimulationRunner(openai_api_key)

    async def run_batch(self) -> Dict[str, Any]:
        """Run batch simulations with isolated environments."""
        print(f"{Fore.CYAN}{Style.BRIGHT}\\n🔄 Starting Isolated Batch Simulation{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Personas: {', '.join(self.personas)}")
        print(f"{Fore.WHITE}Goals: {', '.join(self.goals)}")
        print(f"{Fore.WHITE}Runs per combination: {self.runs_per_combination}")

        total_runs = len(self.personas) * len(self.goals) * self.runs_per_combination
        print(f"{Fore.WHITE}Total simulations: {total_runs}\\n")

        success_count = 0
        fail_count = 0
        run_number = 0

        for persona_id in self.personas:
            for goal_id in self.goals:
                for run in range(self.runs_per_combination):
                    run_number += 1
                    run_id = f"batch-{persona_id}-{goal_id}-{run + 1}-{int(time.time() * 1000)}"

                    print(f"{Fore.CYAN}\\n[{run_number}/{total_runs}] Running: {persona_id} + {goal_id} (Run {run + 1})")
                    print(f"{Fore.YELLOW}🔄 Environment ID: {run_id}")

                    persona = PREDEFINED_PERSONAS.get(persona_id)
                    goal = PREDEFINED_GOALS.get(goal_id)

                    if not persona or not goal:
                        print(f"{Fore.RED}❌ Invalid persona or goal")
                        fail_count += 1
                        continue

                    config = SimulationConfig(
                        persona=persona,
                        goal=goal,
                        max_turns=self.max_turns,
                        api_endpoint="",  # Will be set by isolated runner
                        simulation_id=run_id,
                    )

                    try:
                        print(f"{Fore.CYAN}🚀 Starting isolated environment...")
                        result = await self.isolated_runner.run_simulation(config, run_id)

                        print(f"{Fore.GREEN}✅ Simulation completed, adding to results")
                        self.results.append(result)
                        success_count += 1
                        print(f"{Fore.CYAN}Current results count: {len(self.results)}")

                        # Small delay between simulations to avoid port conflicts
                        print(f"{Fore.YELLOW}⏳ Waiting before next simulation...")
                        await asyncio.sleep(5)

                    except Exception as e:
                        print(f"{Fore.RED}❌ Simulation failed with exception: {e}")
                        import traceback
                        traceback.print_exc()
                        fail_count += 1

        print(f"{Fore.CYAN}Analyzing batch results. Results collected: {len(self.results)}")
        batch_results = self._analyze_batch_results(success_count, fail_count)
        await self._save_batch_results(batch_results)

        return batch_results

    def _analyze_batch_results(self, success_count: int, fail_count: int) -> Dict[str, Any]:
        """Analyze batch simulation results."""
        timestamp = datetime.now().isoformat()

        average_metrics = self._calculate_average_metrics()
        results_by_persona = self._group_results_by_persona()
        results_by_goal = self._group_results_by_goal()

        return {
            'timestamp': timestamp,
            'total_runs': success_count + fail_count,
            'successful_runs': success_count,
            'failed_runs': fail_count,
            'average_metrics': average_metrics,
            'results_by_persona': results_by_persona,
            'results_by_goal': results_by_goal,
            'all_results': [r.model_dump(mode='json') for r in self.results],
        }

    def _calculate_average_metrics(self) -> Dict[str, float]:
        """Calculate average metrics across all simulations."""
        if not self.results:
            return {
                'overall_score': 0,
                'goal_achievement_rate': 0,
                'user_satisfaction': 0,
                'clarity_score': 0,
                'relevance_score': 0,
                'completeness_score': 0,
                'average_turns': 0,
                'average_response_time': 0,
            }

        metrics_sum = {
            'goal_achieved': 0,
            'user_satisfaction': 0,
            'clarity': 0,
            'relevance': 0,
            'completeness': 0,
            'turns': 0,
            'response_time': 0,
        }

        for result in self.results:
            metrics = result.metrics
            metrics_sum['goal_achieved'] += 1 if metrics.goal_achieved else 0
            metrics_sum['user_satisfaction'] += metrics.user_satisfaction_score
            metrics_sum['clarity'] += metrics.clarity_score
            metrics_sum['relevance'] += metrics.relevance_score
            metrics_sum['completeness'] += metrics.completeness_score
            metrics_sum['turns'] += metrics.total_turns
            metrics_sum['response_time'] += metrics.average_response_time

        count = len(self.results)
        averages = {
            'goal_achievement_rate': metrics_sum['goal_achieved'] / count,
            'user_satisfaction': metrics_sum['user_satisfaction'] / count,
            'clarity_score': metrics_sum['clarity'] / count,
            'relevance_score': metrics_sum['relevance'] / count,
            'completeness_score': metrics_sum['completeness'] / count,
            'average_turns': metrics_sum['turns'] / count,
            'average_response_time': metrics_sum['response_time'] / count,
        }

        overall_score = (
            averages['goal_achievement_rate'] * 0.25 +
            averages['user_satisfaction'] * 0.20 +
            averages['clarity_score'] * 0.15 +
            averages['relevance_score'] * 0.20 +
            averages['completeness_score'] * 0.20
        )

        return {
            'overall_score': overall_score,
            **averages
        }

    def _group_results_by_persona(self) -> Dict[str, Any]:
        """Group results by persona."""
        grouped = {}

        for result in self.results:
            persona_id = result.config.persona.id
            if persona_id not in grouped:
                grouped[persona_id] = {
                    'runs': 0,
                    'goal_achieved': 0,
                    'avg_satisfaction': 0,
                    'avg_clarity': 0,
                    'avg_relevance': 0,
                    'avg_completeness': 0,
                }

            grouped[persona_id]['runs'] += 1
            grouped[persona_id]['goal_achieved'] += 1 if result.metrics.goal_achieved else 0
            grouped[persona_id]['avg_satisfaction'] += result.metrics.user_satisfaction_score
            grouped[persona_id]['avg_clarity'] += result.metrics.clarity_score
            grouped[persona_id]['avg_relevance'] += result.metrics.relevance_score
            grouped[persona_id]['avg_completeness'] += result.metrics.completeness_score

        # Calculate averages
        for persona_id, data in grouped.items():
            runs = data['runs']
            grouped[persona_id] = {
                'runs': runs,
                'goal_achievement_rate': data['goal_achieved'] / runs,
                'avg_satisfaction': data['avg_satisfaction'] / runs,
                'avg_clarity': data['avg_clarity'] / runs,
                'avg_relevance': data['avg_relevance'] / runs,
                'avg_completeness': data['avg_completeness'] / runs,
            }

        return grouped

    def _group_results_by_goal(self) -> Dict[str, Any]:
        """Group results by goal."""
        grouped = {}

        for result in self.results:
            goal_id = result.config.goal.id
            if goal_id not in grouped:
                grouped[goal_id] = {
                    'runs': 0,
                    'achieved': 0,
                    'avg_turns': 0,
                    'avg_satisfaction': 0,
                }

            grouped[goal_id]['runs'] += 1
            grouped[goal_id]['achieved'] += 1 if result.metrics.goal_achieved else 0
            grouped[goal_id]['avg_turns'] += result.metrics.total_turns
            grouped[goal_id]['avg_satisfaction'] += result.metrics.user_satisfaction_score

        # Calculate averages
        for goal_id, data in grouped.items():
            runs = data['runs']
            grouped[goal_id] = {
                'runs': runs,
                'achievement_rate': data['achieved'] / runs,
                'avg_turns': data['avg_turns'] / runs,
                'avg_satisfaction': data['avg_satisfaction'] / runs,
            }

        return grouped

    async def _save_batch_results(self, results: Dict[str, Any]):
        """Save batch results to a JSON file."""
        timestamp = datetime.now().isoformat().replace(':', '-')
        filename = f"isolated-batch-results-{timestamp}.json"
        filepath = Path("simulation/results") / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"{Fore.GREEN}\\n✅ Isolated batch results saved to: {filepath}")

        self._print_batch_summary(results)

    def _print_batch_summary(self, results: Dict[str, Any]):
        """Print batch simulation summary."""
        print(f"{Fore.CYAN}{Style.BRIGHT}\\n📊 ISOLATED BATCH SIMULATION SUMMARY{Style.RESET_ALL}")
        print("=" * 60)

        print(f"{Fore.WHITE}\\nOverall Results:")
        print(f"  Total Runs: {results['total_runs']}")
        print(f"  Successful: {results['successful_runs']}")
        print(f"  Failed: {results['failed_runs']}")

        metrics = results['average_metrics']
        print(f"{Fore.WHITE}\\nAverage Metrics:")
        print(f"  Overall Score: {metrics['overall_score'] * 100:.1f}%")
        print(f"  Goal Achievement Rate: {metrics['goal_achievement_rate'] * 100:.1f}%")
        print(f"  User Satisfaction: {metrics['user_satisfaction'] * 100:.1f}%")
        print(f"  Clarity Score: {metrics['clarity_score'] * 100:.1f}%")
        print(f"  Relevance Score: {metrics['relevance_score'] * 100:.1f}%")
        print(f"  Completeness Score: {metrics['completeness_score'] * 100:.1f}%")
        print(f"  Average Turns: {metrics['average_turns']:.1f}")
        print(f"  Average Response Time: {metrics['average_response_time'] / 1000:.2f}s")

        print(f"{Fore.WHITE}\\nResults by Persona:")
        for persona_id, data in results['results_by_persona'].items():
            print(f"  {persona_id}:")
            print(f"    Goal Achievement: {data['goal_achievement_rate'] * 100:.1f}%")
            print(f"    Satisfaction: {data['avg_satisfaction'] * 100:.1f}%")

        print(f"{Fore.WHITE}\\nResults by Goal:")
        for goal_id, data in results['results_by_goal'].items():
            print(f"  {goal_id}:")
            print(f"    Achievement Rate: {data['achievement_rate'] * 100:.1f}%")
            print(f"    Avg Turns: {data['avg_turns']:.1f}")

        print(f"{Fore.GREEN}\\n🎉 Each simulation ran with isolated memory!")
        print(f"{Fore.GREEN}   No memory contamination between runs.")


async def main():
    """Main function to run isolated batch simulations."""
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not openai_api_key:
        print(f"{Fore.RED}❌ OPENAI_API_KEY not found in environment variables")
        sys.exit(1)

    # Batch configuration - small test set
    personas = ['vague_communicator', 'clarification_cooperative']
    goals = ['specific_memory_recall', 'vague_memory_recall']
    runs_per_combination = 1
    max_turns = 8

    runner = IsolatedBatchSimulationRunner(
        openai_api_key=openai_api_key,
        personas=personas,
        goals=goals,
        runs_per_combination=runs_per_combination,
        max_turns=max_turns
    )

    try:
        await runner.run_batch()
    except Exception as e:
        print(f"{Fore.RED}Isolated batch simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())