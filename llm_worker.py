from queue import Queue
import requests

class LLMWorker:
    def __init__(self, llm_endpoint):
        self.llm_endpoint = llm_endpoint
        self.request_queue = Queue()
        self.response_queue = Queue()

    def enqueue_prompt(self, prompt):
        self.request_queue.put(prompt)

    def process_requests(self):
        while not self.request_queue.empty():
            prompt = self.request_queue.get()
            response = self.send_request(prompt)
            if response:
                self.response_queue.put(response)

    def send_request(self, prompt):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer YOUR_API_KEY'  # Replace with actual API key
            }
            payload = {
                'prompt': prompt
            }
            response = requests.post(self.llm_endpoint, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error sending request to LLM: {e}")
        return None

    def get_next_response(self):
        if not self.response_queue.empty():
            return self.response_queue.get()
        return None