#!/bin/bash

# Local testing script for promptfoo CI evaluation
# This script tests the REAL AI assistant endpoint

echo "🚀 Starting AI Assistant CI test..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with OPENAI_API_KEY and DATABASE_URL"
    exit 1
fi

# Load environment variables
set -a
source .env
source .env.local 2>/dev/null || true
set +a

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not set in .env"
    exit 1
fi

# Create results directory
mkdir -p results

# Start PostgreSQL with pgvector if not running
echo "🐘 Starting PostgreSQL database..."
docker compose up -d postgres
sleep 5  # Wait for database to be ready

# Run database migrations
echo "📊 Running database migrations..."
npm run db:migrate || {
    echo "⚠️  Database migration failed, trying to push schema..."
    npm run db:push || true
}

# Kill any existing server on port 3000
echo "🧹 Cleaning up existing processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 2

# Build and start the application
echo "🔨 Building application..."
npm run build || {
    echo "❌ Build failed!"
    exit 1
}

echo "🌐 Starting Next.js server in background..."
npm start > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start (may take 10-20 seconds)..."
MAX_ATTEMPTS=40
for i in $(seq 1 $MAX_ATTEMPTS); do
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        SERVER_READY=true
        break
    fi
    echo "  Waiting... ($i/$MAX_ATTEMPTS)"
    sleep 2
done

if [ "$SERVER_READY" != "true" ]; then
    echo "❌ Server failed to start. Check server.log for details"
    cat server.log | tail -20
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test the API endpoint manually first
echo ""
echo "🔍 Testing API endpoint manually..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:3000/api/chat \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{"messages":[{"role":"user","content":"Hello"}]}' 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ API endpoint responded"
    echo "Response preview: ${TEST_RESPONSE:0:100}..."
else
    echo "❌ API endpoint test failed"
    echo "Response: $TEST_RESPONSE"
fi

# Run promptfoo evaluation
echo ""
echo "🧪 Running promptfoo evaluation against REAL endpoint..."
npx promptfoo@latest eval -c promptfooconfig.yaml \
    --output results/output.json \
    --output results/output.html \
    --no-progress-bar --no-cache || true

# Display results
echo ""
echo "📊 Evaluation Results:"
echo "====================="

if [ -f results/output.json ]; then
    # Extract and display stats
    PASSED=$(jq '.results.stats.successes // 0' results/output.json)
    FAILED=$(jq '.results.stats.failures // 0' results/output.json)
    ERRORS=$(jq '.results.stats.errors // 0' results/output.json)
    TOTAL=$((PASSED + FAILED + ERRORS))

    echo "Tests Run: $TOTAL"
    echo "Tests Passed: $PASSED"
    echo "Tests Failed: $FAILED"

    if [ "$ERRORS" -gt 0 ]; then
        echo "Tests with Errors: $ERRORS"
    fi

    if [ "$TOTAL" -gt 0 ]; then
        PASS_RATE=$((PASSED * 100 / TOTAL))
        echo "Pass Rate: ${PASS_RATE}%"
    fi

    echo ""
    echo "Test Details:"
    jq -r '.results.results[] |
      (if .pass then "✅" elif .error then "⚠️" else "❌" end) +
      " " + (.testCase.description // .description // "Test case")' results/output.json 2>/dev/null || \
    echo "  (Check results/output.html for details)"
else
    echo "❌ No evaluation results found"
fi

# Kill the server
echo ""
echo "🛑 Stopping server..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

# Optional: Stop database (comment out to keep it running)
echo "🐘 Stopping database..."
docker compose stop postgres

echo ""
echo "✅ Local CI test complete!"
echo "📂 Results saved in ./results/"
echo "   - HTML Report: results/output.html"
echo "   - JSON Report: results/output.json"
echo "   - Server logs: server.log"
echo ""
echo "To view HTML report: open results/output.html"