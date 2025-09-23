#!/usr/bin/env python3

import requests
import json
from src.assistant_client import AssistantClient, AssistantClientConfig

def test_backend_connection():
    """Test the backend connection and diagnose issues."""

    print("Testing Backend Connection")
    print("=" * 40)

    # Test 1: Basic connectivity
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"✅ Backend is running (status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible at localhost:3000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

    # Test 2: Chat API endpoint availability
    try:
        response = requests.post(
            "http://localhost:3000/api/chat",
            headers={"Content-Type": "application/json"},
            json={"messages": []},
            timeout=10
        )
        print(f"✅ Chat API endpoint is accessible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error accessing chat API: {e}")
        return False

    # Test 3: Test with simulation client
    print("\nTesting with simulation client...")
    config = AssistantClientConfig("http://localhost:3000/api/chat")
    client = AssistantClient(config)

    response, time_taken, error = client.send_message("Hello, can you help me?", [])

    print(f"Response: {response[:100]}{'...' if len(response) > 100 else ''}")
    print(f"Time taken: {time_taken:.2f}ms")

    if error:
        print(f"Error: {error}")

        if "Cannot connect to API" in error:
            print("\n🔧 DIAGNOSIS:")
            print("The backend is running but cannot connect to the AI service.")
            print("This usually means:")
            print("1. Missing or invalid OPENAI_API_KEY in .env.local")
            print("2. OpenAI API quota exceeded")
            print("3. Network connectivity issues")
            print("\nPlease check your .env.local file and ensure you have a valid OpenAI API key.")
            return False
    else:
        print("✅ Simulation client working correctly!")
        return True

if __name__ == "__main__":
    test_backend_connection()