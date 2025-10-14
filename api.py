# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()


class API():
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('MY_DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")
        self.conversation_token_history = []  # I was thinking later use this to put on a graph or something

    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)

    def add_user_prompt(self, prompt: str, messages: list):
        messages.append({"role": "user", "content": prompt})
    
    def add_system_prompt(self, system: str, messages: list):
        messages.append({"role": "system", "content": system})
    
    def add_assistant_prompt(self, prompt: str, messages: list):
        messages.append({"role": "assistant", "content": prompt})

    def check_limit(self, messages, limit):
        if len(messages) > limit:
            messages.pop(1) # user
            messages.pop(1) # assistant

    def call(self, prompt: str, system: str = "You are a helpful assistant"):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        return response.choices[0].message.content
    
    def converse(self, messages: List[Dict[str, str]]) -> str:
        response: ChatCompletion = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        self.conversation_token_history.append({
            "cache_hit_tokens": response.usage.prompt_tokens_details.cached_tokens,
            "cache_miss_tokens": response.usage.prompt_tokens - response.usage.prompt_tokens_details.cached_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        })
        return response.choices[0].message.content


def conversation_cycle():
    api = API()
    messages = [
        {"role": "system", "content": "You are a helpful assistant"}
    ]
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        messages.append({"role": "user", "content": user_input})
        response = api.converse(messages)
        print("Assistant:", response)
        messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    conversation_cycle()