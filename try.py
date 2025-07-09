import google.generativeai as genai
import os
import pprint # For pretty printing the model details

# Configure the API key. The SDK automatically picks it up from the GOOGLE_API_KEY environment variable.
# Alternatively, you can pass it directly:
# genai.configure(api_key="YOUR_ACTUAL_API_KEY_HERE")
genai.configure(api_key='AIzaSyCLuL_iLynn9A7hUi0nymdqtwMYO-pYXM0')

print("Attempting to list available Gemini models for your API key...\n")

try:
    # Use genai.list_models() to get an iterable of available models
    for m in genai.list_models():
        # Models often have a 'supported_generation_methods' attribute.
        # 'generateContent' is the common method for text and multimodal generation.
        if "generateContent" in m.supported_generation_methods:
            print(f"Model Name: {m.name}")
            print(f"  Display Name: {m.display_name}")
            print(f"  Description: {m.description}")
            print(f"  Input Token Limit: {m.input_token_limit}")
            print(f"  Output Token Limit: {m.output_token_limit}")
            print(f"  Supported Methods: {m.supported_generation_methods}")
            # You can uncomment the line below to see all available attributes for each model
            # pprint.pprint(m)
            print("-" * 30)

except Exception as e:
    print(f"An error occurred: {e}")
    print("\nPlease ensure your API key is correctly set as an environment variable named 'GOOGLE_API_KEY'")
    print("or passed directly to genai.configure(api_key='YOUR_API_KEY').")
    print("Also, check your internet connection and API key validity.")