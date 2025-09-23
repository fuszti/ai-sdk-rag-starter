import time
import json
import requests
from typing import Dict, List, Optional, Tuple
from src.types import Message


class AssistantClientConfig:
    def __init__(
        self,
        api_endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30000
    ):
        self.api_endpoint = api_endpoint
        self.headers = headers or {}
        self.timeout = timeout / 1000  # Convert to seconds


class AssistantClient:
    def __init__(self, config: AssistantClientConfig):
        self.config = config

    def send_message(
        self,
        message: str,
        conversation_history: List[Message]
    ) -> Tuple[str, float, Optional[str]]:
        """
        Send a message to the assistant and get a response.
        Returns: (response, response_time_ms, error)
        """
        start_time = time.time()

        try:
            # Build messages array in AI SDK UIMessage format
            messages = []
            for i, msg in enumerate(conversation_history):
                messages.append({
                    'id': f'msg-{i}',
                    'role': msg.role,
                    'parts': [{'type': 'text', 'text': msg.content}]
                })

            # Add the new user message
            messages.append({
                'id': f'msg-{len(conversation_history)}',
                'role': 'user',
                'parts': [{'type': 'text', 'text': message}]
            })

            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'User-Agent': 'AI-Simulation-Client/1.0',
                **self.config.headers
            }

            request_data = {'messages': messages}

            # Make the request with streaming enabled
            response = requests.post(
                self.config.api_endpoint,
                json=request_data,
                headers=headers,
                timeout=self.config.timeout,
                stream=True
            )

            if not response.ok:
                # Try to get more details about the error
                try:
                    error_body = response.text
                    raise Exception(f"API responded with status {response.status_code}: {error_body}")
                except Exception as err_e:
                    raise Exception(f"API responded with status {response.status_code}")

            # Handle streaming response with better error handling
            full_response = ''
            error_message = None
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')

                        # Handle Next.js streaming format (0:...)
                        if line_str.startswith('0:'):
                            content = line_str[2:].strip()
                            if content and content not in ['"', '""']:
                                try:
                                    # Try to parse as JSON
                                    parsed = json.loads(content)
                                    if isinstance(parsed, str):
                                        full_response += parsed
                                    else:
                                        full_response += str(parsed)
                                except json.JSONDecodeError:
                                    # Remove quotes and add content
                                    content_cleaned = content.strip('"')
                                    full_response += content_cleaned

                        # Handle SSE format (data: ...)
                        elif line_str.startswith('data: '):
                            data = line_str[6:].strip()
                            if data and data != '[DONE]':
                                try:
                                    parsed = json.loads(data)

                                    # Handle AI SDK message format
                                    if parsed.get('type') == 'error':
                                        error_message = parsed.get('errorText', 'Unknown error')
                                        break
                                    elif parsed.get('type') == 'text-delta':
                                        full_response += parsed.get('delta', '')
                                    elif parsed.get('type') == 'text':
                                        full_response += parsed.get('text', '')

                                    # Handle OpenAI streaming format (fallback)
                                    elif 'choices' in parsed and parsed['choices']:
                                        delta = parsed['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            full_response += delta['content']

                                except json.JSONDecodeError:
                                    # Fallback: treat as raw text if not JSON
                                    if not data.startswith('{'):
                                        full_response += data

                        # Handle plain text lines
                        elif line_str.strip() and not line_str.startswith(':'):
                            # Try to parse as JSON first
                            try:
                                parsed = json.loads(line_str)
                                if isinstance(parsed, str):
                                    full_response += parsed
                                else:
                                    full_response += str(parsed)
                            except json.JSONDecodeError:
                                full_response += line_str

                # If no content was found in streaming, try to get the full response
                if not full_response.strip():
                    try:
                        response_text = response.text
                        if response_text:
                            full_response = response_text
                    except:
                        pass

            except Exception as parse_error:
                # Fallback to full response text
                try:
                    full_response = response.text
                except:
                    raise Exception(f"Response parsing error: {parse_error}")

            response_time = (time.time() - start_time) * 1000

            # Return error if one was detected in the stream
            if error_message:
                return '', response_time, error_message

            return full_response.strip() or 'No response received', response_time, None

        except requests.Timeout:
            response_time = (time.time() - start_time) * 1000
            return '', response_time, 'Request timeout'

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return '', response_time, str(e)