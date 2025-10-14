# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()


class API():
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('MY_DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)

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
    
    def converse(self, messages: List[Dict[str, str]]):
        # Assert that last message is not from assistant
        assert messages[-1]['role'] != 'assistant', "Last message should not be from assistant"

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content

    def test_deepseek_api(self):
        # Initialize the OpenAI client with DeepSeek API key and base URL
        client = OpenAI(api_key=os.getenv('MY_DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Who are you?"},
            ],
            stream=False
        )

        print(response.choices[0].message.content)
        return response.choices[0].message.content
