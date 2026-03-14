from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

hf_token = "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"
client = InferenceClient(token=hf_token)


def generate_text(prompt, max_tokens=200):
    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="Qwen/Qwen2.5-72B-Instruct",
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"LLM Error: {e}")
        return "AI insight generation failed."