from typing import Dict, Tuple
from datetime import datetime
from openai import OpenAI
from src.types import (
    UserPersona,
    ConversationGoal,
    ConversationState,
    Message,
)


class UserSimulator:
    def __init__(self, openai_api_key: str, persona: UserPersona, goal: ConversationGoal):
        self.client = OpenAI(api_key=openai_api_key)
        self.persona = persona
        self.goal = goal
        self.state = ConversationState(
            messages=[],
            current_turn=0,
            goal_progress=0.0,
            user_satisfaction=0.5,
            frustration_level=0.0,
            context={},
        )

    def generate_initial_message(self) -> str:
        """Generate the first message to start a conversation."""
        system_prompt = self._build_system_prompt()
        user_prompt = f"""Generate the first message to start a conversation about: "{self.goal.description}".

        Remember your persona traits:
        - Patience level: {self.persona.patience}
        - Expertise: {self.persona.expertise}
        - Communication clarity: {self.persona.clarity_of_communication}

        Make the message natural and consistent with these traits."""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=300,
        )

        return response.choices[0].message.content or ''

    def generate_response(self, assistant_message: str) -> Tuple[str, bool, float]:
        """
        Generate a response to the assistant's message.
        Returns: (message, should_continue, satisfaction)
        """
        self._update_state(assistant_message)

        system_prompt = self._build_system_prompt()
        conversation_context = self._build_conversation_context()

        user_prompt = f"""Based on the assistant's last response, generate your next message.

        Current conversation state:
        - Turn number: {self.state.current_turn}
        - Goal progress: {self.state.goal_progress * 100:.0f}%
        - Your frustration level: {self.state.frustration_level * 100:.0f}%
        - Your satisfaction: {self.state.user_satisfaction * 100:.0f}%

        Success criteria for your goal:
        {chr(10).join(f'- {c}' for c in self.goal.success_criteria)}

        Recent conversation:
        {conversation_context}

        Generate your response based on:
        1. Your persona traits (patience: {self.persona.patience}, expertise: {self.persona.expertise})
        2. Whether the assistant is helping you achieve your goal
        3. Your current frustration and satisfaction levels

        YOU MUST format your response EXACTLY like this:
        MESSAGE: [your message]
        CONTINUE: [true/false]
        SATISFACTION: [0-1]
        REASON: [brief reason]

        Example:
        MESSAGE: Could you try explaining it in a different way?
        CONTINUE: true
        SATISFACTION: 0.3
        REASON: Assistant didn't provide helpful information

        IMPORTANT: Always include all four fields (MESSAGE, CONTINUE, SATISFACTION, REASON) in your response."""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=500,
        )

        content = response.choices[0].message.content or ''
        return self._parse_simulated_response(content)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the simulated user."""
        return f"""You are simulating a user with the following characteristics:

        Persona: {self.persona.name}
        Description: {self.persona.description}

        Personality Traits (0-1 scale):
        - Patience: {self.persona.patience} ({self._get_trait_description('patience', self.persona.patience)})
        - Expertise: {self.persona.expertise} ({self._get_trait_description('expertise', self.persona.expertise)})
        - Verbosity: {self.persona.verbosity} ({self._get_trait_description('verbosity', self.persona.verbosity)})
        - Frustration Tolerance: {self.persona.frustration_tolerance}
        - Communication Clarity: {self.persona.clarity_of_communication}
        - Technical Level: {self.persona.technical_level}

        Your Goal: {self.goal.description}
        Expected conversation length: {self.goal.expected_turns} turns
        Domain: {self.goal.domain}
        Complexity: {self.goal.complexity}

        Behave consistently with these traits throughout the conversation.
        Express frustration or satisfaction naturally based on your persona.
        Use language and terminology appropriate to your technical level."""

    def _get_trait_description(self, trait: str, value: float) -> str:
        """Get a descriptive text for a trait value."""
        descriptions = {
            'patience': {
                'low': 'very impatient, wants quick answers',
                'high': 'very patient, willing to explore topics deeply',
            },
            'expertise': {
                'low': 'novice, needs simple explanations',
                'high': 'expert, understands complex concepts',
            },
            'verbosity': {
                'low': 'concise, uses few words',
                'high': 'verbose, provides detailed context',
            },
        }

        desc = descriptions.get(trait)
        if not desc:
            return ''

        if value < 0.3:
            return desc['low']
        elif value > 0.7:
            return desc['high']
        else:
            return 'moderate'

    def _build_conversation_context(self) -> str:
        """Build a string representation of recent conversation."""
        recent_messages = self.state.messages[-6:]
        return '\n\n'.join(
            f"{msg.role.upper()}: {msg.content}"
            for msg in recent_messages
        )

    def _parse_simulated_response(self, content: str) -> Tuple[str, bool, float]:
        """Parse the simulated response into components."""
        lines = content.split('\n')
        message = ''
        should_continue = True
        satisfaction = 0.5

        for line in lines:
            if line.startswith('MESSAGE:'):
                message = line.replace('MESSAGE:', '').strip()
            elif line.startswith('CONTINUE:'):
                should_continue = 'true' in line.lower()
            elif line.startswith('SATISFACTION:'):
                import re
                match = re.search(r'[\d.]+', line)
                if match:
                    satisfaction = float(match.group())

        return message, should_continue, satisfaction

    def _update_state(self, assistant_message: str):
        """Update the conversation state with a new assistant message."""
        assistant_msg = Message(
            role='assistant',
            content=assistant_message,
            timestamp=datetime.now(),
            turn_number=self.state.current_turn,
        )

        self.state.messages.append(assistant_msg)
        self.state.current_turn += 1

        self._update_goal_progress()
        self._update_frustration_level()

    def _update_goal_progress(self):
        """Update the progress toward the goal."""
        progress_per_turn = 1 / (self.goal.expected_turns or 10)
        self.state.goal_progress = min(
            1.0,
            self.state.goal_progress + progress_per_turn
        )

    def _update_frustration_level(self):
        """Update the user's frustration level."""
        turn_ratio = self.state.current_turn / (self.goal.expected_turns or 10)

        if turn_ratio > 1.5:
            self.state.frustration_level = min(
                1.0,
                self.state.frustration_level + (1 - self.persona.patience) * 0.1
            )

        if self.state.user_satisfaction < 0.3:
            self.state.frustration_level = min(
                1.0,
                self.state.frustration_level + (1 - self.persona.frustration_tolerance) * 0.15
            )

    def add_user_message(self, content: str):
        """Add a user message to the conversation state."""
        user_msg = Message(
            role='user',
            content=content,
            timestamp=datetime.now(),
            turn_number=self.state.current_turn,
        )
        self.state.messages.append(user_msg)

    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation state."""
        assistant_msg = Message(
            role='assistant',
            content=content,
            timestamp=datetime.now(),
            turn_number=self.state.current_turn,
        )
        self.state.messages.append(assistant_msg)

    def update_satisfaction(self, value: float):
        """Update the user satisfaction level."""
        self.state.user_satisfaction = max(0, min(1, value))

    def get_state(self) -> ConversationState:
        """Get the current conversation state."""
        return self.state.model_copy()

    def should_stop(self) -> bool:
        """Check if the simulation should stop."""
        return (
            self.state.current_turn >= (self.goal.expected_turns or 10) * 2 or
            self.state.frustration_level > 0.9 or
            self.state.goal_progress >= 1
        )