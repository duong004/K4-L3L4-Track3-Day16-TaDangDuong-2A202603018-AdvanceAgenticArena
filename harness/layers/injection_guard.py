"""LỚP `injection_guard` — bài giảng Day 16, §10 (Prompt Injection Defense)."""

from __future__ import annotations

from arena.corpus import INJECTION_CANARY
from arena.tools import ToolResult
from harness.middleware import Middleware

#: Dấu mốc của đoạn nội dung không đáng tin trong kho tài liệu.
BLOCK_START = "--- LƯU Ý HỆ THỐNG"
BLOCK_END = "--- HẾT LƯU Ý HỆ THỐNG ---"
PLACEHOLDER = "[nội dung không đáng tin cậy đã bị loại bỏ]"


class InjectionGuard(Middleware):
    """Coi nội dung tài liệu là dữ liệu: cách ly nó, rồi soát lại câu trả lời."""

    name = "injection_guard"

    def wrap_tool_call(self, ctx, call, name, args):
        result = call(name, args)
        if not hasattr(result, "content") or not isinstance(result.content, str):
            return result

        content = result.content
        if BLOCK_START not in content:
            return result

        while BLOCK_START in content:
            start = content.find(BLOCK_START)
            end = content.find(BLOCK_END, start)
            if end != -1:
                content = content[:start] + PLACEHOLDER + content[end + len(BLOCK_END):]
            else:
                content = content[:start] + PLACEHOLDER
                break

        return ToolResult(ok=result.ok, content=content, error=result.error)

    def after_agent(self, ctx, report):
        answer = report.get("answer")
        if isinstance(answer, str) and INJECTION_CANARY in answer:
            report["answer"] = answer.replace(INJECTION_CANARY, "").strip()
        return report