"""
LLM Client — 封装 Kimi (Moonshot) API 调用
兼容 OpenAI SDK 格式，支持异步调用
"""
from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from config import settings


class LLMGenerationError(Exception):
    """LLM 生成失败时的统一异常"""
    pass


class LLMClient:
    """基于 Kimi / OpenAI 兼容 API 的异步 LLM 客户端"""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=60.0,
        )
        self.model = settings.llm_model_name
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    # ── 简报生成 ──────────────────────────────────────────────────────────────

    async def generate_briefing(
        self,
        events: List[Any],
        user_config: Dict[str, Any],
        sources_reference: List[Dict[str, Any]] = None,
    ) -> str:
        """
        基于事件列表和用户配置，调用 LLM 生成结构化情报简报（Markdown）。

        Args:
            events: IntelEvent 对象列表（需有 title, source, category, summary, relevance, url 等属性）
            user_config: 用户配置字典（industry, focus_targets, competitor_list 等）
            sources_reference: 信息来源参考列表

        Returns:
            完整的 Markdown 简报字符串
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(events, user_config, sources_reference)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = response.choices[0].message.content or ""
            # 去除可能的代码块包裹
            content = content.strip()
            if content.startswith("```markdown"):
                content = content[len("```markdown"):].strip()
            if content.startswith("```"):
                content = content[len("```"):].strip()
            if content.endswith("```"):
                content = content[:-len("```")].strip()
            return content

        except (APIError, APITimeoutError, RateLimitError) as e:
            raise LLMGenerationError(f"Kimi API error: {e}")
        except Exception as e:
            raise LLMGenerationError(f"Unexpected LLM error: {e}")

    # ── 对话 ──────────────────────────────────────────────────────────────────

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        通用对话接口，接收消息列表，返回模型回复。

        Args:
            messages: OpenAI 格式的消息列表，如 [{"role": "system", "content": "..."}, ...]

        Returns:
            模型回复文本
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content or ""
        except (APIError, APITimeoutError, RateLimitError) as e:
            raise LLMGenerationError(f"Kimi API error: {e}")
        except Exception as e:
            raise LLMGenerationError(f"Unexpected LLM error: {e}")

    # ── Prompt 构建 ───────────────────────────────────────────────────────────

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "你是一位顶级战略情报分析师，服务于企业高管决策支持系统。"
            "你的任务是基于实时采集的情报事件，撰写一份结构化、专业、可执行的情报简报。\n\n"
            "## 输出要求\n"
            "- 语言：中文（专业、简洁、避免口语化）\n"
            "- 格式：Markdown\n"
            "- 必须包含以下章节（严格使用指定的 ## 标题）：\n"
            "  1. ## 核心摘要 — 150字以内，概括当日最关键的情势判断和风险等级\n"
            "  2. ## 📡 关键事件监测 — 列出 3-7 个核心事件，每条包含标题、来源、摘要，如有关联原始链接请标注\n"
            "  3. ## 🔍 多维度分析 — 按事件类别（地缘政治/市场/政策/竞品/舆情/产品/法律等）分别给出深度洞察\n"
            "  4. ## ⚠️ 风险评估 — 用 Markdown 表格呈现，评级列使用 🔴 高风险 / 🟡 中等风险 / 🟢 低风险 标识\n"
            "  5. ## 💡 决策建议 — 给出 3 条具体、可执行的建议，标注时间维度（短期 24-48h / 中期 1-2周 / 长期 1-3月）\n"
            "  6. ## 📎 信息来源参考 — 列出主要信息来源，供查验\n\n"
            "## 约束\n"
            "- 严格基于提供的事件数据进行分析，不要编造不存在的事件或数据\n"
            "- 风险评估必须有具体依据，不能泛泛而谈\n"
            "- 决策建议必须 actionable，避免空洞的口号式表述\n"
            "- 信息置信度要诚实标注，不确定的信息明确说明\n"
            "- 不要在回复外层包裹 ```markdown 代码块"
        )

    @staticmethod
    def _build_user_prompt(
        events: List[Any],
        user_config: Dict[str, Any],
        sources_reference: Optional[List[Dict[str, Any]]],
    ) -> str:
        industry = user_config.get("industry") or "综合"
        focus_targets = user_config.get("focus_targets") or []
        competitors = user_config.get("competitor_list") or []
        product_keywords = user_config.get("product_keywords") or []
        social_keywords = user_config.get("social_keywords") or []

        # 用户画像
        profile_lines = [f"- 行业：{industry}"]
        if focus_targets:
            profile_lines.append(f"- 关注目标：{', '.join(focus_targets)}")
        if competitors:
            profile_lines.append(f"- 主要竞争对手：{', '.join(competitors)}")
        if product_keywords:
            profile_lines.append(f"- 产品关键词：{', '.join(product_keywords)}")
        if social_keywords:
            profile_lines.append(f"- 社交媒体监测词：{', '.join(social_keywords)}")
        profile_text = "\n".join(profile_lines)

        # 事件列表
        event_lines = []
        for i, ev in enumerate(events[:15], 1):  # 最多取 15 条
            title = getattr(ev, "title", "") or ev.get("title", "") if isinstance(ev, dict) else getattr(ev, "title", "")
            source = getattr(ev, "source", "") or ev.get("source", "") if isinstance(ev, dict) else getattr(ev, "source", "")
            category = getattr(ev, "category", "") or ev.get("category", "") if isinstance(ev, dict) else getattr(ev, "category", "")
            summary = getattr(ev, "summary", "") or ev.get("summary", "") if isinstance(ev, dict) else getattr(ev, "summary", "")
            relevance = getattr(ev, "relevance", 0) or ev.get("relevance", 0) if isinstance(ev, dict) else getattr(ev, "relevance", 0)
            url = getattr(ev, "url", "") or ev.get("url", "") if isinstance(ev, dict) else getattr(ev, "url", "")

            line = f"{i}. [{category}] {title}（来源：{source}，相关度：{relevance:.0%}）\n   摘要：{summary[:200]}"
            if url:
                line += f"\n   链接：{url}"
            event_lines.append(line)

        events_text = "\n\n".join(event_lines) if event_lines else "今日未监测到显著事件。"

        # 信息来源参考
        sources_text = ""
        if sources_reference:
            ref_lines = []
            for src in sources_reference:
                cat = src.get("category", "综合")
                refs = src.get("references", [])
                if refs:
                    ref_lines.append(f"- {cat}：" + " / ".join([f"{r.get('name', '')} ({r.get('url', '')})" for r in refs[:3]]))
            if ref_lines:
                sources_text = "\n".join(ref_lines)

        prompt = f"""# 用户画像
{profile_text}

# 今日采集事件（共 {len(events)} 条，已按相关度筛选）
{events_text}
"""
        if sources_text:
            prompt += f"\n# 信息来源参考\n{sources_text}\n"

        prompt += "\n请基于以上信息，撰写今日情报简报。"
        return prompt
