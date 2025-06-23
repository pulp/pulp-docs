---
date: 2025-06-17T00:00:00Z
title: AI CLI Integration - An experiment
authors: 
  - ytrahnov
tags:
  - documentation
  - AI
---
# What Happens When You Add AI to Your Terminal? A Personal Experiment

## A Simple Idea

I wanted to try adding AI to a CLI tool to see how easy it would be. The idea was simple: instead of looking up command syntax, just ask the terminal in plain English.

<!-- more -->

## Building It

Here's the basic implementation using OpenAI's API, which than got ported to pulp-cli:

```python
import json
import click
import requests

@click.command()
@click.argument("question", type=str)
@click.option("--api-key", envvar="OPENAI_API_KEY", help="OpenAI API key")
@click.option("--model", default="gpt-3.5-turbo", help="ChatGPT model to use")
def ask(question, api_key, model):
    """Ask a question to ChatGPT and get a response."""
    
    if not api_key:
        raise click.ClickException("OpenAI API key is required")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 150,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        click.echo(answer)
        
    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"API request failed: {str(e)}")
    except (json.JSONDecodeError, KeyError):
        raise click.ClickException("Failed to parse API response")

if __name__ == "__main__":
    ask()
```

## Usage Examples

```bash
# Set your API key
export OPENAI_API_KEY="your-api-key-here"

# Ask questions
python3 openai.py "how do I list files in linux"
python3 openai.py "explain git rebase"

# Or pass the API key directly
python3 openai.py --api-key "your-key" "what is docker"
```

For Pulp CLI integration:
```bash
# Ask about repository management
pulp console chat ask "How do I create an RPM repository?"

# Get help with workflows
pulp console chat ask --model gpt-4.1 "How do I sync and publish content?"

# Troubleshooting
pulp console chat ask "Why is my sync failing with authentication errors?"
```

## How Easy It Is

It's straightforward to execute, using the OpenAI documentation. The actual implementation includes additional features like:

- Multiple output formats (JSON/text)
- Model selection options  
- Configurable response parameters
- Better error handling

You can add this to any CLI tool by:
1. Adding the chat command to your CLI framework
2. Setting up the OpenAI API integration
3. Handling API keys and error cases

The full implementation is available in the [Pulp CLI Console extension](https://github.com/pulp/pulp-cli-console) - check out <https://github.com/pulp/pulp-cli-console/blob/pulp-cli-ai-experiment/pulpcore/cli/console/chat.py>.
