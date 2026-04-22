from __future__ import annotations

import io
import os
import re

import fitz
import requests

_nltk_ready = False


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    _nltk_ready = True


def _get_summarizer(algorithm: str = "lsa"):
    if algorithm == "lsa":
        from sumy.summarizers.lsa import LsaSummarizer
        return LsaSummarizer()
    elif algorithm == "luhn":
        from sumy.summarizers.luhn import LuhnSummarizer
        return LuhnSummarizer()
    elif algorithm == "text-rank":
        from sumy.summarizers.text_rank import TextRankSummarizer
        return TextRankSummarizer()
    else:
        from sumy.summarizers.lsa import LsaSummarizer
        return LsaSummarizer()


def _is_meaningful_text(text: str, min_words: int = 10) -> bool:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return len(cleaned.split()) >= min_words


def summarize_page_text(text: str, sentences_count: int = 3, algorithm: str = "lsa") -> str | None:
    _ensure_nltk()

    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.nlp.stemmers import Stemmer

    language = "english"

    try:
        parser = PlaintextParser.from_string(text, Tokenizer(language))
        summarizer = _get_summarizer(algorithm)
        summarizer.stop_words = None
        summarizer.stem_word = Stemmer(language)

        sentences = summarizer(parser.document, sentences_count)
        if not sentences:
            return None
        return " ".join(str(s) for s in sentences)
    except Exception:
        # sumy had a stroke
        return text[:500].strip() + ("..." if len(text) > 500 else "")


def _call_groq(compressed_tokens: str, api_key: str, model: str) -> str | None:
    if not api_key:
        return None

    # don't nuke the API
    if len(compressed_tokens) > 12000:
        compressed_tokens = compressed_tokens[:12000] + "..."

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a document summarization expert. "
                    "The user will provide extracted keywords and key sentences from a PDF document. "
                    "Write a well-structured, readable summary using markdown formatting:\n"
                    "- Use ## for section headings to break the summary into logical parts\n"
                    "- Use **bold** for key terms, names, and important concepts\n"
                    "- Use *italic* for emphasis, definitions, and clarifications\n"
                    "- Use __underline__ (double underscore) for critical keywords that are central to the document\n"
                    "- Use bullet points for listing multiple related items\n"
                    "- Keep paragraphs short and scannable\n"
                    "Be concise but thorough. Make it easy to skim."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Here are the most critical extracted keywords and sentences from a long document. "
                    "Write a well-structured, formatted summary with headings, bold keywords, "
                    "italic emphasis, and underlined critical terms:\n\n"
                    f"{compressed_tokens}"
                ),
            },
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # groq said no lol
        print(f"[groq] request failed: {e}")
        return None


def summarize_pdf(
    buffer: io.BytesIO,
    sentences_per_page: int = 3,
    algorithm: str = "lsa",
    mode: str = "llama",
    progress_callback=None,
) -> dict:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    total_pages = doc.page_count
    results = []
    all_text_parts = []

    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    use_groq = mode in ("llama", "both") and bool(api_key)

    try:
        # sumy pre-chews everything
        for i in range(total_pages):
            page = doc[i]
            raw_text = page.get_text()

            if _is_meaningful_text(raw_text):
                summary = summarize_page_text(
                    raw_text,
                    sentences_count=sentences_per_page,
                    algorithm=algorithm,
                )
                results.append({
                    "page": i + 1,
                    "summary": summary,
                    "has_text": True,
                    "word_count": len(raw_text.split()),
                })
                if summary:
                    all_text_parts.append(f"[Page {i + 1}] {summary}")
            else:
                results.append({
                    "page": i + 1,
                    "summary": None,
                    "has_text": False,
                    "warning": "No text found on this page (possibly scanned/image).",
                })

            if progress_callback:
                progress_callback(i + 1, total_pages)

        compressed = "\n".join(all_text_parts)
        overall_summary = None
        engine_used = "local"

        if _is_meaningful_text(compressed, min_words=15):
            if use_groq:
                # feed compressed crumbs to AI
                overall_summary = _call_groq(compressed, api_key, model)
                if overall_summary:
                    engine_used = "llama"

            # AI ghosted, sumy takes over
            if not overall_summary:
                overall_summary = summarize_page_text(
                    compressed,
                    sentences_count=min(sentences_per_page * 2, 10),
                    algorithm=algorithm,
                )
                engine_used = "local"

        if mode == "llama" and use_groq and overall_summary and engine_used == "llama":
            for r in results:
                if r.get("has_text") and r.get("summary"):
                    r["engine"] = "llama"
                else:
                    r["engine"] = "none"
        else:
            for r in results:
                r["engine"] = "local" if r.get("has_text") else "none"

        return {
            "pages": results,
            "total_pages": total_pages,
            "overall_summary": overall_summary,
            "engine_used": engine_used,
        }
    finally:
        doc.close()