# Vercel AI SDK RAG Guide Starter Project

This is the starter project for the Vercel AI SDK [Retrieval-Augmented Generation (RAG) guide](https://sdk.vercel.ai/docs/guides/rag-chatbot).

In this project, you will build a chatbot that will only respond with information that it has within its knowledge base. The chatbot will be able to both store and retrieve information. This project has many interesting use cases from customer support through to building your own second brain!

This project will use the following stack:

- [Next.js](https://nextjs.org) 14 (App Router)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [OpenAI](https://openai.com)
- [Drizzle ORM](https://orm.drizzle.team)
- [Postgres](https://www.postgresql.org/) with [ pgvector ](https://github.com/pgvector/pgvector)
- [shadcn-ui](https://ui.shadcn.com) and [TailwindCSS](https://tailwindcss.com) for styling

## CI/CD with Promptfoo

This project includes automated evaluation of the RAG assistant using [Promptfoo](https://promptfoo.dev) and GitHub Actions.

### Setup

1. **Configure GitHub Secrets**: Add the following secrets to your repository:
   - `OPENAI_API_KEY`: Your OpenAI API key for the assistant
   - `DATABASE_URL`: PostgreSQL connection string (if needed for tests)

2. **GitHub Actions Workflow**: The CI pipeline runs automatically on:
   - Push to `main` branch
   - Pull requests to `main`
   - Manual trigger via workflow dispatch

### Local Testing

Run the evaluation locally before pushing:

```bash
# Using the test script
./scripts/test-ci.sh

# Or manually with promptfoo
npx promptfoo@latest eval -c promptfooconfig.yaml
```

### Test Configuration

- **Config File**: `promptfooconfig.yaml` - Main evaluation configuration
- **Test Cases**: `prompts/test_cases.yaml` - Contains test scenarios
- **Pass Threshold**: 75% (configurable in workflow)

### Evaluation Tests

The CI evaluates these RAG capabilities:
1. Adding information to knowledge base
2. Handling unknown queries appropriately
3. Storing and retrieving technical facts
4. Response consistency and format

### Results

- **Artifacts**: HTML and JSON reports uploaded to each workflow run
- **PR Comments**: Automatic summary posted on pull requests
- **Status Badge**: Pass/fail status visible in Actions tab

### Troubleshooting

If tests fail:
1. Check the workflow logs in GitHub Actions
2. Review the uploaded HTML report for detailed results
3. Run tests locally to debug: `./scripts/test-ci.sh`
4. Ensure API keys are correctly configured in GitHub Secrets
