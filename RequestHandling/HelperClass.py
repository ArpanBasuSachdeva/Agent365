import os
import shutil
import tempfile
import uuid
import subprocess
import requests
import ssl
import urllib3
import json
from dotenv import load_dotenv

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def handle_streaming_response(response):
    """
    Handle streaming response from Gemini API.
    Returns a combined result similar to non-streaming response.
    """
    full_text = ""
    
    for line in response.iter_lines(decode_unicode=True):
        if line:
            line_str = line if isinstance(line, str) else line.decode('utf-8', errors='ignore')
            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix
                if data_str == '[DONE]':
                    break
                try:
                    chunk = json.loads(data_str)
                    if 'candidates' in chunk and len(chunk['candidates']) > 0:
                        candidate = chunk['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    full_text += part['text']
                except json.JSONDecodeError:
                    continue
    
    # Return in the same format as non-streaming response
    return {
        'candidates': [{
            'content': {
                'parts': [{'text': full_text}]
            },
            'finishReason': 'STOP'
        }]
    }

# Set temp and codes directories outside the Agent365_2..0 folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMP_DIR = os.path.join(PARENT_DIR, "temp")
CODES_DIR = os.path.join(PARENT_DIR, "codes")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CODES_DIR, exist_ok=True)

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if API key is available
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")

def call_gemini(prompt, files=None, stream=False):
    """
    Calls the Gemini API with the given prompt and optional files.
    Returns the response text.
    
    Args:
        prompt (str): The prompt to send to Gemini
        files (dict, optional): Dictionary of filename: file_bytes pairs
        stream (bool): Whether to use streaming (default: False)
    """
    # Use the correct model name from the terminal output
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20"
    
    if stream:
        url = f"{base_url}:streamGenerateContent"
    else:
        url = f"{base_url}:generateContent"
    
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    # Build the parts array starting with the text prompt
    parts = [{"text": prompt}]
    
    # Add files if provided
    if files:
        for filename, file_bytes in files.items():
            # For now, we'll add file information as text since Gemini 2.5 Flash doesn't support file uploads
            # This is a limitation - we'll include file info in the prompt instead
            parts.append({"text": f"\n[File: {filename} - {len(file_bytes)} bytes]"})

    data = {
        "contents": [
            {
                "parts": parts
            }
        ]
    }
    
    # Add generation config to prevent token limit issues
    data["generationConfig"] = {
        "maxOutputTokens": 8192,  # Limit output tokens
        "temperature": 0.1,       # Lower temperature for more focused responses
        "topP": 0.8,
        "topK": 40
    }

    # Retry logic for network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Create a session with custom SSL context
            session = requests.Session()
            
            # Try different SSL configurations based on attempt
            if attempt == 0:
                # First attempt: Normal SSL verification
                session.verify = True
            elif attempt == 1:
                # Second attempt: Try with different SSL context
                session.verify = True
                session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            else:
                # Third attempt: Last resort - disable SSL verification (not recommended for production)
                print("Warning: Disabling SSL verification for final attempt")
                session.verify = False
            
            response = session.post(
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=60,
                stream=bool(stream)
            )
            
            if response.status_code != 200:
                error_msg = f"Gemini API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', response.text)}"
                except:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
            
            if stream:
                result = handle_streaming_response(response)
            else:
                result = response.json()
            break  # Success, exit retry loop
            
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                print(f"SSL Error (attempt {attempt + 1}/{max_retries}): {e}")
                continue
            else:
                raise Exception(f"SSL connection failed after {max_retries} attempts: {e}")
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                continue
            else:
                raise Exception("Gemini API request timed out after 60 seconds")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Network error (attempt {attempt + 1}/{max_retries}): {e}")
                continue
            else:
                raise Exception(f"Network error calling Gemini API after {max_retries} attempts: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    # Extract the generated text with better error handling
    try:
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            
            # Check finishReason - STOP is actually a successful completion
            finish_reason = candidate.get("finishReason", "UNKNOWN")
            if finish_reason == "SAFETY":
                raise Exception("Gemini API blocked the request due to safety concerns")
            elif finish_reason == "RECITATION":
                raise Exception("Gemini API detected recitation and blocked the request")
            elif finish_reason == "OTHER":
                raise Exception("Gemini API blocked the request for other reasons")
            # Note: STOP is a successful completion, not an error
            
            if "content" in candidate:
                content = candidate["content"]
                # Handle different response formats
                if "parts" in content and len(content["parts"]) > 0:
                    text = content["parts"][0]["text"]
                    if text and text.strip():
                        return text
                    else:
                        raise Exception(f"empty-response: Gemini returned empty text content (finishReason: {finish_reason})")
                elif "text" in content:
                    text = content["text"]
                    if text and text.strip():
                        return text
                    else:
                        raise Exception(f"empty-response: Gemini returned empty text content (finishReason: {finish_reason})")
                elif "role" in content and len(content) == 1:
                    # Empty response with only role
                    raise Exception(f"empty-response: Gemini returned empty response (finishReason: {finish_reason})")
                else:
                    raise Exception(f"Unexpected content structure: {content}")
            else:
                raise Exception(f"No content in candidate: {candidate}")
        else:
            raise Exception(f"No candidates in response: {result}")
    except Exception as e:
        # Bubble up a tagged empty-response for upstream retry handling
        message = str(e)
        if message.startswith("empty-response"):
            raise Exception(message)
        if "Unexpected" not in message and "Failed to parse" not in message:
            raise Exception(f"Gemini API Error: {message}. Response: {result}")
        else:
            raise Exception(f"Unexpected Gemini API response: {result}")


def install_dependencies(code):
    # Extract and install dependencies from code (very basic)
    import re
    pkgs = re.findall(r'import (\w+)', code) + re.findall(r'from (\w+) import', code)
    for pkg in set(pkgs):
        try:
            __import__(pkg)
        except ImportError:
            subprocess.run(["pip", "install", pkg])
