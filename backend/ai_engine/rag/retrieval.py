import re

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "him",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "me", "more", "most",
    "my", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "would", "you", "your"
}

def retrieve(text: str, question: str, k: int = 5) -> list:
    if not text or not text.strip():
        return []

    # Clean question keywords (filter out stop words)
    q_words = set(re.findall(r"\b\w+\b", question.lower())) - STOP_WORDS
    if not q_words:
        q_words = set(re.findall(r"\b\w+\b", question.lower()))

    # Split document into paragraph/section chunks as well as sentence chunks
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    all_chunks = paragraphs + [s for s in sentences if s not in paragraphs]

    def score_chunk(chunk: str) -> float:
        chunk_words = set(re.findall(r"\b\w+\b", chunk.lower()))
        matches = q_words & chunk_words
        if not matches:
            return 0.0
        # Give higher weight to matches and moderate length chunks
        return len(matches) * 2.0 + (1.0 if 30 <= len(chunk.split()) <= 200 else 0.5)

    ranked = sorted(all_chunks, key=score_chunk, reverse=True)
    top_chunks = [c for c in ranked if score_chunk(c) > 0][:k]

    # If no specific matches found, return top paragraphs
    if not top_chunks:
        top_chunks = paragraphs[:k] if paragraphs else sentences[:k]

    return top_chunks
