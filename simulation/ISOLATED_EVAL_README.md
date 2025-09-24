# Isolated Simulation Evaluation System

This system provides memory-isolated evaluation for the RAG (Retrieval-Augmented Generation) chatbot, ensuring that each simulation runs with a fresh vector database containing only pre-defined test memories.

## Architecture

### Problem Solved
The original evaluation system shared a single PostgreSQL database with pgvector between all simulation runs. This meant:
- Memory contamination between evaluations
- Non-deterministic results based on previous runs
- Inability to test specific memory retrieval scenarios consistently

### Solution
Each simulation now runs in its own isolated Docker environment with:
- Separate PostgreSQL + pgvector database
- Pre-seeded test memories
- Clean state for each evaluation
- Parallel execution capability

## Components

### 1. Docker Environment (`docker-compose.eval.yml`)
- **postgres-eval**: Isolated PostgreSQL with pgvector
- **app-eval**: Next.js application instance
- Dynamic service naming using `EVAL_RUN_ID`
- Automatic database initialization

### 2. Database Seeding (`simulation/db/`)
- `init.sql`: Database schema and initial resources
- `seed_embeddings.ts`: TypeScript service for generating embeddings
- Pre-defined test memories for consistent evaluation

### 3. Simulation Runners
- `IsolatedSimulationRunner`: Single simulation with isolated environment
- `IsolatedBatchSimulationRunner`: Multiple simulations, each isolated
- Automatic Docker lifecycle management

### 4. API Integration
- `/api/eval/seed`: Endpoint to initialize test embeddings
- Compatible with existing chat API
- Health checks and service readiness

## Pre-defined Test Memories

The system includes these test memories for consistent evaluation:

1. **Social Memory**: Dinner with friend Sarah at Cafe Luna
2. **Shopping Memory**: Grocery list and spending at Whole Foods
3. **Medical Memory**: Appointment with Dr. Johnson about knee injury
4. **Personal Memory**: Mom's birthday plans and gift ideas
5. **Entertainment Memory**: Reading "The Seven Husbands of Evelyn Hugo"

## Usage

### Quick Test
```bash
cd simulation
python test_isolated_eval.py
```

### Single Isolated Simulation
```python
from src.isolated_simulation_runner import IsolatedSimulationRunner
from src.types import SimulationConfig

runner = IsolatedSimulationRunner(openai_api_key)
result = await runner.run_simulation(config)
```

### Isolated Batch Evaluation
```bash
cd simulation
python isolated_batch_runner.py
```

### Custom Batch Configuration
```python
from isolated_batch_runner import IsolatedBatchSimulationRunner

runner = IsolatedBatchSimulationRunner(
    openai_api_key=api_key,
    personas=['vague_communicator', 'precise_questioner'],
    goals=['specific_memory_recall', 'vague_memory_recall'],
    runs_per_combination=3,
    max_turns=10
)

results = await runner.run_batch()
```

## Environment Variables

### Required
- `OPENAI_API_KEY`: OpenAI API key for embeddings and chat

### Automatic (set by system)
- `EVAL_RUN_ID`: Unique identifier for each evaluation run
- `EVAL_APP_PORT`: Application port (default: 3001+)
- `EVAL_DB_PORT`: Database port (default: 5433+)

## File Structure

```
simulation/
├── isolated_batch_runner.py      # Main batch evaluation script
├── test_isolated_eval.py          # Quick test script
├── db/
│   ├── init.sql                   # Database initialization
│   └── seed_embeddings.ts         # Embedding generation service
└── src/
    └── isolated_simulation_runner.py  # Core isolation logic

app/api/eval/
└── seed/
    └── route.ts                   # Database seeding endpoint

docker-compose.eval.yml            # Isolated environment definition
Dockerfile                        # Application container
```

## Benefits

### 1. **True Isolation**
- Each simulation starts with identical memory state
- No contamination from previous runs
- Deterministic evaluation results

### 2. **Parallel Execution**
- Multiple evaluations can run simultaneously
- Different port assignments prevent conflicts
- Independent Docker environments

### 3. **Consistent Testing**
- Pre-defined test memories ensure reproducible scenarios
- Same starting conditions for all evaluations
- Reliable performance metrics

### 4. **Easy Cleanup**
- Automatic environment teardown after each run
- No persistent state between evaluations
- Docker handles resource cleanup

## Performance Considerations

- **Startup Time**: ~30-60 seconds per environment (Docker + DB initialization)
- **Memory Usage**: ~500MB per isolated environment
- **Disk Space**: Temporary Docker volumes cleaned automatically
- **Ports**: Automatic assignment starting from 3001, 5433

## Monitoring

The system provides detailed logging for:
- Docker environment lifecycle
- Database seeding progress
- Simulation execution status
- Cleanup operations

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - System automatically finds available ports
   - Check Docker processes if issues persist

2. **Docker Build Failures**
   - Ensure Docker daemon is running
   - Check Dockerfile and dependencies

3. **Database Connection Issues**
   - Health checks ensure DB readiness
   - Check environment variables

4. **Seeding Failures**
   - Verify OPENAI_API_KEY is valid
   - Check API rate limits

### Debugging

Enable verbose logging:
```bash
DOCKER_BUILDKIT=1 python isolated_batch_runner.py
```

Check Docker logs:
```bash
docker-compose -f docker-compose.eval.yml -p eval-{run_id} logs
```

## Future Enhancements

- [ ] Parallel batch execution
- [ ] Custom memory scenarios
- [ ] Performance benchmarking
- [ ] Result comparison tools
- [ ] Cloud deployment support