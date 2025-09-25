#!/usr/bin/env python3
import json
import sys

# Simple echo provider for testing
def main():
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())
    prompt = input_data.get('prompt', '')

    # Return the prompt as output
    result = {
        'output': prompt
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()