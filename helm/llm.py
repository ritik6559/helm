from openai import OpenAI

from config import BASE_URL, API_KEY, MODEL
from tools import TOOL_SCHEMAS

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

def call_llm(messages):
    response = client.chat.completions.create(
        model = MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS
    )

    output = response.choices[0].message
    completion_details = response.usage.completion_tokens_details
    prompt_details = response.usage.prompt_tokens_details

    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None)
    }

    return output, usage
