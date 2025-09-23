from typing import Dict
from src.types import UserPersona


PREDEFINED_PERSONAS: Dict[str, UserPersona] = {
    'vague_communicator': UserPersona(
        id='vague-communicator',
        name='Vague Communicator',
        description='A user who tends to ask unclear questions about their stored memories, testing clarification policy',
        patience=0.6,
        expertise=0.4,
        verbosity=0.3,
        frustration_tolerance=0.5,
        clarity_of_communication=0.2,  # Intentionally low - asks vague questions
        technical_level=0.3,
    ),

    'clarification_cooperative': UserPersona(
        id='clarification-cooperative',
        name='Clarification Cooperative',
        description='A helpful user who provides good clarifications when asked by the memory assistant',
        patience=0.8,
        expertise=0.5,
        verbosity=0.6,
        frustration_tolerance=0.7,
        clarity_of_communication=0.8,
        technical_level=0.4,
    ),

    'clarification_resistant': UserPersona(
        id='clarification-resistant',
        name='Clarification Resistant',
        description='A user who gets frustrated with clarification requests and resists providing details',
        patience=0.2,
        expertise=0.3,
        verbosity=0.4,
        frustration_tolerance=0.3,
        clarity_of_communication=0.4,
        technical_level=0.2,
    ),

    'memory_heavy_user': UserPersona(
        id='memory-heavy-user',
        name='Memory Heavy User',
        description='A user who stores lots of information and frequently recalls it with varying levels of specificity',
        patience=0.7,
        expertise=0.6,
        verbosity=0.7,
        frustration_tolerance=0.6,
        clarity_of_communication=0.6,
        technical_level=0.5,
    ),

    'precise_questioner': UserPersona(
        id='precise-questioner',
        name='Precise Questioner',
        description='A user who asks very specific questions about stored memories, testing direct retrieval',
        patience=0.5,
        expertise=0.7,
        verbosity=0.5,
        frustration_tolerance=0.5,
        clarity_of_communication=0.9,  # Very clear communication
        technical_level=0.6,
    ),

    'extremely_vague': UserPersona(
        id='extremely-vague',
        name='Extremely Vague',
        description='A user who asks the most ambiguous questions possible, requiring multiple clarification rounds',
        patience=0.4,
        expertise=0.2,
        verbosity=0.3,
        frustration_tolerance=0.4,
        clarity_of_communication=0.1,  # Extremely unclear
        technical_level=0.1,
    ),
}


def create_custom_persona(**overrides) -> UserPersona:
    """Create a custom persona with specified overrides."""
    base = PREDEFINED_PERSONAS['average_user'].model_dump()
    base.update(overrides)

    if 'id' not in overrides:
        import time
        base['id'] = f'custom-{int(time.time() * 1000)}'

    return UserPersona(**base)