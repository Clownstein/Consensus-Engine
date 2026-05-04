import inspect
import openai
from openai.resources import responses

print(inspect.signature(openai.AsyncOpenAI().responses.create))
