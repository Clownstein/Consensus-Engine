import asyncio
import inspect
import openai
import sys
from dotenv import load_dotenv
load_dotenv()

async def test():
    client = openai.AsyncOpenAI(api_key="dummy")
    
    # Just inspect the types
    from openai.types.response import Response
    print(dir(Response))
    print(Response.model_fields.keys())

asyncio.run(test())
