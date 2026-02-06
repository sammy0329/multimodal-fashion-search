"""OpenAI GPT 클라이언트 서비스.

GPT-4o-mini 기반 텍스트 생성 (동기/스트리밍) 기능을 제공한다.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from functools import partial
from typing import Any

logger = logging.getLogger(__name__)


class LLMService:
    """OpenAI GPT API 호출 서비스.

    Args:
        api_key: OpenAI API 키.
        model: 모델 ID (기본 gpt-4o-mini).
        max_tokens: 최대 생성 토큰 수.
        temperature: 생성 온도 (낮을수록 결정론적).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._client: Any = None

        if api_key:
            import openai

            self._client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트 초기화 완료 (model=%s)", model)
        else:
            logger.warning("OpenAI API 키가 설정되지 않았습니다")

    def _generate_sync(self, system_prompt: str, user_message: str) -> str:
        """OpenAI Chat Completions API 동기 호출.

        Args:
            system_prompt: 시스템 프롬프트.
            user_message: 사용자 메시지.

        Returns:
            생성된 텍스트.

        Raises:
            RuntimeError: 클라이언트 미초기화 또는 API 오류 시.
        """
        if self._client is None:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다")

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    async def generate(self, system_prompt: str, user_message: str) -> str:
        """LLM 텍스트 생성 (비동기).

        Args:
            system_prompt: 시스템 프롬프트.
            user_message: 사용자 메시지.

        Returns:
            생성된 텍스트.

        Raises:
            RuntimeError: API 호출 실패 시.
        """
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None,
                partial(self._generate_sync, system_prompt, user_message),
            )
        except Exception as exc:
            logger.error("LLM 생성 실패: %s", exc, exc_info=True)
            raise RuntimeError(f"LLM 호출 실패: {exc}") from exc

    async def generate_stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[str]:
        """LLM 텍스트 스트리밍 생성.

        Args:
            system_prompt: 시스템 프롬프트.
            user_message: 사용자 메시지.

        Yields:
            텍스트 청크.

        Raises:
            RuntimeError: 클라이언트 미초기화 시.
        """
        if self._client is None:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다")

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _stream_sync() -> None:
            try:
                stream = self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        loop.call_soon_threadsafe(queue.put_nowait, delta)
            except Exception as exc:
                logger.error("스트리밍 생성 실패: %s", exc, exc_info=True)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(None, _stream_sync)

        while True:
            chunk = await asyncio.wait_for(queue.get(), timeout=60.0)
            if chunk is None:
                break
            yield chunk
