import io
import json
import os
import re
import fitz
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
QUIZ_MODEL = "openai/gpt-oss-120b"


def _is_meaningful(text: str, min_words: int = 10) -> bool:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return len(cleaned.split()) >= min_words


def _call_groq(text: str, api_key: str, num_questions: int) -> dict | None:
    if not api_key:
        print("[quiz-groq] no api key")
        return None

    # sadly, we dont own a LLM so use groq.
    if len(text) > 6000:
        text = text[:6000]

    prompt = (
        f"Extract {num_questions} key concepts from this text. "
        f"Return ONLY valid JSON, no markdown.\n"
        f'Format: {{"flashcards":[{{"term":"...","definition":"..."}}],'
        f'"questions":[{{"q":"...","options":["A","B","C","D"],"answer":"A"}}]}}\n\n'
        f"{text}"
    )

    payload = {
        "model": QUIZ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1500,
    }

    print(f"[quiz-groq] calling {QUIZ_MODEL}, {len(text)} chars, {num_questions}q")

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        print(f"[quiz-groq] status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[quiz-groq] error: {resp.text[:300]}")
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"].strip()

        # strips MD so its look readable
        if raw.startswith("```"):
            raw = re.sub(r'^```[a-zA-Z]*\n', '', raw)
            raw = re.sub(r'\n```$', '', raw)

        return json.loads(raw)
    except Exception as e:
        print(f"[quiz-groq] failed: {e}")
        return None


def generate_quiz(
    buffer: io.BytesIO,
    num_questions: int = 5,
    progress_callback=None,
) -> dict:
    buffer.seek(0)
    doc = fitz.open(stream=buffer.read(), filetype="pdf")
    total_pages = doc.page_count
    all_text_parts = []

    api_key = os.getenv("GROQ_API_KEY", "")

    try:
        for i in range(total_pages):
            page = doc[i]
            raw_text = page.get_text()

            if _is_meaningful(raw_text):
                all_text_parts.append(raw_text)

            if progress_callback:
                progress_callback(i + 1, total_pages)

        compressed = "\n".join(all_text_parts)

        quiz_data = None
        if api_key and _is_meaningful(compressed):
            quiz_data = _call_groq(compressed, api_key, num_questions)

        if not quiz_data:
            quiz_data = {"error": "Failed to generate quiz. Check API key or PDF text."}

        return {
            "quiz_data": quiz_data,
            "engine_used": "groq" if "error" not in quiz_data else "none",
        }
    finally:
        doc.close()
