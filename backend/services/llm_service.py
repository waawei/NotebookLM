"""
LLM 服务 - 支持通义千问和 OpenAI
"""

from typing import Optional
from openai import OpenAI

from core.config import settings


class LLMService:
    """大语言模型服务"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        # 初始化客户端
        if self.provider == "dashscope":
            # 通义千问
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        elif self.provider == "openai":
            # OpenAI 或自定义 API
            if self.base_url:
                # 使用自定义 base_url（如 muyuan.do）
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            else:
                # 使用官方 OpenAI
                self.client = OpenAI(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate(self, prompt: str) -> str:
        """
        生成回答

        Args:
            prompt: 完整的 Prompt

        Returns:
            answer: LLM 生成的回答
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            print(f"LLM call failed: {e}")
            raise e

    async def generate_stream(self, prompt: str):
        """
        流式生成回答（用于打字机效果）

        Args:
            prompt: 完整的 Prompt

        Yields:
            chunk: 生成的文本片段
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            print(f"LLM streaming call failed: {e}")
            raise e
