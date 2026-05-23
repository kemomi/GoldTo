"""
MemoryManager — Agent memory management.
Supports Zep Cloud for persistent long-term memory,
with automatic fallback to in-process memory store.
"""
from __future__ import annotations
import time
from collections import defaultdict
from typing import Optional


class MemoryManager:
    """
    Manages agent memories.
    - If ZEP_API_KEY is configured, uses Zep Cloud for persistent memory.
    - Otherwise, uses a simple in-process sliding-window store.
    """

    _MAX_SHORT_TERM = 20   # messages per agent in short-term window

    def __init__(self):
        from config import settings
        self._zep_key = (settings.zep_api_key or "").strip()
        self._zep_client = None
        self._store: dict[str, list[dict]] = defaultdict(list)

        if self._zep_key:
            try:
                from zep_cloud.client import AsyncZep
                self._zep_client = AsyncZep(api_key=self._zep_key)
                print("[Memory] Zep Cloud 已连接")
            except ImportError:
                print("[Memory] zep-cloud 未安装，退回内存模式")
            except Exception as e:
                print(f"[Memory] Zep 连接失败 ({e})，退回内存模式")
        else:
            print("[Memory] 使用内存模式（无 Zep API Key）")

    # ── Public API ────────────────────────────────────────────────────────────

    async def init_agent(self, agent_id: str, metadata: dict) -> None:
        """Initialise a memory session for an agent."""
        if self._zep_client:
            try:
                await self._zep_client.memory.add_session(
                    session_id=agent_id,
                    metadata=metadata,
                )
            except Exception:
                pass  # Session may already exist
        # Always initialise local store
        if agent_id not in self._store:
            self._store[agent_id] = []

    async def add_memory(self, agent_id: str, role: str, content: str) -> None:
        """Add a message to an agent's memory."""
        message = {
            "role": role,
            "content": content,
            "ts": time.time(),
        }

        if self._zep_client:
            try:
                from zep_cloud.types import Message
                await self._zep_client.memory.add(
                    session_id=agent_id,
                    messages=[Message(role_type=role, content=content)],
                )
            except Exception:
                pass  # Fallback to local on any error

        # Always maintain local copy (sliding window)
        self._store[agent_id].append(message)
        if len(self._store[agent_id]) > self._MAX_SHORT_TERM:
            self._store[agent_id] = self._store[agent_id][-self._MAX_SHORT_TERM:]

    async def get_memory(self, agent_id: str, last_n: int = 6) -> list[dict]:
        """Retrieve recent memory for an agent."""
        if self._zep_client:
            try:
                result = await self._zep_client.memory.get(session_id=agent_id)
                messages = result.messages or []
                return [
                    {"role": m.role_type, "content": m.content}
                    for m in messages[-last_n:]
                ]
            except Exception:
                pass  # Fallback to local

        local = self._store.get(agent_id, [])
        return [
            {"role": m["role"], "content": m["content"]}
            for m in local[-last_n:]
        ]

    async def get_summary(self, agent_id: str) -> str:
        """Get a condensed summary of an agent's memory (Zep feature)."""
        if self._zep_client:
            try:
                result = await self._zep_client.memory.get(session_id=agent_id)
                return result.summary.content if result.summary else ""
            except Exception:
                pass

        # Fallback: concatenate last few messages
        messages = await self.get_memory(agent_id, last_n=4)
        return " | ".join(m["content"][:60] for m in messages)

    def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear memory for one agent or all agents."""
        if agent_id:
            self._store.pop(agent_id, None)
        else:
            self._store.clear()
