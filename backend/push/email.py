"""
SMTP 邮件推送服务
"""
from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Any

from push.base import PushService, PushResult


class EmailPushService(PushService):
    """通过 SMTP 发送邮件推送。"""
    channel_name = "email"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        required = ["email_smtp_host", "email_smtp_user", "email_smtp_pass", "email"]
        return all(config.get(k) for k in required)

    async def send(self, title: str, content: str, config: Dict[str, Any]) -> PushResult:
        if not self.validate_config(config):
            return PushResult(
                success=False,
                channel=self.channel_name,
                message="邮件配置不完整",
            )

        try:
            host = config["email_smtp_host"]
            port = config.get("email_smtp_port", 587)
            user = config["email_smtp_user"]
            password = config["email_smtp_pass"]
            sender = config.get("email_sender") or user
            receiver = config["email"]

            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(title, "utf-8")
            msg["From"] = sender
            msg["To"] = receiver

            # 同时发送纯文本和 HTML 版本
            text_part = MIMEText(self._strip_markdown(content), "plain", "utf-8")
            html_part = MIMEText(self._markdown_to_html(content), "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(sender, [receiver], msg.as_string())

            return PushResult(
                success=True,
                channel=self.channel_name,
                message="邮件发送成功",
                detail={"to": receiver, "subject": title},
            )

        except Exception as e:
            return PushResult(
                success=False,
                channel=self.channel_name,
                message=f"邮件发送失败: {str(e)}",
            )

    def _strip_markdown(self, text: str) -> str:
        """简单去除 Markdown 标记，生成纯文本摘要。"""
        import re
        text = re.sub(r"#+\s*", "", text)
        text = re.sub(r"\*\*|__", "", text)
        text = re.sub(r"\*|_", "", text)
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "[图片]", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*+]\s*", "• ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\|\s*", "", text, flags=re.MULTILINE)
        return text.strip()

    def _markdown_to_html(self, text: str) -> str:
        """简单的 Markdown 转 HTML（MVP 阶段，后续可接入 markdown 库）。"""
        import re
        html = text

        # 代码块
        html = re.sub(r"```(\w+)?\n(.*?)```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # 标题
        html = re.sub(r"^######\s*(.+)$", r"<h6>\1</h6>", html, flags=re.MULTILINE)
        html = re.sub(r"^#####\s*(.+)$", r"<h5>\1</h5>", html, flags=re.MULTILINE)
        html = re.sub(r"^####\s*(.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
        html = re.sub(r"^###\s*(.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^##\s*(.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^#\s*(.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # 粗体、斜体
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"__(.+?)__", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # 链接
        html = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', html)

        # 引用
        html = re.sub(r"^>\s*(.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

        # 列表
        html = re.sub(r"^\s*[-*+]\s*(.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # 段落
        paragraphs = html.split("\n\n")
        html = "\n".join(f"<p>{p.strip()}</p>" if not p.strip().startswith("<") else p for p in paragraphs)

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body style="font-family:Inter,sans-serif;line-height:1.6;color:#333;max-width:720px;margin:0 auto;padding:20px;">
{html}
</body></html>"""
