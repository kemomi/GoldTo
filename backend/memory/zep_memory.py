"""
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
