"""
<<<<<<< HEAD
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
=======
Memory Manager — Zep Cloud with in-memory fallback.
If ZEP_API_KEY is empty, uses local dict as memory store.
"""
from __future__ import annotations
import time
from typing import Optional
from config import settings


class MemoryManager:
    def __init__(self):
        self._use_zep = bool(settings.zep_api_key)
        self._local: dict[str, list[dict]] = {}
        self._zep_client = None

        if self._use_zep:
            try:
                from zep_cloud.client import AsyncZep
                self._zep_client = AsyncZep(api_key=settings.zep_api_key)
                print("[Memory] Using Zep Cloud for agent memories")
            except Exception as e:
                print(f"[Memory] Zep init failed ({e}), falling back to in-memory")
                self._use_zep = False
        else:
            print("[Memory] Using in-memory storage (set ZEP_API_KEY for persistent memory)")

    # ── public API ──────────────────────────────────────────────────────────

    async def add_memory(self, agent_id: str, role: str, content: str) -> None:
        if self._use_zep:
            await self._zep_add(agent_id, role, content)
        else:
            self._local.setdefault(agent_id, [])
            self._local[agent_id].append({
                "role": role,
                "content": content,
                "ts": time.time(),
            })

    async def get_memory(self, agent_id: str, limit: int = 10) -> str:
        if self._use_zep:
            return await self._zep_get(agent_id, limit)
        records = self._local.get(agent_id, [])
        recent = records[-limit:]
        if not recent:
            return "（暂无记忆）"
        return "\n".join(f"[{r['role']}] {r['content']}" for r in recent)

    async def init_agent(self, agent_id: str, metadata: Optional[dict] = None) -> None:
        if self._use_zep:
            try:
                await self._zep_client.user.add(user_id=agent_id, metadata=metadata or {})
            except Exception:
                pass
        else:
            self._local.setdefault(agent_id, [])

    # ── Zep helpers ─────────────────────────────────────────────────────────

    async def _zep_add(self, agent_id: str, role: str, content: str) -> None:
        from zep_cloud.types import Message
        try:
            await self._zep_client.memory.add(
                session_id=agent_id,
                messages=[Message(role=role, role_type="user", content=content)],
            )
        except Exception as e:
            print(f"[Zep] add_memory error: {e}")

    async def _zep_get(self, agent_id: str, limit: int) -> str:
        try:
            result = await self._zep_client.memory.get(session_id=agent_id)
            msgs = result.messages or []
            recent = msgs[-limit:]
            return "\n".join(f"[{m.role}] {m.content}" for m in recent)
        except Exception as e:
            print(f"[Zep] get_memory error: {e}")
            return "（记忆读取失败）"
>>>>>>> kemomi/main
