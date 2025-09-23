import json
from datetime import datetime
from pathlib import Path
from typing import List
from colorama import init, Fore, Style

from src.user_simulator import UserSimulator
from src.assistant_client import AssistantClient, AssistantClientConfig
from src.evaluator import ConversationEvaluator
from src.types import SimulationConfig, SimulationResult

# Initialize colorama for colored output
init(autoreset=True)


class SimulationRunner:
    def __init__(self, config: SimulationConfig, openai_api_key: str):
        self.config = config
        self.user_simulator = UserSimulator(openai_api_key, config.persona, config.goal)
        self.assistant_client = AssistantClient(
            AssistantClientConfig(api_endpoint=config.api_endpoint)
        )
        self.evaluator = ConversationEvaluator(openai_api_key)
        self.response_times: List[float] = []
        self.errors: List[str] = []

    def run(self) -> SimulationResult:
        """Run the simulation."""
        print(f"{Fore.CYAN}\nStarting Simulation")
        print(f"{Fore.WHITE}Persona: {self.config.persona.name}")
        print(f"{Fore.WHITE}Goal: {self.config.goal.description}")
        print(f"{Fore.WHITE}Max Turns: {self.config.max_turns}\n")

        start_time = datetime.now()

        try:
            self._run_conversation()
        except Exception as e:
            print(f"{Fore.RED}Simulation error: {e}")
            self.errors.append(str(e))

        end_time = datetime.now()
        conversation = self.user_simulator.get_state()

        print(f"{Fore.CYAN}\nEvaluating Conversation...")
        metrics = self.evaluator.evaluate(
            conversation,
            self.config.goal,
            self.config.persona,
            self.response_times,
            self.errors
        )

        duration = (end_time - start_time).total_seconds() * 1000  # Convert to ms

        result = SimulationResult(
            config=self.config,
            conversation=conversation,
            metrics=metrics,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            errors=self.errors if self.errors else None,
        )

        self._save_results(result)
        self._print_report(result)

        return result

    def _run_conversation(self):
        """Run the conversation between user and assistant."""
        # Generate initial message
        initial_message = self.user_simulator.generate_initial_message()
        self.user_simulator.add_user_message(initial_message)

        print(f"{Fore.BLUE}USER: {initial_message}")

        turn_count = 0
        should_continue = True

        while (
            should_continue
            and turn_count < self.config.max_turns
            and not self.user_simulator.should_stop()
        ):
            state = self.user_simulator.get_state()

            # Get assistant response
            response, response_time, error = self.assistant_client.send_message(
                state.messages[-1].content,
                state.messages[:-1]
            )

            if error:
                print(f"{Fore.RED}ERROR: {error}")
                self.errors.append(error)
                break

            self.response_times.append(response_time)
            print(f"{Fore.GREEN}ASSISTANT: {response}")

            # Add assistant message to conversation history
            self.user_simulator.add_assistant_message(response)

            # Generate user response
            user_message, should_continue, satisfaction = self.user_simulator.generate_response(
                response
            )

            if user_message:
                self.user_simulator.add_user_message(user_message)
                print(f"{Fore.BLUE}USER: {user_message}")

            self.user_simulator.update_satisfaction(satisfaction)

            if not should_continue:
                print(f"{Fore.YELLOW}\nUser ended conversation")

            turn_count += 1

        if turn_count >= self.config.max_turns:
            print(f"{Fore.YELLOW}\nMaximum turns reached")

    def _save_results(self, result: SimulationResult):
        """Save simulation results to a JSON file."""
        timestamp = datetime.now().isoformat().replace(':', '-')
        filename = f"simulation-{self.config.simulation_id}-{timestamp}.json"
        filepath = Path("simulation/results") / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dict for JSON serialization
        result_dict = result.model_dump(mode='json')

        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2)

        print(f"{Fore.WHITE}\nResults saved to: {filepath}")

    def _print_report(self, result: SimulationResult):
        """Print the evaluation report."""
        report = self.evaluator.generate_report(result.metrics)
        print(report)

        if result.errors:
            print(f"{Fore.RED}\n⚠️ Errors encountered:")
            for error in result.errors:
                print(f"{Fore.RED}  - {error}")