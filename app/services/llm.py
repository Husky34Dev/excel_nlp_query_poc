import os
from groq import Groq

class GroqLLM:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "moonshotai/kimi-k2-instruct"

    def ask(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0,
            seed=42,
        )
        return response.choices[0].message.content.strip() # type: ignore
