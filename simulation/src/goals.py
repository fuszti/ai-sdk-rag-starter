from typing import Dict
from src.types import ConversationGoal


PREDEFINED_GOALS: Dict[str, ConversationGoal] = {
    'vague_memory_recall': ConversationGoal(
        id='vague-memory-recall',
        description='Ask vague questions about previously stored memories to test clarification policy',
        success_criteria=[
            'Assistant recognizes vague query and asks clarifying questions',
            'User provides clarification in response to assistant prompts',
            'Assistant uses clarification to search for specific memory',
            'User either gets their answer or understands why memory not found',
        ],
        expected_turns=4,
        domain='general',
        complexity='moderate',
    ),

    'specific_memory_recall': ConversationGoal(
        id='specific-memory-recall',
        description='Ask specific questions about stored memories to test direct retrieval',
        success_criteria=[
            'Assistant immediately searches for the specific memory',
            'Assistant provides the memory if found or explains if not found',
            'No unnecessary clarification requests for clear queries',
        ],
        expected_turns=2,
        domain='general',
        complexity='simple',
    ),

    'multi_clarification_memory': ConversationGoal(
        id='multi-clarification-memory',
        description='Ask extremely vague questions requiring multiple rounds of clarification',
        success_criteria=[
            'Assistant asks appropriate follow-up clarification questions',
            'Assistant maintains context through multiple clarification rounds',
            'User eventually gets specific enough for memory search',
            'Assistant successfully retrieves or explains absence of memory',
        ],
        expected_turns=6,
        domain='general',
        complexity='complex',
    ),

    'resist_clarification': ConversationGoal(
        id='resist-clarification',
        description='Test how assistant handles users who resist providing clarification',
        success_criteria=[
            'Assistant persists in seeking necessary clarification',
            'Assistant explains why clarification is needed',
            'Assistant handles user frustration gracefully',
            'Assistant either gets clarification or explains inability to help',
        ],
        expected_turns=5,
        domain='general',
        complexity='moderate',
    ),

    'memory_storage_test': ConversationGoal(
        id='memory-storage-test',
        description='Share information to be stored and then test recall with vague queries',
        success_criteria=[
            'Assistant successfully stores shared information',
            'Assistant later asks for clarification when vague recall attempted',
            'Assistant retrieves stored information after clarification provided',
        ],
        expected_turns=6,
        domain='general',
        complexity='moderate',
    ),
}


def create_custom_goal(**overrides) -> ConversationGoal:
    """Create a custom goal with specified overrides."""
    base = PREDEFINED_GOALS['learn_basic_concept'].model_dump()
    base.update(overrides)

    if 'id' not in overrides:
        import time
        base['id'] = f'custom-goal-{int(time.time() * 1000)}'

    return ConversationGoal(**base)