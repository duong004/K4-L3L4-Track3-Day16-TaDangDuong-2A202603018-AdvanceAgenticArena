"""LỚP `citation_checker` — bài giảng Day 16, §11 (Grounding & Citations)."""

from __future__ import annotations

from harness.middleware import Middleware


def _norm(s: str) -> str:
    return " ".join(s.strip().split())


def _supports(lines: list[str], claim_text: str) -> bool:
    norm_claim = _norm(claim_text)
    if not norm_claim:
        return False
    return any(norm_claim in _norm(line) for line in lines if line.strip())


class CitationChecker(Middleware):
    """Trỏ mỗi claim về đúng tài liệu thật sự chứa câu đó."""

    name = "citation_checker"

    def after_agent(self, ctx, report):
        claims = report.get("claims")
        if not isinstance(claims, list) or not claims or not getattr(ctx, "corpus", None):
            return report

        obs_raw = getattr(ctx, "observed_text", "") or ""
        obs_norm = obs_raw.replace("\r\n", "\n")

        for claim in claims:
            if not isinstance(claim, dict) or "text" not in claim:
                continue
            text = claim["text"]
            if not text or not isinstance(text, str):
                continue

            doc_id = claim.get("doc_id")
            curr_doc = ctx.corpus.get(doc_id) if doc_id else None

            # 1. Kiểm tra tài liệu hiện tại đã đỡ claim chưa (theo chuẩn substring của 1 dòng)
            if curr_doc and curr_doc.body:
                curr_lines = curr_doc.body.replace("\r\n", "\n").splitlines()
                if _supports(curr_lines, text):
                    continue

            # 2. Tìm tài liệu thật trong corpus đã quan sát nguyên vẹn
            for doc in ctx.corpus.docs:
                if not doc.body:
                    continue
                doc_body_norm = doc.body.replace("\r\n", "\n")

                # Tài liệu phải nằm nguyên vẹn trong quan sát đã đọc
                if doc_body_norm.strip() in obs_norm or doc.body in obs_raw:
                    doc_lines = doc_body_norm.splitlines()
                    if _supports(doc_lines, text):
                        claim["doc_id"] = doc.doc_id
                        break

        # 3. Đồng bộ lại danh sách citations
        report["citations"] = sorted(
            set(c["doc_id"] for c in claims if isinstance(c, dict) and c.get("doc_id"))
        )
        return report