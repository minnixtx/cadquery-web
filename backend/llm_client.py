from openai import OpenAI
from typing import Optional


class LLMClient:
    """Client for OpenAI-compatible API endpoints (e.g., llama-server)."""

    def __init__(self, base_url: str, model: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.model = model
        api_key = api_key or "sk-placeholder"
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, messages: list[str], images: Optional[list[str]] = None) -> str:
        """Send a chat completion request and return the assistant's text response.

        Args:
            messages: List of messages in the conversation.
            images: Optional list of base64-encoded PNG images for vision input.

        Returns:
            The assistant's text response.
        """
        content = []

        for msg in messages:
            content.append({
                "type": "text",
                "text": msg
            })

        for img in (images or []):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img}",
                    "detail": "high"
                }
            })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=4096,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )

        return response.choices[0].message.content.strip()
