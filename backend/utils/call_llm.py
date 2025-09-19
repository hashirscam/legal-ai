from openai import OpenAI, AsyncOpenAI
import os
from dotenv import load_dotenv
import asyncio
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import get_llm_config

# Load environment variables from backend/.env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def call_llm(prompt):    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    config = get_llm_config()
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content

async def call_llm_async(prompt):
    """Async version of call_llm for true parallel execution"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    config = get_llm_config()
    client = AsyncOpenAI(api_key=api_key)
    r = await client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content
    
if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
