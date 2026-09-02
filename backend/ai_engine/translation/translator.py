import os
import re
import time
from dotenv import load_dotenv

load_dotenv(override=True)

LANG_MAP = {
    "hi": "hindi",
    "te": "telugu",
    "ta": "tamil",
    "kn": "kannada",
    "ml": "malayalam",
    "bn": "bengali",
    "mr": "marathi",
    "gu": "gujarati",
    "pa": "punjabi",
    "ur": "urdu",
    "fr": "french",
    "de": "german",
    "es": "spanish",
    "ar": "arabic",
    "en": "english"
}

LANG_NAMES = {
    "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada",
    "ml": "Malayalam", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati",
    "pa": "Punjabi", "ur": "Urdu", "fr": "French", "de": "German",
    "es": "Spanish", "ar": "Arabic", "en": "English"
}


def _split_sentences(text: str, max_len: int = 1200) -> list:
    """Split text into chunks at sentence boundaries, each under max_len chars."""
    sentences = re.split(r"(?<=[.!?।])\s+", text)
    chunks = []
    current = ""
    for s in sentences:
        # Hard-split any single sentence longer than max_len
        while len(s) > max_len:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(s[:max_len])
            s = s[max_len:]
        if len(current) + len(s) + 1 > max_len:
            if current:
                chunks.append(current)
            current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        chunks.append(current)
    return chunks if chunks else [text[:max_len]]


def _is_error_output(text: str) -> bool:
    """Detect garbage returned by failing free-translation endpoints."""
    if not text or not text.strip():
        return True
    lowered = text.lower()
    return ("error 500" in lowered
            or "server error" in lowered
            or "that’s an error" in lowered
            or "that's an error" in lowered
            or "please try again later" in lowered
            or "<html" in lowered)


def _translate_openai(chunks: list, lang_name: str) -> str:
    """Translate using OpenAI gpt-4o-mini (primary, reliable)."""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not api_key:
        raise RuntimeError("no openai key")

    import requests
    out = []
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for i, chunk in enumerate(chunks):
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content":
                    f"You are a professional legal translator. Translate the following legal document "
                    f"text into {lang_name}. Preserve meaning, clause structure, numbering, dates, "
                    f"names, and monetary amounts exactly. Output ONLY the translation, no explanations."},
                {"role": "user", "content": chunk}
            ],
            "temperature": 0.1
        }
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            ans = r.json()["choices"][0]["message"]["content"]
            if ans and ans.strip():
                out.append(ans.strip())
                continue
        raise RuntimeError(f"openai http {r.status_code}")
    return "\n".join(out)


def _translate_google_free(chunks: list, lang: str) -> str:
    """Fallback: deep_translator with sentence-boundary chunks, retries, error detection."""
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source="auto", target=lang)
    out = []
    for chunk in chunks:
        result = None
        for attempt in range(3):
            try:
                result = translator.translate(chunk)
                if not _is_error_output(result):
                    break
            except Exception:
                result = None
            time.sleep(1.5 * (attempt + 1))
        if result is None or _is_error_output(result):
            raise RuntimeError(f"google free translation failed for chunk ({len(chunk)} chars)")
        out.append(result)
        time.sleep(0.5)  # avoid rate-limiting between chunks
    return "\n".join(out)


def translate(text: str, target_language: str) -> dict:
    try:
        code = target_language.lower().strip()
        lang = LANG_MAP.get(code, code)
        lang_name = LANG_NAMES.get(code, code.capitalize())

        if not text or not text.strip():
            return {"translated_text": "", "target_language": target_language,
                    "status": "error", "provider": "none"}

        chunks = _split_sentences(text.strip())
        provider = None

        # 1. Primary: OpenAI LLM translation
        try:
            translated_text = _translate_openai(chunks, lang_name)
            provider = "openai"
        except Exception as e:
            print(f"[TRANSLATE] OpenAI failed: {e}")

        # 2. Fallback: deep_translator with hardening
        if provider is None:
            try:
                translated_text = _translate_google_free(chunks, lang)
                provider = "google_free"
            except Exception as e:
                print(f"[TRANSLATE] Google free failed: {e}")

        if provider is None:
            return {
                "translated_text": (
                    "Translation is currently unavailable. Please check your internet connection "
                    "or OPENAI_API_KEY configuration in .env."
                ),
                "target_language": target_language,
                "status": "error",
                "provider": "none"
            }

        return {
            "translated_text": translated_text,
            "target_language": code,
            "status": "success",
            "provider": provider
        }
    except Exception as e:
        return {
            "translated_text": f"Error translating text: {str(e)}",
            "target_language": target_language,
            "status": "error",
            "provider": "none"
        }
