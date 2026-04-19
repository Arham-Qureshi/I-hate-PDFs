from __future__ import annotations

import io
import os
import re

import fitz
import requests

_nltk_ready = False

# groq endpoint
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
        # sumy choked, truncate
        return text[:500].strip() + ("..." if len(text) > 500 else "")


def _call_groq(compressed_tokens: str, api_key: str, model: str) -> str | None:
    if not api_key:
        return None

    # cap the payload so we dont blow token limits
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
                    "Write a clear, comprehensive summary capturing the core ideas. "
                    "Be concise but thorough. Use plain language."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Here are the most critical extracted keywords and sentences from a long document. "
                    "Write a clear, comprehensive summary of the document capturing these core ideas:\n\n"
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
        # groq failed, fall back to None
        print(f"[groq] request failed: {e}")
        return None


def summarize_pdf(buffer: io.BytesIO, sentences_per_page: int = 3, algorithm: str = "lsa", progress_callback=None) -> dict:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    total_pages = doc.page_count
    results = []
    all_text_parts = []

    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    try:
        for i in range(total_pages):
            page = doc[i]
            raw_text = page.get_text()

            if _is_meaningful_text(raw_text):
                summary = summarize_page_text(raw_text, sentences_count=sentences_per_page, algorithm=algorithm)
                results.append({
                    "page": i + 1,
                    "summary": summary,
                    "has_text": True,
                    "word_count": len(raw_text.split()),
                })
                # feed pages as token chunks xD
                if summary:
                    all_text_parts.append(summary)
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

        if _is_meaningful_text(compressed, min_words=15):
            # try groq first
            overall_summary = _call_groq(compressed, api_key, model)

            #local NLP if groq fails or no key
            if not overall_summary:
                overall_summary = summarize_page_text(
                    compressed,
                    sentences_count=min(sentences_per_page * 2, 10),
                    algorithm=algorithm,
                )

        return {
            "pages": results,
            "total_pages": total_pages,
            "overall_summary": overall_summary,
            "used_llama": overall_summary is not None and api_key != "",
        }
    finally:
        doc.close()
