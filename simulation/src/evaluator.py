from typing import List
from openai import OpenAI
from src.types import (
    ConversationState,
    ConversationGoal,
    EvaluationMetrics,
    UserPersona,
)


class ConversationEvaluator:
    """
    LLM-as-Judge evaluator for conversation quality.

    Uses integer scoring (0-3) internally for better consistency and reliability,
    following best practices for LLM evaluation:

    Scoring Scale:
    - 0: Poor - Fails to meet basic requirements
    - 1: Fair - Partially meets requirements with notable issues
    - 2: Good - Mostly meets requirements with minor issues
    - 3: Excellent - Fully meets or exceeds requirements

    Scores are normalized to 0-1 floats for metrics compatibility.
    """
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)

    def evaluate(
        self,
        conversation: ConversationState,
        goal: ConversationGoal,
        persona: UserPersona,
        response_times: List[float],
        errors: List[str]
    ) -> EvaluationMetrics:
        """Evaluate a completed conversation.

        Uses 0-3 integer scoring internally, normalized to 0-1 floats for metrics.
        """
        goal_achieved = self._evaluate_goal_achievement(conversation, goal)

        # Get integer scores (0-3) and normalize to 0-1 floats
        clarity_score_int = self._evaluate_clarity(conversation)
        relevance_score_int = self._evaluate_relevance(conversation, goal)
        completeness_score_int = self._evaluate_completeness(conversation, goal)

        # Normalize integer scores (0-3) to float scores (0-1)
        clarity_score = clarity_score_int / 3.0
        relevance_score = relevance_score_int / 3.0
        completeness_score = completeness_score_int / 3.0

        frustration_incidents = self._count_frustration_incidents(conversation)
        error_rate = len(errors) / max(len(conversation.messages), 1)

        average_response_time = (
            sum(response_times) / len(response_times)
            if response_times else 0
        )

        return EvaluationMetrics(
            goal_achieved=goal_achieved,
            total_turns=conversation.current_turn,
            average_response_time=average_response_time,
            user_satisfaction_score=conversation.user_satisfaction,
            clarity_score=clarity_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            frustration_incidents=frustration_incidents,
            error_rate=error_rate,
        )

    def _evaluate_goal_achievement(
        self,
        conversation: ConversationState,
        goal: ConversationGoal
    ) -> bool:
        """Evaluate if the conversation achieved its goal."""
        conversation_text = '\n\n'.join(
            f"{msg.role}: {msg.content}"
            for msg in conversation.messages
        )

        prompt = f"""Evaluate if the following conversation achieved its goal.

        Context: This is a "Keep in mind" memory assistant that follows a clarification policy:
        - When users ask vague questions about stored memories, the assistant should ask clarifying questions
        - When users ask specific questions, the assistant should search directly
        - The assistant should help users find their stored information through appropriate clarification

        Goal: {goal.description}

        Success Criteria:
        {chr(10).join(f'- {c}' for c in goal.success_criteria)}

        Conversation:
        {conversation_text}

        Based on the success criteria, was the goal achieved? Consider:
        1. Were all success criteria met?
        2. Did the assistant follow the clarification policy appropriately?
        3. Did the user ultimately get their answer or understand why not?
        4. Was the assistant's behavior appropriate for the query type (vague vs specific)?

        Respond with only "TRUE" if the goal was achieved, or "FALSE" if not."""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_completion_tokens=10,
        )

        result = response.choices[0].message.content.upper().strip()
        return result == 'TRUE'

    def _evaluate_clarity(self, conversation: ConversationState) -> int:
        """Evaluate the clarity of assistant responses using 0-3 integer scale."""
        assistant_messages = '\n\n'.join(
            msg.content
            for msg in conversation.messages
            if msg.role == 'assistant'
        )

        if not assistant_messages:
            return 1  # Default to "fair" if no messages

        prompt = f"""Evaluate the clarity of these assistant responses.

        Assistant Messages:
        {assistant_messages}

        Scoring Rubric (0-3):
        0 - Poor: Responses are confusing, unclear, or incomprehensible. Structure is illogical, instructions are vague.
        1 - Fair: Responses are somewhat clear but have notable issues. Some parts are confusing or poorly structured.
        2 - Good: Responses are mostly clear and well-structured. Minor clarity issues that don't impede understanding.
        3 - Excellent: Responses are crystal clear, well-organized, and easy to follow. Instructions are specific and actionable.

        Evaluation Criteria:
        - Are explanations clear and easy to understand?
        - Is technical jargon explained when necessary?
        - Are instructions specific and actionable?
        - Is the structure logical and easy to follow?

        First provide your reasoning, then give your score.
        Format your response as:
        REASONING: [Your analysis]
        SCORE: [0, 1, 2, or 3]"""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_completion_tokens=200,
        )

        try:
            response_text = response.choices[0].message.content
            score_line = [line for line in response_text.split('\n') if 'SCORE:' in line][0]
            score = int(score_line.split('SCORE:')[1].strip())
            return max(0, min(3, score))
        except (ValueError, IndexError):
            return 1  # Default to "fair" on parsing errors

    def _evaluate_relevance(
        self,
        conversation: ConversationState,
        goal: ConversationGoal
    ) -> int:
        """Evaluate the relevance of responses to the goal using 0-3 integer scale."""
        conversation_text = '\n\n'.join(
            f"{msg.role}: {msg.content}"
            for msg in conversation.messages
        )

        prompt = f"""Evaluate the relevance of the assistant's responses to the user's goal.

        User's Goal: {goal.description}
        Domain: {goal.domain}

        Conversation:
        {conversation_text}

        Scoring Rubric (0-3):
        0 - Irrelevant: Responses mostly miss the point, contain off-topic content, or fail to address the goal.
        1 - Partially Relevant: Some responses address the goal but with significant tangents or missing key aspects.
        2 - Mostly Relevant: Responses generally stay on topic and address the goal with minor irrelevant content.
        3 - Highly Relevant: All responses directly address the user's questions and goal without unnecessary tangents.

        Evaluation Criteria:
        - Do responses directly address the user's questions?
        - Is information provided relevant to the goal?
        - Are there unnecessary tangents or off-topic content?
        - Does the assistant stay focused on helping achieve the goal?

        First provide your reasoning, then give your score.
        Format your response as:
        REASONING: [Your analysis]
        SCORE: [0, 1, 2, or 3]"""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_completion_tokens=200,
        )

        try:
            response_text = response.choices[0].message.content
            score_line = [line for line in response_text.split('\n') if 'SCORE:' in line][0]
            score = int(score_line.split('SCORE:')[1].strip())
            return max(0, min(3, score))
        except (ValueError, IndexError):
            return 1  # Default to "fair" on parsing errors

    def _evaluate_completeness(
        self,
        conversation: ConversationState,
        goal: ConversationGoal
    ) -> int:
        """Evaluate the completeness of responses using 0-3 integer scale."""
        conversation_text = '\n\n'.join(
            f"{msg.role}: {msg.content}"
            for msg in conversation.messages
        )

        prompt = f"""Evaluate the completeness of the assistant's responses.

        Goal: {goal.description}
        Expected Complexity: {goal.complexity}

        Success Criteria:
        {chr(10).join(f'- {c}' for c in goal.success_criteria)}

        Conversation:
        {conversation_text}

        Scoring Rubric (0-3):
        0 - Incomplete: Major aspects missing, provides only surface-level information, fails to meet success criteria.
        1 - Partially Complete: Addresses some aspects but omits important details or steps, meets few success criteria.
        2 - Mostly Complete: Covers most important aspects with adequate depth, meets most success criteria.
        3 - Fully Complete: Thoroughly addresses all aspects with appropriate depth, meets all success criteria.

        Evaluation Criteria:
        - Were all aspects of the question addressed?
        - Are responses thorough given the complexity level?
        - Were important details or steps omitted?
        - Did the assistant provide sufficient depth?

        First provide your reasoning, then give your score.
        Format your response as:
        REASONING: [Your analysis]
        SCORE: [0, 1, 2, or 3]"""

        response = self.client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_completion_tokens=200,
        )

        try:
            response_text = response.choices[0].message.content
            score_line = [line for line in response_text.split('\n') if 'SCORE:' in line][0]
            score = int(score_line.split('SCORE:')[1].strip())
            return max(0, min(3, score))
        except (ValueError, IndexError):
            return 1  # Default to "fair" on parsing errors

    def _count_frustration_incidents(self, conversation: ConversationState) -> int:
        """Count frustration incidents in user messages."""
        incidents = 0
        frustration_phrases = [
            'not what i asked',
            "that's not helpful",
            "you're not understanding",
            'this is frustrating',
            'can you just',
            'i already said',
            'please listen',
            'wrong answer',
            "that doesn't help",
            "this isn't working",
        ]

        for message in conversation.messages:
            if message.role == 'user':
                lower_content = message.content.lower()
                for phrase in frustration_phrases:
                    if phrase in lower_content:
                        incidents += 1
                        break

        return incidents

    def generate_report(self, metrics: EvaluationMetrics) -> str:
        """Generate a human-readable evaluation report.

        Displays both normalized percentages and original 0-3 scale ratings.
        """
        overall_score = self._calculate_overall_score(metrics)

        # Convert normalized scores back to 0-3 scale for display
        clarity_rating = round(metrics.clarity_score * 3)
        relevance_rating = round(metrics.relevance_score * 3)
        completeness_rating = round(metrics.completeness_score * 3)
        satisfaction_rating = round(metrics.user_satisfaction_score * 3)

        report = f"""
=== EVALUATION REPORT ===

Overall Score: {overall_score * 100:.1f}% {self._get_grade(overall_score)}

Goal Achievement: {'✓ Achieved' if metrics.goal_achieved else '✗ Not Achieved'}

Performance Metrics:
- Total Turns: {metrics.total_turns}
- Avg Response Time: {metrics.average_response_time / 1000:.2f}s
- Error Rate: {metrics.error_rate * 100:.1f}%

Quality Scores (0-3 scale | percentage):
- User Satisfaction: {satisfaction_rating}/3 ({metrics.user_satisfaction_score * 100:.1f}%)
- Clarity: {clarity_rating}/3 ({metrics.clarity_score * 100:.1f}%)
- Relevance: {relevance_rating}/3 ({metrics.relevance_score * 100:.1f}%)
- Completeness: {completeness_rating}/3 ({metrics.completeness_score * 100:.1f}%)

Score Interpretation:
  0 = Poor | 1 = Fair | 2 = Good | 3 = Excellent

Issues:
- Frustration Incidents: {metrics.frustration_incidents}

{self._generate_recommendations(metrics)}
"""
        return report

    def _calculate_overall_score(self, metrics: EvaluationMetrics) -> float:
        """Calculate an overall score from individual metrics."""
        weights = {
            'goal_achieved': 0.25,
            'user_satisfaction': 0.20,
            'clarity': 0.15,
            'relevance': 0.20,
            'completeness': 0.15,
            'error_penalty': 0.05,
        }

        score = 0
        score += weights['goal_achieved'] if metrics.goal_achieved else 0
        score += metrics.user_satisfaction_score * weights['user_satisfaction']
        score += metrics.clarity_score * weights['clarity']
        score += metrics.relevance_score * weights['relevance']
        score += metrics.completeness_score * weights['completeness']
        score -= metrics.error_rate * weights['error_penalty']

        score -= metrics.frustration_incidents * 0.02

        return max(0, min(1, score))

    def _get_grade(self, score: float) -> str:
        """Convert score to a letter grade."""
        # Adjusted thresholds for 0-3 scale normalized to 0-1
        if score >= 0.83:  # ~2.5/3
            return '(Excellent)'
        elif score >= 0.67:  # ~2/3
            return '(Good)'
        elif score >= 0.5:  # ~1.5/3
            return '(Satisfactory)'
        elif score >= 0.33:  # ~1/3
            return '(Needs Improvement)'
        else:
            return '(Poor)'

    def _generate_recommendations(self, metrics: EvaluationMetrics) -> str:
        """Generate recommendations based on evaluation metrics."""
        recommendations = []

        if not metrics.goal_achieved:
            recommendations.append('- Focus on achieving user goals more effectively')

        # Using 2/3 threshold (equivalent to score of 2 out of 3)
        if metrics.clarity_score < 0.67:
            recommendations.append('- Improve response clarity and structure')

        if metrics.relevance_score < 0.67:
            recommendations.append('- Stay more focused on user questions')

        if metrics.completeness_score < 0.67:
            recommendations.append('- Provide more comprehensive responses')

        if metrics.frustration_incidents > 2:
            recommendations.append('- Better understand user intent to reduce frustration')

        if metrics.error_rate > 0.1:
            recommendations.append('- Improve error handling and recovery')

        if not recommendations:
            recommendations.append('- Continue maintaining high performance')

        return f"Recommendations:\n{chr(10).join(recommendations)}"

    @staticmethod
    def aggregate_metrics(metrics_list: List[EvaluationMetrics]) -> EvaluationMetrics:
        """Aggregate multiple evaluation metrics into a single summary.

        Args:
            metrics_list: List of EvaluationMetrics from multiple simulations

        Returns:
            Aggregated EvaluationMetrics with averaged scores
        """
        if not metrics_list:
            raise ValueError("Cannot aggregate empty metrics list")

        n = len(metrics_list)

        # Calculate averages
        goal_achieved_rate = sum(m.goal_achieved for m in metrics_list) / n
        avg_turns = sum(m.total_turns for m in metrics_list) / n
        avg_response_time = sum(m.average_response_time for m in metrics_list) / n
        avg_satisfaction = sum(m.user_satisfaction_score for m in metrics_list) / n
        avg_clarity = sum(m.clarity_score for m in metrics_list) / n
        avg_relevance = sum(m.relevance_score for m in metrics_list) / n
        avg_completeness = sum(m.completeness_score for m in metrics_list) / n
        total_frustration = sum(m.frustration_incidents for m in metrics_list)
        avg_error_rate = sum(m.error_rate for m in metrics_list) / n

        # Return aggregated metrics
        return EvaluationMetrics(
            goal_achieved=goal_achieved_rate >= 0.5,  # Majority achieved
            total_turns=round(avg_turns),
            average_response_time=avg_response_time,
            user_satisfaction_score=avg_satisfaction,
            clarity_score=avg_clarity,
            relevance_score=avg_relevance,
            completeness_score=avg_completeness,
            frustration_incidents=round(total_frustration / n),
            error_rate=avg_error_rate,
        )

    def generate_aggregated_report(
        self,
        metrics_list: List[EvaluationMetrics],
        num_simulations: int
    ) -> str:
        """Generate a report for aggregated metrics from multiple simulations.

        Args:
            metrics_list: List of individual simulation metrics
            num_simulations: Total number of simulations run

        Returns:
            Formatted report string
        """
        aggregated = self.aggregate_metrics(metrics_list)
        goal_achievement_rate = sum(m.goal_achieved for m in metrics_list) / len(metrics_list) * 100

        report = f"""
=== AGGREGATED EVALUATION REPORT ===
Simulations Run: {num_simulations}
Successful Evaluations: {len(metrics_list)}

{self.generate_report(aggregated)}

Goal Achievement Rate: {goal_achievement_rate:.1f}%

Individual Score Distribution (0-3 scale):
- Clarity: {self._get_score_distribution(metrics_list, 'clarity_score')}
- Relevance: {self._get_score_distribution(metrics_list, 'relevance_score')}
- Completeness: {self._get_score_distribution(metrics_list, 'completeness_score')}
"""
        return report

    def _get_score_distribution(self, metrics_list: List[EvaluationMetrics], score_attr: str) -> str:
        """Get distribution of scores for a specific attribute."""
        scores = [round(getattr(m, score_attr) * 3) for m in metrics_list]
        distribution = {0: 0, 1: 0, 2: 0, 3: 0}
        for score in scores:
            distribution[score] += 1

        total = len(scores)
        return " | ".join([
            f"{score}: {count} ({count/total*100:.0f}%)"
            for score, count in distribution.items()
        ])