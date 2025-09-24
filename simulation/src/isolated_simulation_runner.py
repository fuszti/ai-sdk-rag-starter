#!/usr/bin/env python3
"""
Isolated Simulation Runner that manages separate Docker environments for each evaluation run.
"""

import asyncio
import json
import os
import subprocess
import time
import requests
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from colorama import init, Fore, Style

from src.simulation_runner import SimulationRunner
from src.types import SimulationConfig, SimulationResult

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


def find_free_port(start_port: int = 3001, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise Exception(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


def find_free_ports(count: int, start_port: int = 3001) -> List[int]:
    """Find multiple free ports."""
    ports = []
    current_port = start_port

    for _ in range(count):
        port = find_free_port(current_port)
        ports.append(port)
        current_port = port + 1

    return ports


class IsolatedSimulationEnvironment:
    """Manages an isolated Docker environment for a single simulation run."""

    def __init__(self, run_id: str, app_port: int = None, db_port: int = None):
        self.run_id = run_id

        # Find free ports if not provided
        if app_port is None or db_port is None:
            free_ports = find_free_ports(2, 3001)
            self.app_port = app_port or free_ports[0]
            self.db_port = db_port or free_ports[1]
        else:
            self.app_port = app_port
            self.db_port = db_port
        self.env_vars = {
            'EVAL_RUN_ID': run_id,
            'EVAL_APP_PORT': str(self.app_port),
            'EVAL_DB_PORT': str(self.db_port),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        }

        print(f"{Fore.CYAN}🔌 Assigned ports: App={self.app_port}, DB={self.db_port}")
        self.api_endpoint = f"http://localhost:{self.app_port}/api/chat"
        self.seed_endpoint = f"http://localhost:{self.app_port}/api/eval/seed"

    async def start(self) -> bool:
        """Start the isolated environment."""
        print(f"{Fore.CYAN}🚀 Starting isolated environment: {self.run_id}")

        try:
            # Start docker compose with unique services
            cmd = [
                'docker', 'compose',
                '-f', 'docker-compose.eval.yml',
                '-p', f'eval-{self.run_id}',  # Unique project name
                'up', '-d'
            ]

            # Set environment variables for docker-compose
            env = os.environ.copy()
            env.update(self.env_vars)

            print(f"{Fore.CYAN}🔧 Running command: {' '.join(cmd)}")
            print(f"{Fore.CYAN}🔧 Working directory: {os.path.abspath('../..')}")

            process = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                cwd='..'  # Run from project root where docker-compose.eval.yml is
            )

            if process.returncode != 0:
                print(f"{Fore.RED}❌ Failed to start environment:")
                print(f"{Fore.RED}   stdout: {process.stdout}")
                print(f"{Fore.RED}   stderr: {process.stderr}")
                print(f"{Fore.RED}   return code: {process.returncode}")
                return False

            print(f"{Fore.GREEN}✅ Environment started")

            # Wait for services to be ready
            await self._wait_for_services()

            # Seed the database with test data
            await self._seed_database()

            return True

        except Exception as e:
            print(f"{Fore.RED}❌ Error starting environment: {e}")
            return False

    async def stop(self):
        """Stop and clean up the isolated environment."""
        print(f"{Fore.YELLOW}🛑 Stopping isolated environment: {self.run_id}")

        try:
            # Stop docker compose services
            cmd = [
                'docker', 'compose',
                '-f', 'docker-compose.eval.yml',
                '-p', f'eval-{self.run_id}',
                'down', '-v'  # Remove volumes too
            ]

            env = os.environ.copy()
            env.update(self.env_vars)

            process = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                cwd='..'  # Run from project root where docker-compose.eval.yml is
            )

            if process.returncode != 0:
                print(f"{Fore.RED}⚠️ Warning stopping environment: {process.stderr}")
            else:
                print(f"{Fore.GREEN}✅ Environment stopped and cleaned up")

        except Exception as e:
            print(f"{Fore.RED}❌ Error stopping environment: {e}")

    async def _wait_for_services(self, max_retries: int = 30, retry_delay: float = 2.0):
        """Wait for services to become available."""
        print(f"{Fore.CYAN}⏳ Waiting for services to be ready...")

        for attempt in range(max_retries):
            try:
                # Check if app is responding
                response = requests.get(f"http://localhost:{self.app_port}", timeout=5)
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✅ Services are ready!")
                    return

            except requests.exceptions.RequestException:
                pass

            print(f"{Fore.YELLOW}⏳ Attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)

        raise Exception(f"Services did not become ready after {max_retries} attempts")

    async def _seed_database(self):
        """Seed the database with pre-defined test data."""
        print(f"{Fore.CYAN}🌱 Seeding database with test memories...")

        try:
            response = requests.post(self.seed_endpoint, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"{Fore.GREEN}✅ Database seeded successfully")
                else:
                    print(f"{Fore.RED}❌ Seeding failed: {result.get('error')}")
                    raise Exception(f"Seeding failed: {result.get('error')}")
            else:
                print(f"{Fore.RED}❌ Seeding request failed: {response.status_code}")
                raise Exception(f"Seeding request failed with status {response.status_code}")

        except Exception as e:
            print(f"{Fore.RED}❌ Error seeding database: {e}")
            raise


class IsolatedSimulationRunner:
    """Runs simulations in isolated environments."""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key

    async def run_simulation(
        self,
        config: SimulationConfig,
        run_id: Optional[str] = None
    ) -> SimulationResult:
        """Run a single simulation in an isolated environment."""

        if run_id is None:
            run_id = f"sim-{int(time.time() * 1000)}"

        # Create environment with dynamic port assignment
        environment = IsolatedSimulationEnvironment(run_id)

        try:
            # Start isolated environment
            if not await environment.start():
                raise Exception("Failed to start isolated environment")

            # Update config to use the isolated endpoint
            isolated_config = SimulationConfig(
                persona=config.persona,
                goal=config.goal,
                max_turns=config.max_turns,
                api_endpoint=environment.api_endpoint,
                simulation_id=f"isolated-{config.simulation_id}",
                seed=config.seed
            )

            # Run the simulation
            runner = SimulationRunner(isolated_config, self.openai_api_key)
            result = runner.run()

            return result

        finally:
            # Always clean up the environment
            await environment.stop()


async def main():
    """Test the isolated simulation runner."""
    from src.personas import PREDEFINED_PERSONAS
    from src.goals import PREDEFINED_GOALS

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print(f"{Fore.RED}❌ OPENAI_API_KEY not found")
        return

    # Test configuration
    persona = PREDEFINED_PERSONAS['vague_communicator']
    goal = PREDEFINED_GOALS['specific_memory_recall']

    config = SimulationConfig(
        persona=persona,
        goal=goal,
        max_turns=5,
        api_endpoint="",  # Will be set by isolated runner
        simulation_id=f"test-{int(time.time() * 1000)}"
    )

    runner = IsolatedSimulationRunner(openai_api_key)

    try:
        result = await runner.run_simulation(config)
        print(f"\n{Fore.GREEN}✅ Simulation completed successfully!")
        print(f"Goal achieved: {result.metrics.goal_achieved}")
        print(f"Satisfaction: {result.metrics.user_satisfaction_score}")

    except Exception as e:
        print(f"\n{Fore.RED}❌ Simulation failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())