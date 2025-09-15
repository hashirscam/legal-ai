from openai import OpenAI, AsyncOpenAI
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(prompt):    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content

async def call_llm_async(prompt):
    """Async version of call_llm for true parallel execution"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    client = AsyncOpenAI(api_key=api_key)
    r = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content
    
if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
