def text_to_speech_synth(text: str, lang: str = "en") -> dict:
    return {
        "text": text,
        "language": lang,
        "status": "ready",
        "audio_format": "web_speech_api"
    }
