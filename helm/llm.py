from openai import OpenAI

from config import BASE_URL, API_KEY, MODEL

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

user_input = input("Enter your prompt: ")

SYSTEM_PROMPT = "You are a helpful assistant."

response = client.chat.completions.create(
    model = MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]
)

output = response.choices[0].message.content
completion_details = response.usage.completion_tokens_details
prompt_details = response.usage.prompt_tokens_details

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
    "cached_tokens": getattr(prompt_details, "cached_tokens", None)
}

print("Agents: ", output)
print(usage)