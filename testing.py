import requests
import json

def chat_stream(prompt, session_id="default"):
    """
    Stream responses from the RAG API
    """
    url = "http://localhost:8000/chat/stream"
    
    payload = {
        "prompt": prompt,
        "session_id": session_id
    }
    
    
    response = requests.post(
        url,
        json=payload,
        stream=True,
        headers={"Accept": "text/event-stream"}
    )
    
    # Disable any buffering
    response.raw.decode_content = True
    
    for line in response.iter_lines(decode_unicode=True):
        if line:
            if line.startswith('data: '):
                data_str = line[6:]
                
                try:
                    data = json.loads(data_str)
                    
                    if 'text' in data:
                        print(data['text'], end="", flush=True)
                    elif 'done' in data:
                        print()  # New line when done
                    elif 'error' in data:
                        print(f"\nError: {data['error']}")
                        break
                
                except json.JSONDecodeError:
                    continue
    
    print("\n")


# Example usage
if __name__ == "__main__":
    while True:
        prompt = input("User: ")
        chat_stream(prompt, session_id="demo")
