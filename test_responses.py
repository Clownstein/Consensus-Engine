import asyncio
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
load_dotenv()

async def test():
    client = AsyncOpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5.1-codex-mini")
    print(f"Testing model: {model}")
    
    response = await client.responses.create(
        model=model,
        instructions="You are a JSON generator. Output valid JSON.",
        input="Output a JSON object with 'message' set to 'hi json'.",
        text={
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "greeting",
                    "strict": False,
                    "schema": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": ["message"]
                    }
                }
            }
        }
    )
    
    print("Responses output text:")
    try:
        content = response.output[0].content[0].text
        print(content)
        print(json.loads(content))
    except Exception as e:
        print("Failed to parse output:", e)
        print(response)

asyncio.run(test())
