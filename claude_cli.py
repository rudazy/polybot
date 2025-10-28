"""
Simple Claude CLI tool
Usage: python claude_cli.py "your question here"
"""

import sys
from anthropic import Anthropic

# Your API key (get from https://console.anthropic.com)
API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual key

def ask_claude(question):
    """Ask Claude a question"""
    client = Anthropic(api_key=API_KEY)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": question}
        ]
    )
    
    return message.content[0].text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python claude_cli.py 'your question here'")
    else:
        question = " ".join(sys.argv[1:])
        response = ask_claude(question)
        print(response)