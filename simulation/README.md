# AI Assistant Multi-Turn Evaluation System

This Python-based simulation system evaluates your AI assistant through automated multi-turn conversations with OpenAI-powered user simulations. It provides comprehensive metrics and insights to improve your assistant's performance across different user types and scenarios.

## Key Features

### Intelligent User Simulation
- Uses OpenAI GPT-4 to simulate realistic users with distinct personalities
- Dynamic behavior adaptation based on conversation progress
- Natural frustration and satisfaction modeling

### Rich Persona System
- 6 predefined personas (novice to expert, impatient to patient)
- Configurable personality traits on 0-1 scales
- Easy custom persona creation

### Goal-Driven Conversations
- 7 predefined conversation goals across domains
- Clear success criteria for objective evaluation
- Support for custom goals and scenarios

### Comprehensive Evaluation
- AI-powered scoring for clarity, relevance, and completeness
- Performance metrics (response time, error rate, turn count)
- Frustration incident detection and user satisfaction tracking

### Batch Testing & Analysis
- Run multiple persona/goal combinations automatically
- Statistical analysis across different scenarios
- Comparative performance insights

### Rich Reporting
- Colored console output with real-time progress
- Detailed JSON results with full conversation transcripts
- Actionable recommendations for improvement

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key
- Your Next.js AI assistant running locally

### Installation

1. **Navigate to simulation directory:**
   ```bash
   cd simulation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   ASSISTANT_API_URL=http://localhost:3000/api/chat
   BRAINTRUST_API_KEY=optional-for-logging
   ```

4. **Start your Next.js assistant:**
   ```bash
   # In the root directory
   pnpm dev
   ```

## Usage

### Single Simulation

Test specific user scenarios with targeted simulations:

```bash
python run_simulation.py [persona] [goal]
```

**Example Commands:**
```bash
# Test how an average user learns basic concepts
python run_simulation.py average_user learn_basic_concept

# See how an impatient novice handles troubleshooting
python run_simulation.py impatient_novice troubleshoot_issue

# Evaluate expert-level deep analysis capabilities
python run_simulation.py patient_expert deep_dive_analysis

# Quick fact-checking with a busy professional
python run_simulation.py busy_professional quick_fact_check
```

**Real-time Output:**
```
🤖 Starting Simulation
Persona: Impatient Novice
Goal: Learn about basic concept
Max Turns: 20

USER: I need to understand what RAG is but I'm in a hurry
ASSISTANT: RAG stands for Retrieval-Augmented Generation...
USER: That's too technical, can you simplify it?
...

📊 Evaluating Conversation...

=== EVALUATION REPORT ===
Overall Score: 78.5% (Good)
Goal Achievement: ✓ Achieved
```

### Batch Simulations

Run comprehensive testing across multiple scenarios:

```bash
python batch_runner.py
```

This automatically tests combinations of:
- 3 different personas (impatient_novice, average_user, patient_expert)
- 3 different goals (learn_basic_concept, troubleshoot_issue, quick_fact_check)
- 2 runs per combination = 18 total simulations

**Batch Output Summary:**
```
📊 BATCH SIMULATION SUMMARY
==================================================

Overall Results:
  Total Runs: 18
  Successful: 17
  Failed: 1

Average Metrics:
  Overall Score: 82.3%
  Goal Achievement Rate: 89.5%
  User Satisfaction: 78.2%
  Clarity Score: 85.1%
  Relevance Score: 91.2%
  Completeness Score: 76.8%
```

## User Personas

### Predefined Personas

| Persona | Description | Key Traits |
|---------|-------------|------------|
| **impatient_novice** | Non-technical user wanting quick answers | Low patience (0.2), Low expertise (0.1) |
| **patient_expert** | Technical expert appreciating detailed explanations | High patience (0.9), High expertise (0.9) |
| **average_user** | Typical user with moderate technical knowledge | Balanced traits (0.5 across most dimensions) |
| **confused_student** | Student learning, needs frequent clarification | High patience (0.7), Low clarity (0.3) |
| **busy_professional** | Time-conscious user needing precise answers | Low patience (0.3), High clarity (0.8) |
| **detail_oriented_researcher** | Wants comprehensive information with sources | High verbosity (0.9), High expertise (0.8) |

### Persona Trait System (0-1 Scale)

Each persona is defined by six core traits that shape their behavior:

- **`patience`** (0-1): Willingness to wait for comprehensive answers
- **`expertise`** (0-1): Domain knowledge and technical understanding
- **`verbosity`** (0-1): How much detail they provide in their messages
- **`frustration_tolerance`** (0-1): Resistance to becoming frustrated
- **`clarity_of_communication`** (0-1): How clearly they express their needs
- **`technical_level`** (0-1): Comfort with technical terminology

### Creating Custom Personas

```python
from src.personas import create_custom_persona

# Create a custom "Anxious Developer" persona
anxious_dev = create_custom_persona(
    name='Anxious Developer',
    description='A developer under pressure who needs quick, accurate solutions',
    patience=0.3,           # Somewhat impatient
    expertise=0.7,          # Good technical knowledge
    verbosity=0.4,          # Concise communication
    frustration_tolerance=0.2,  # Gets frustrated easily
    clarity_of_communication=0.8,  # Communicates clearly
    technical_level=0.8     # High technical understanding
)
```

## Conversation Goals

### Predefined Goals

| Goal | Domain | Complexity | Expected Turns | Description |
|------|--------|------------|----------------|-------------|
| **learn_basic_concept** | Educational | Simple | 5 | Learn about a basic concept with clear explanations |
| **troubleshoot_issue** | Technical | Moderate | 8 | Diagnose and solve a technical problem step-by-step |
| **deep_dive_analysis** | Technical | Complex | 12 | Comprehensive analysis with multiple perspectives |
| **quick_fact_check** | General | Simple | 2 | Get a quick, accurate answer to a specific question |
| **step_by_step_guide** | Technical | Moderate | 6 | Detailed instructions for completing a task |
| **comparative_analysis** | Business | Moderate | 8 | Compare multiple options with pros/cons |
| **creative_ideation** | Creative | Complex | 10 | Brainstorm innovative solutions and ideas |

### Goal Configuration

Each goal defines:

- **`success_criteria`**: Specific, measurable outcomes that indicate success
- **`expected_turns`**: Anticipated conversation length for baseline comparison
- **`domain`**: Context area (technical, general, business, creative, educational)
- **`complexity`**: Difficulty level affecting evaluation expectations

### Success Criteria Examples

**learn_basic_concept:**
- ✅ User receives a clear explanation of the concept
- ✅ User gets relevant examples if applicable
- ✅ Key terminology is explained appropriately

**troubleshoot_issue:**
- ✅ Problem is clearly identified
- ✅ Root cause is determined
- ✅ Solution is provided with clear steps
- ✅ Implementation guidance is given

### Creating Custom Goals

```python
from src.goals import create_custom_goal

# Create a custom goal for API integration help
api_help_goal = create_custom_goal(
    description='Learn how to integrate with the Stripe API',
    success_criteria=[
        'User understands API authentication',
        'User knows how to make basic API calls',
        'User gets code examples',
        'Error handling is explained'
    ],
    expected_turns=8,
    domain='technical',
    complexity='moderate'
)
```

## Evaluation Metrics

The system provides comprehensive evaluation across multiple dimensions:

### Success Metrics
- **Goal Achievement**: Binary success/failure based on success criteria
- **User Satisfaction**: Simulated user's satisfaction level (0-1)
- **Overall Score**: Weighted composite score across all metrics

### Quality Metrics (AI-Evaluated)
- **Clarity Score** (0-100%): How clear and understandable responses are
- **Relevance Score** (0-100%): How well responses address user questions
- **Completeness Score** (0-100%): How thorough responses are given complexity

### Performance Metrics
- **Total Turns**: Number of conversation exchanges
- **Average Response Time**: Assistant API response latency
- **Error Rate**: Frequency of API/system errors
- **Frustration Incidents**: Count of user frustration expressions

### Scoring Algorithm

The overall score is calculated using weighted metrics:
```
Overall Score = (
    Goal Achievement × 25% +
    User Satisfaction × 20% +
    Clarity Score × 15% +
    Relevance Score × 20% +
    Completeness Score × 15% +
    Performance Penalties × 5%
)
```

**Grade Scale:**
- 90-100%: Excellent
- 80-89%: Good
- 70-79%: Satisfactory
- 60-69%: Needs Improvement
- <60%: Poor

## Results & Data

### Result Storage

All simulation results are automatically saved to `simulation/results/` as structured JSON files:

```json
{
  "config": {
    "persona": { "name": "Average User", "traits": {...} },
    "goal": { "description": "Learn basic concept", "criteria": [...] }
  },
  "conversation": {
    "messages": [
      { "role": "user", "content": "...", "timestamp": "..." },
      { "role": "assistant", "content": "...", "timestamp": "..." }
    ],
    "final_satisfaction": 0.85,
    "goal_progress": 0.95
  },
  "metrics": {
    "goal_achieved": true,
    "overall_score": 0.823,
    "clarity_score": 0.91,
    "relevance_score": 0.88,
    "user_satisfaction_score": 0.85
  },
  "duration": 45230,
  "errors": []
}
```

### Data Analysis

Results can be analyzed using standard Python data tools:

```python
import json
import pandas as pd
from pathlib import Path

# Load all results
results = []
for file in Path("simulation/results").glob("*.json"):
    with open(file) as f:
        results.append(json.load(f))

# Convert to DataFrame for analysis
df = pd.DataFrame([{
    'persona': r['config']['persona']['name'],
    'goal': r['config']['goal']['description'],
    'success': r['metrics']['goal_achieved'],
    'score': r['metrics']['overall_score'],
    'satisfaction': r['metrics']['user_satisfaction_score']
} for r in results])

# Analyze performance by persona
persona_stats = df.groupby('persona').agg({
    'success': 'mean',
    'score': 'mean',
    'satisfaction': 'mean'
})
```

## Project Structure

```
simulation/
├── src/                        # Core simulation code
│   ├── __init__.py
│   ├── types.py                # Pydantic data models
│   ├── personas.py             # User persona definitions
│   ├── goals.py                # Conversation goal configs
│   ├── user_simulator.py       # OpenAI-powered user simulation
│   ├── assistant_client.py     # Next.js API client
│   ├── evaluator.py            # AI conversation evaluation
│   └── simulation_runner.py    # Main orchestration logic
├── results/                    # Generated simulation data (auto-created)
├── config/                     # Configuration files (for custom setups)
├── tests/                      # Unit tests (future expansion)
├── run_simulation.py           # Single simulation entry point
├── batch_runner.py             # Batch simulation entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This documentation
```

## Advanced Usage

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...                    # OpenAI API key for user simulation

# Optional
ASSISTANT_API_URL=http://localhost:3000/api/chat  # Your assistant endpoint
BRAINTRUST_API_KEY=bt-...               # For logging conversations
```

### Custom Batch Configurations

Modify `batch_runner.py` to test specific scenarios:

```python
# Custom batch configuration
personas = ['impatient_novice', 'patient_expert']  # Test extreme cases
goals = ['troubleshoot_issue']                      # Focus on one goal type
runs_per_combination = 5                            # More statistical power
max_turns = 25                                      # Allow longer conversations
```

### Integration with CI/CD

Add to your GitHub Actions workflow:

```yaml
- name: Run AI Assistant Evaluation
  run: |
    cd simulation
    pip install -r requirements.txt
    python batch_runner.py
    # Upload results to artifacts or send to monitoring
```

## Extending the System

### Evaluation Metrics
- Add domain-specific scoring (e.g., code quality for technical responses)
- Implement custom rubrics for specialized use cases
- Integration with human evaluation workflows

### User Simulation
- Support for different LLM providers (Anthropic, local models)
- Multi-modal simulation (images, documents)
- Conversation memory and context persistence

### Analysis & Monitoring
- Real-time dashboard with live simulation results
- A/B testing framework for assistant improvements
- Integration with observability tools (Braintrust, Weights & Biases)
- Export to analytics platforms (Google Analytics, Mixpanel)

### Custom Integrations
- Slack/Discord bot for running evaluations
- API endpoints for triggering simulations programmatically
- Webhook notifications for completed batch runs
- Custom evaluation criteria for specific domains