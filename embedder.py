from openai import OpenAI
from typing import List, Union
from datetime import datetime
import os
import json
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

class OpenAIEmbeder:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('THEIR_GPT_API_KEY'))
        self.history_file = "embedding_history.json"
        spent = self.get_total_spent()
        print(f"Total spent on embeddings so far: ${spent:.6f}")

    def save_embedding_to_history(self, embedding: dict) -> None:
        return
        # Save embedding details to a JSON file for tracking
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(embedding)
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error saving embedding to history: {e}")

    def get_embedding(self, text: Union[str, List[str]], model: str = "text-embedding-3-small") -> dict:
        response = self.client.embeddings.create(
            model=model,
            input=text,
            encoding_format="float"
        )

        result = {
            "embedding_model": model,
            "embedding_size": len(response.data[0].embedding),
            "created_at": str(datetime.now()),
            "token_count": response.usage.total_tokens,
            "money_cost": response.usage.total_tokens * self.get_cost_per_model(model) / 1_000_000
        }
        self.save_embedding_to_history(result)

        result["embedding"] = response.data

        return result
    
    def get_cost_per_model(self, model: str = "text-embedding-3-small") -> float:
        model_costs = {
            "text-embedding-3-small": 0.02,  # cost per 1M tokens
            "text-embedding-3-large": 0.13,  # cost per 1M tokens
            "text-embedding-ada-002": 0.10   # cost per 1M tokens
        }
        return model_costs.get(model, 0.02)  # default to 0.02 if model not found
    
    def get_total_spent(self) -> float:
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                total_spent = sum(item.get("money_cost", 0) for item in history)
                return total_spent
            else:
                return 0.0
        except Exception as e:
            print(f"Error calculating total spent: {e}")
            return 0.0