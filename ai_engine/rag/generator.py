import os
import re
import json
import requests
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore")

def _local_extractive_answer(question: str, doc_context: str, contexts: list) -> str:
    """Intelligent local legal QA engine that extracts direct answers, clauses, and key insights when external LLM keys are absent or unreachable."""
    q_lower = question.lower()
    
    intents = {
        "obligations": ["obligation", "duty", "must", "shall", "responsible", "agree", "requirement", "undertake", "duty of"],
        "payment": ["payment", "fee", "cost", "dollar", "$", "price", "remuneration", "compensation", "due", "invoice", "pay", "salary", "rate"],
        "termination": ["terminate", "termination", "cancel", "notice", "expire", "expiration", "breach", "renew", "end", "period of notice"],
        "liability": ["liable", "liability", "indemnity", "indemnify", "damage", "loss", "hold harmless", "warranty", "penalty"],
        "confidentiality": ["confidential", "privacy", "disclosure", "proprietary", "secret", "nondisclosure", "nda", "classified"],
        "governing_law": ["law", "jurisdiction", "court", "governing", "state", "arbitration", "dispute", "venue", "legal framework"],
        "duration": ["term", "duration", "period", "effective date", "validity", "month", "year", "date", "schedule"]
    }
    
    matched_intent = None
    for intent, keywords in intents.items():
        if any(kw in q_lower for kw in keywords):
            matched_intent = intent
            break
            
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc_context) if p.strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc_context) if s.strip()]
    
    q_terms = set(re.findall(r"\b\w{3,}\b", q_lower)) - {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how", 
        "this", "that", "there", "have", "with", "from", "contract", "agreement", 
        "document", "clause", "terms", "explain", "describe", "tell", "does", "is", "are"
    }
    
    scored_sentences = []
    for s in sentences:
        s_lower = s.lower()
        score = 0
        for term in q_terms:
            if term in s_lower:
                score += 2
        if matched_intent:
            for kw in intents[matched_intent]:
                if kw in s_lower:
                    score += 3
        if score > 0:
            scored_sentences.append((score, s))
            
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    best_sentences = []
    seen = set()
    for _, s in scored_sentences:
        if s not in seen:
            best_sentences.append(s)
            seen.add(s)
        if len(best_sentences) >= 4:
            break
            
    relevant_excerpts = []
    if contexts:
        for c in contexts[:3]:
            if c not in relevant_excerpts:
                relevant_excerpts.append(c)
    elif paragraphs:
        relevant_excerpts = paragraphs[:2]
        
    topic_labels = {
        "obligations": "Party Obligations & Requirements",
        "payment": "Payment Terms & Financial Obligations",
        "termination": "Termination & Cancellation Terms",
        "liability": "Liability, Indemnification & Risk Clauses",
        "confidentiality": "Confidentiality & Non-Disclosure Terms",
        "governing_law": "Governing Law & Dispute Resolution",
        "duration": "Agreement Duration & Timelines"
    }
    header_label = topic_labels.get(matched_intent, "Legal Document Analysis")
    
    lines = []
    # Generate a natural, LLM-like answer (no template tip when called as fallback - real LLM unavailable)
    lines = []
    # Direct, conversational answer style
    if best_sentences:
        lines.append(f"Based on the document ({header_label}):\n")
        for s in best_sentences:
            lines.append(f"{s}")
        lines.append("")
    else:
        first_para = paragraphs[0] if paragraphs else doc_context[:600]
        lines.append(first_para[:700])
        lines.append("")
        
    if relevant_excerpts:
        lines.append("Supporting excerpts from the document:")
        for exc in relevant_excerpts[:2]:
            clean_exc = exc.replace("\n", " ").strip()
            short_exc = clean_exc[:400] + ("..." if len(clean_exc) > 400 else "")
            lines.append(f"\"{short_exc}\"")
        lines.append("")
        
    lines.append("_Note: This is an extractive answer (no cloud LLM key detected). Add OPENAI_API_KEY via .env or the 🔑 button for full generative reasoning._")
    return "\n".join(lines)


def generate_answer(question: str, contexts: list, full_text: str = "", user_api_key: str = None) -> str:
    # Reload environment variables in case .env was recently updated (override ensures fresh .env)
    load_dotenv(override=True)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"), override=True)
    
    doc_context = ""
    if full_text and len(full_text.strip()) > 0:
        doc_context = full_text[:40000].strip()
    elif contexts:
        doc_context = "\n\n".join([f"Excerpt {i+1}:\n{c}" for i, c in enumerate(contexts)])
    else:
        return "I could not find relevant content in the provided legal document to answer your question."

    excerpt_str = ""
    if contexts:
        excerpt_str = "\n\nKEY RELEVANT EXCERPTS:\n" + "\n---\n".join(contexts[:5])

    system_prompt = (
        "You are an expert Legal AI Assistant specializing in contract law, compliance, and legal document analysis. "
        "You must answer the user's question DIRECTLY and CONCISELY using ONLY the provided legal document. "
        "Rules:\n"
        "1. Start with a direct answer to the question in 1-2 sentences.\n"
        "2. Then cite the exact clause/section that supports your answer (quote it).\n"
        "3. If the document does not contain the answer, explicitly state 'The document does not contain information about [topic]' and summarize what it does say.\n"
        "4. Be professional, structured, and avoid generic filler. No disclaimers about being AI."
    )

    user_prompt = (
        f"FULL LEGAL DOCUMENT CONTENT:\n"
        f"\"\"\"\n{doc_context}\n\"\"\""
        f"{excerpt_str}\n\n"
        f"USER QUESTION: {question}\n\n"
        f"Provide a direct, real answer based strictly on the document above. Cite clauses."
    )

    # 1. OpenAI API Provider - PRIMARY for real answers
    openai_key = (user_api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    # Strip accidental quotes/spaces
    openai_key = openai_key.strip().strip('"').strip("'")

    if openai_key:
        # Validate format early
        if not openai_key.startswith("sk-"):
            print(f"[LLM] OpenAI key looks invalid (must start with sk-): {openai_key[:8]}...")
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1200,
                "temperature": 0.1
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                res_json = r.json()
                ans = res_json["choices"][0]["message"]["content"]
                if ans and ans.strip():
                    print(f"[LLM] OpenAI success: {len(ans)} chars")
                    return ans.strip()
            else:
                # Surface real error instead of silent fallback - helps user rectify 401/429
                err_text = r.text[:800]
                print(f"[LLM] OpenAI failed {r.status_code}: {err_text}")
                if r.status_code in (401, 403):
                    return f"⚠️ OpenAI API key invalid or unauthorized (HTTP {r.status_code}). Please check your OPENAI_API_KEY in .env or the 🔑 frontend input. Details: {err_text[:300]}"
                if r.status_code == 429:
                    return f"⚠️ OpenAI rate limit / quota exceeded (HTTP 429). {err_text[:300]}"
                # For other errors fall through to next provider but keep log
        except Exception as e:
            print(f"[LLM] OpenAI error: {e}")

    # 2. Google Gemini Provider (REST API)
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if gemini_key:
        # A. Gemini REST API endpoint
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
                ]
            }
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                res = r.json()
                candidates = res.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
        except Exception as e:
            print(f"[LLM] Gemini REST error: {e}")

        # B. Google GenAI SDK
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[LLM] Gemini SDK error: {e}")

    # 3. Groq API Provider
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.2
            }
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                res_json = r.json()
                ans = res_json["choices"][0]["message"]["content"]
                if ans and ans.strip():
                    return ans.strip()
        except Exception as e:
            print(f"[LLM] Groq error: {e}")

    # 4. Local Ollama Provider
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    try:
        url = f"{ollama_host}/api/generate"
        payload = {
            "model": "llama3",
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False
        }
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200 and r.json().get("response"):
            return r.json()["response"].strip()
    except Exception:
        pass

    # 5. Smart Local Legal Extractive RAG QA Engine (Fallback)
    return _local_extractive_answer(question, doc_context, contexts)

