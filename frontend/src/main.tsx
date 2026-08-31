import React, { useState, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = "/api/v1";

// ─── TYPES ───────────────────────────────────────────────────────────────────

interface UploadResult {
  id: number;
  filename: string;
  document_type: string;
  characters: number;
}

interface RiskFlag { term: string; level: string; }
interface Risk { score: number; level: string; flags: RiskFlag[]; }

interface AnalysisResult {
  summary: string;
  risk: Risk;
  obligations: string[];
  dates: string[];
  money: string[];
  simplified: string;
}

interface ChatMessage { role: "user" | "ai"; text: string; }

// ─── SPEECH RECOGNITION (STT) HELPER ──────────────────────────────────────────

const SpeechRecognitionAPI =
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

// ─── HELPERS ─────────────────────────────────────────────────────────────────

function fmt(bytes: number) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function docIcon(type: string) {
  const icons: Record<string, string> = { employment: "👔", nda: "🔒", loan: "💰", rental: "🏠", unknown: "📄" };
  return icons[type] || "📄";
}

// ─── HIGH CLARITY FEMALE TEXT-TO-SPEECH (gTTS + Web SpeechSynthesis) ──────────

let currentAudio: HTMLAudioElement | null = null;

async function speakTextClearFemale(text: string, lang: string = "en") {
  if (!text) return;
  stopSpeaking();

  // 1. Try gTTS High-Clarity Neural Audio Server Endpoint
  try {
    const res = await fetch(`${API}/speech/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.substring(0, 1000), language: lang })
    });
    const data = await res.json();
    if (data.status === "success" && data.audio_url) {
      currentAudio = new Audio(data.audio_url);
      currentAudio.play();
      return;
    }
  } catch (e) {
    console.warn("gTTS audio fetch fallback to WebSpeech API:", e);
  }

  // 2. Web SpeechSynthesis Female Voice Selection Fallback
  if (!("speechSynthesis" in window)) {
    alert("Speech synthesis is not supported in this browser.");
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.1; // Slightly higher pitch for female voice clarity

  // Select high clarity female voice if available
  const voices = window.speechSynthesis.getVoices();
  const femaleVoice = voices.find(v => 
    v.lang.startsWith(lang) && 
    (v.name.includes("Female") || v.name.includes("Samantha") || v.name.includes("Victoria") || v.name.includes("Zira") || v.name.includes("Karen") || v.name.includes("Google") || v.name.includes("Fiona"))
  ) || voices.find(v => v.lang.startsWith(lang));

  if (femaleVoice) utterance.voice = femaleVoice;

  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

// ─── COMPONENTS ──────────────────────────────────────────────────────────────

function Spinner({ dark }: { dark?: boolean }) {
  return <span className={dark ? "spinner spinner-dark" : "spinner"} />;
}

function EmptyState({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div className="empty-state">
      <span className="empty-icon">{icon}</span>
      <div className="empty-title">{title}</div>
      <div className="empty-desc">{desc}</div>
    </div>
  );
}

// ─── UPLOAD SECTION ──────────────────────────────────────────────────────────

function UploadSection({
  onUploaded, uploadResult, loading, setLoading
}: {
  onUploaded: (r: UploadResult) => void;
  uploadResult: UploadResult | null;
  loading: boolean;
  setLoading: (v: boolean) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (f: File) => {
    setFile(f);
    setError("");
  };

  async function upload() {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch(`${API}/documents/upload`, { method: "POST", body: fd });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.detail || `Server error ${r.status}`);
      }
      const data: UploadResult = await r.json();
      onUploaded(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">📂</span>
        <span className="card-title">Upload Legal Document</span>
      </div>
      <div className="card-body">
        <div
          className={`upload-zone ${dragOver ? "drag-over" : ""}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
        >
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <span className="upload-icon">☁️</span>
          <div className="upload-text">Drag & drop or click to browse</div>
          <div className="upload-hint">Supports PDF, DOCX, TXT files</div>
        </div>

        {file && (
          <div className="file-selected">
            <span className="file-icon">📄</span>
            <span className="file-name">{file.name}</span>
            <span className="file-size">{fmt(file.size)}</span>
          </div>
        )}

        {error && <div className="alert alert-danger" style={{ marginTop: 12 }}>⚠️ {error}</div>}

        <div className="btn-group" style={{ marginTop: 16 }}>
          <button
            className="btn btn-primary btn-lg"
            disabled={!file || loading}
            onClick={upload}
          >
            {loading ? <><Spinner /> Uploading…</> : "⬆️ Upload & Process"}
          </button>
          {file && <button className="btn btn-outline btn-lg" onClick={() => setFile(null)}>✕ Clear</button>}
        </div>

        {uploadResult && (
          <div className="alert alert-success" style={{ marginTop: 16 }}>
            <strong>✅ Document Ready!</strong>
            &nbsp; <span className="doc-type-chip">{docIcon(uploadResult.document_type)} {uploadResult.document_type}</span>
            &nbsp;{uploadResult.characters.toLocaleString()} characters extracted
          </div>
        )}
      </div>
    </div>
  );
}

// ─── ANALYSIS SECTION ────────────────────────────────────────────────────────

function AnalysisSection({ docId, loading, setLoading }: { docId: number; loading: boolean; setLoading: (v: boolean) => void }) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("summary");

  async function analyze() {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API}/analysis/${docId}`, { method: "POST" });
      if (!r.ok) throw new Error(`Server error ${r.status}`);
      setResult(await r.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">🔍</span>
        <span className="card-title">AI Document Analysis</span>
        <div style={{ marginLeft: "auto" }}>
          <button className="btn btn-secondary" onClick={analyze} disabled={loading}>
            {loading ? <><Spinner /> Analyzing…</> : "▶ Run Analysis"}
          </button>
        </div>
      </div>
      <div className="card-body">
        {error && <div className="alert alert-danger">⚠️ {error}</div>}
        {loading && <div className="loading-bar"><div className="loading-bar-fill" /></div>}

        {result && (
          <>
            <div className="tabs">
              {[["summary","📋 Summary"],["risk","⚠️ Risk"],["obligations","📌 Obligations"],["entities","🏷️ Entities"],["simplified","💬 Plain English"]].map(([k, label]) => (
                <button key={k} className={`tab ${activeTab === k ? "active" : ""}`} onClick={() => setActiveTab(k)}>{label}</button>
              ))}
            </div>

            {activeTab === "summary" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div className="section-title" style={{ marginBottom: 0 }}>📋 Document Summary</div>
                  <div className="btn-group">
                    <button className="btn btn-outline btn-sm" onClick={() => speakTextClearFemale(result.summary, "en")}>🔊 Listen (Female Voice)</button>
                    <button className="btn btn-outline btn-sm" onClick={stopSpeaking}>⏹️ Stop</button>
                  </div>
                </div>
                <div className="summary-text">{result.summary || "No summary available."}</div>
              </div>
            )}

            {activeTab === "risk" && (
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
                  <div>
                    <div className="section-title" style={{ marginBottom: 4 }}>Risk Score</div>
                    <div style={{ fontSize: "2.5rem", fontWeight: 800, color: result.risk.level === "high" ? "var(--danger)" : result.risk.level === "medium" ? "var(--warning)" : "var(--success)" }}>
                      {result.risk.score}/100
                    </div>
                  </div>
                  <div>
                    <span className={`risk-badge ${result.risk.level}`}>
                      {result.risk.level === "high" ? "🔴" : result.risk.level === "medium" ? "🟡" : "🟢"} {result.risk.level} risk
                    </span>
                  </div>
                </div>
                <div className="risk-bar">
                  <div className={`risk-fill risk-${result.risk.level}`} style={{ width: `${result.risk.score}%` }} />
                </div>
                {result.risk.flags.length > 0 ? (
                  <>
                    <div className="section-title" style={{ marginTop: 20 }}>Risk Flags</div>
                    <div className="flag-list">
                      {result.risk.flags.map((f, i) => (
                        <div key={i} className="flag-item">
                          <span className={`flag-level ${f.level}`}>{f.level}</span>
                          <span style={{ fontFamily: "monospace", background: "#f1f5f9", padding: "2px 8px", borderRadius: 4 }}>{f.term}</span>
                          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Found in document</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="alert alert-success" style={{ marginTop: 12 }}>✅ No significant risk flags detected</div>
                )}
              </div>
            )}

            {activeTab === "obligations" && (
              <div>
                <div className="section-title">📌 Key Obligations</div>
                {result.obligations.length > 0 ? (
                  <div className="obligation-list">
                    {result.obligations.map((o, i) => <div key={i} className="obligation-item">{o}</div>)}
                  </div>
                ) : (
                  <EmptyState icon="📌" title="No obligations found" desc="No explicit obligations (shall/must/agrees to) detected." />
                )}
              </div>
            )}

            {activeTab === "entities" && (
              <div>
                <div className="grid-2">
                  <div>
                    <div className="section-title">📅 Dates</div>
                    {result.dates.length > 0 ? (
                      <div className="tag-list">{result.dates.map((d, i) => <span key={i} className="tag tag-green">📅 {d}</span>)}</div>
                    ) : <div className="alert alert-info">No dates found</div>}
                  </div>
                  <div>
                    <div className="section-title">💰 Monetary Values</div>
                    {result.money.length > 0 ? (
                      <div className="tag-list">{result.money.map((m, i) => <span key={i} className="tag tag-orange">💰 {m}</span>)}</div>
                    ) : <div className="alert alert-info">No monetary values found</div>}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "simplified" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div className="section-title" style={{ marginBottom: 0 }}>💬 Plain English Version</div>
                  <div className="btn-group">
                    <button className="btn btn-outline btn-sm" onClick={() => speakTextClearFemale(result.simplified, "en")}>🔊 Read Aloud (Female Voice)</button>
                    <button className="btn btn-outline btn-sm" onClick={stopSpeaking}>⏹️ Stop</button>
                  </div>
                </div>
                <div className="alert alert-info" style={{ marginBottom: 12 }}>Legal jargon has been replaced with everyday language.</div>
                <div className="simplified-box">{result.simplified}</div>
              </div>
            )}
          </>
        )}

        {!result && !loading && (
          <EmptyState icon="🔍" title="No analysis yet" desc="Click 'Run Analysis' to extract insights from your document." />
        )}
      </div>
    </div>
  );
}

// ─── CHAT SECTION (REAL LLM GENERATED Q&A + STT + FEMALE TTS) ───────────────

function ChatSection({ docId, loading, setLoading }: { docId: number; loading: boolean; setLoading: (v: boolean) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [isListening, setIsListening] = useState(false);
  // API key state removed - LLM uses backend .env configuration
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const recognitionRef = useRef<any>(null);

  // Cleanup recognition and audio on unmount
  React.useEffect(() => {
    return () => {
      stopSpeaking();
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (_) {}
        recognitionRef.current = null;
      }
    };
  }, []);

  const startVoiceInput = () => {
    if (!SpeechRecognitionAPI) {
      alert("Speech Recognition (STT) is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    // Stop any currently playing audio
    stopSpeaking();

    // If already listening, stop it
    if (isListening && recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (_) {}
      recognitionRef.current = null;
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognitionAPI();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognitionRef.current = recognition;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };
      recognition.onerror = (event: any) => {
        setIsListening(false);
        recognitionRef.current = null;
        if (event.error !== "aborted") {
          setError(`Voice input error: ${event.error}`);
        }
      };
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(transcript);
      };

      recognition.start();
    } catch (e: any) {
      setIsListening(false);
      recognitionRef.current = null;
      setError(`Could not start speech recognition: ${e.message}`);
    }
  };

  async function ask() {
    if (!question.trim() || loading) return;
    const q = question.trim();
    setQuestion("");
    setMessages(prev => [...prev, { role: "user", text: q }]);
    setLoading(true);
    setError("");
    setTimeout(scrollToBottom, 50);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({ document_id: docId, question: q }),
      });
      if (!r.ok) throw new Error(`Server error ${r.status}`);
      const data = await r.json();
      setMessages(prev => [...prev, { role: "ai", text: data.answer }]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      setMessages(prev => [...prev, { role: "ai", text: "⚠️ Could not get an answer from LLM API. Please try again." }]);
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 50);
    }
  }

  const suggestions = [
    "What are my main obligations under this contract?",
    "Are there any termination penalties or liability clauses?",
    "What are the payment terms and due dates?",
    "Explain the governing law and confidentiality terms.",
  ];

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">🧠</span>
        <span className="card-title">Real LLM Legal Q&A Engine</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
          <button className="btn btn-outline btn-sm" onClick={stopSpeaking}>⏹️ Stop Audio</button>
        </div>
      </div>
      <div className="card-body">
        {messages.length === 0 && (
          <div style={{ marginBottom: 12 }}>
            <div className="section-title" style={{ marginBottom: 8 }}>Suggested Legal Questions</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {suggestions.map((s, i) => (
                <button key={i} className="btn btn-outline btn-sm" onClick={() => setQuestion(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-state" style={{ margin: "auto" }}>
                <span className="empty-icon">🤖</span>
                <div className="empty-title">Real LLM AI Q&A Engine</div>
                <div className="empty-desc">Ask any legal question. The LLM generates real answers (no rule-based template). Click 🔊 for high-clarity female voice readout.</div>
              </div>
            ) : (
              messages.map((m, i) => (
                <div key={i} className={`chat-bubble ${m.role}`}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    {m.role === "ai" && <div className="ai-label">⚖️ Legal LLM Generated Response</div>}
                    {m.role === "ai" && (
                      <button
                        className="btn btn-outline btn-sm"
                        style={{ padding: "2px 8px", fontSize: "0.75rem" }}
                        onClick={() => speakTextClearFemale(m.text, "en")}
                      >
                        🔊 Listen (Female Voice)
                      </button>
                    )}
                  </div>
                  <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
                </div>
              ))
            )}
            {loading && (
              <div className="chat-bubble ai">
                <div className="ai-label">⚖️ Legal LLM Engine</div>
                <Spinner dark /> Generating real AI response with LLM…
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-row">
            <button
              className={`btn ${isListening ? "btn-danger" : "btn-secondary"}`}
              onClick={startVoiceInput}
              title="Click to speak (Speech-to-Text STT)"
              type="button"
            >
              {isListening ? "🔴 Listening…" : "🎤 Speak"}
            </button>
            <input
              className="form-input"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === "Enter" && ask()}
              placeholder="e.g. What are my obligations? (or click 🎤 to speak)"
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={ask} disabled={!question.trim() || loading}>
              {loading ? <Spinner /> : "Send ➤"}
            </button>
          </div>
        </div>
        {error && <div className="alert alert-danger" style={{ marginTop: 8 }}>⚠️ {error}</div>}
      </div>
    </div>
  );
}

// ─── REAL TRANSLATION SECTION + HIGH CLARITY FEMALE TTS ─────────────────────

function TranslationSection({ docId, loading, setLoading }: { docId: number; loading: boolean; setLoading: (v: boolean) => void }) {
  const [lang, setLang] = useState("hi");
  const [result, setResult] = useState<{ translated_text: string; target_language: string; status: string } | null>(null);
  const [error, setError] = useState("");

  const languages = [
    { code: "hi", label: "🇮🇳 Hindi (हिन्दी)" },
    { code: "te", label: "🇮🇳 Telugu (తెలుగు)" },
    { code: "ta", label: "🇮🇳 Tamil (தமிழ்)" },
    { code: "kn", label: "🇮🇳 Kannada (கன்னட)" },
    { code: "ml", label: "🇮🇳 Malayalam (മലയാളം)" },
    { code: "bn", label: "🇮🇳 Bengali (বাংলা)" },
    { code: "mr", label: "🇮🇳 Marathi (मराठी)" },
    { code: "gu", label: "🇮🇳 Gujarati (ગુજરાતી)" },
    { code: "pa", label: "🇮🇳 Punjabi (ਪੰਜਾਬੀ)" },
    { code: "ur", label: "🇵🇰 Urdu (اردو)" },
    { code: "fr", label: "🇫🇷 French (Français)" },
    { code: "de", label: "🇩🇪 German (Deutsch)" },
    { code: "es", label: "🇪🇸 Spanish (Español)" },
    { code: "ar", label: "🇸🇦 Arabic (العربية)" },
  ];

  async function translate() {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API}/translation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: docId, target_language: lang }),
      });
      if (!r.ok) throw new Error(`Server error ${r.status}`);
      const data = await r.json();
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">🌐</span>
        <span className="card-title">Real Multi-Language Translation + Clear Female TTS</span>
      </div>
      <div className="card-body">
        <div className="form-group">
          <label className="form-label">Select Target Language</label>
          <select className="form-select" value={lang} onChange={e => setLang(e.target.value)}>
            {languages.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
        </div>
        <button className="btn btn-primary" onClick={translate} disabled={loading}>
          {loading ? <><Spinner /> Translating Document…</> : "🌐 Translate Document"}
        </button>

        {error && <div className="alert alert-danger" style={{ marginTop: 12 }}>⚠️ {error}</div>}

        {result && (
          <div style={{ marginTop: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <div className="section-title" style={{ marginBottom: 0 }}>
                Translated Output ({result.target_language.toUpperCase()})
              </div>
              <div className="btn-group">
                <button
                  className="btn btn-success btn-sm"
                  onClick={() => speakTextClearFemale(result.translated_text, result.target_language)}
                >
                  🔊 Play Clear Female Audio (TTS)
                </button>
                <button className="btn btn-outline btn-sm" onClick={stopSpeaking}>
                  ⏹️ Stop
                </button>
              </div>
            </div>
            <div className="summary-text" style={{ whiteSpace: "pre-wrap", maxHeight: 450, overflowY: "auto" }}>
              {result.translated_text}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── VOICE ASSISTANT DEDICATED SECTION ──────────────────────────────────────

function VoiceAssistantSection({ docId, loading, setLoading }: { docId: number; loading: boolean; setLoading: (v: boolean) => void }) {
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState("");
  const recognitionRef = useRef<any>(null);

  // Cleanup: stop all audio and recognition when component unmounts
  React.useEffect(() => {
    return () => {
      stopSpeaking();
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (_) {}
        recognitionRef.current = null;
      }
    };
  }, []);

  const stopAll = useCallback(() => {
    // Stop any playing audio
    stopSpeaking();
    setIsSpeaking(false);
    // Stop recognition if active
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (_) {}
      recognitionRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const toggleRecording = () => {
    if (!SpeechRecognitionAPI) {
      alert("Speech Recognition (STT) is not supported in this browser.");
      return;
    }

    // If already recording, stop everything
    if (isRecording) {
      stopAll();
      return;
    }

    // Stop any currently playing audio before starting new recording
    stopSpeaking();
    setIsSpeaking(false);

    try {
      const recognition = new SpeechRecognitionAPI();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognitionRef.current = recognition;

      recognition.onstart = () => {
        setIsRecording(true);
        setError("");
        setTranscript("");
      };

      recognition.onend = () => {
        setIsRecording(false);
        recognitionRef.current = null;
      };

      recognition.onerror = (event: any) => {
        setIsRecording(false);
        recognitionRef.current = null;
        if (event.error !== "aborted") {
          setError(`Audio recording error: ${event.error}`);
        }
      };

      recognition.onresult = async (event: any) => {
        const text = event.results[0][0].transcript;
        setTranscript(text);
        setLoading(true);
        try {
          const r = await fetch(`${API}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: docId, question: text }),
          });
          const data = await r.json();
          setResponse(data.answer);
          // Play high-clarity female voice audio response automatically
          setIsSpeaking(true);
          await speakTextClearFemale(data.answer, "en");
          // After speech finishes, update state
          // Use a timeout to let audio finish
          const checkAudioDone = setInterval(() => {
            if (!currentAudio || currentAudio.paused || currentAudio.ended) {
              if (!window.speechSynthesis.speaking) {
                setIsSpeaking(false);
                clearInterval(checkAudioDone);
              }
            }
          }, 500);
        } catch (e: any) {
          setError(e.message);
        } finally {
          setLoading(false);
        }
      };

      recognition.start();
    } catch (e: any) {
      setIsRecording(false);
      recognitionRef.current = null;
      setError(e.message);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">🎙️</span>
        <span className="card-title">Interactive Voice Assistant (Clear Female Voice)</span>
        <div style={{ marginLeft: "auto" }}>
          <button className="btn btn-outline btn-sm" onClick={stopAll}>⏹️ Stop All</button>
        </div>
      </div>
      <div className="card-body" style={{ textAlign: "center", padding: "40px 24px" }}>
        <div style={{ marginBottom: 24 }}>
          <button
            className={`btn btn-lg ${isRecording ? "btn-danger" : isSpeaking ? "btn-success" : "btn-primary"}`}
            style={{ borderRadius: "50%", width: 100, height: 100, fontSize: "2.5rem", padding: 0, justifyContent: "center", boxShadow: isRecording ? "0 0 20px rgba(220,38,38,0.6)" : isSpeaking ? "0 0 20px rgba(34,197,94,0.6)" : "var(--shadow-lg)" }}
            onClick={isRecording || isSpeaking ? stopAll : toggleRecording}
          >
            {isRecording ? "⏹️" : isSpeaking ? "🔊" : "🎙️"}
          </button>
          <div style={{ marginTop: 16, fontWeight: 700, fontSize: "1.1rem" }}>
            {isRecording ? "Listening to your voice... Speak now!" : isSpeaking ? "Playing AI response... Click to stop" : "Click Microphone to Speak"}
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            STT captures your voice 🎙️ → LLM API generates the answer 🧠 → High-Clarity Female Audio plays 🔊!
          </div>
        </div>

        {transcript && (
          <div className="alert alert-info" style={{ textAlign: "left", marginBottom: 16 }}>
            <strong>🎙️ Transcribed Voice Query:</strong> {transcript}
          </div>
        )}

        {loading && (
          <div className="alert alert-warning" style={{ textAlign: "left" }}>
            <Spinner dark /> Real LLM API is processing your voice query and generating answer…
          </div>
        )}

        {response && (
          <div className="summary-text" style={{ textAlign: "left", marginTop: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <strong>🔊 AI Female Voice Response:</strong>
              <div className="btn-group">
                <button className="btn btn-outline btn-sm" onClick={() => { setIsSpeaking(true); speakTextClearFemale(response, "en"); }}>🔊 Replay Audio</button>
                <button className="btn btn-outline btn-sm" onClick={stopAll}>⏹️ Stop</button>
              </div>
            </div>
            <div style={{ whiteSpace: "pre-wrap" }}>{response}</div>
          </div>
        )}

        {error && <div className="alert alert-danger" style={{ marginTop: 12, textAlign: "left" }}>⚠️ {error}</div>}
      </div>
    </div>
  );
}

// ─── SUMMARY SECTION ─────────────────────────────────────────────────────────

function SummarySection({ docId, loading, setLoading }: { docId: number; loading: boolean; setLoading: (v: boolean) => void }) {
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");

  async function fetchSummary() {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API}/summarization/${docId}`);
      if (!r.ok) throw new Error(`Server error ${r.status}`);
      const data = await r.json();
      setSummary(data.summary);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">📝</span>
        <span className="card-title">Quick Summary</span>
        <div style={{ marginLeft: "auto" }}>
          <button className="btn btn-primary btn-sm" onClick={fetchSummary} disabled={loading}>
            {loading ? <><Spinner /> Loading…</> : "Generate Summary"}
          </button>
        </div>
      </div>
      <div className="card-body">
        {error && <div className="alert alert-danger">⚠️ {error}</div>}
        {summary ? (
          <div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 10 }}>
              <div className="btn-group">
                <button className="btn btn-outline btn-sm" onClick={() => speakTextClearFemale(summary, "en")}>🔊 Listen (Female Voice)</button>
                <button className="btn btn-outline btn-sm" onClick={stopSpeaking}>⏹️ Stop</button>
              </div>
            </div>
            <div className="summary-text">{summary}</div>
          </div>
        ) : (
          <EmptyState icon="📝" title="No summary yet" desc="Click 'Generate Summary' for a quick AI-generated document overview." />
        )}
      </div>
    </div>
  );
}

// ─── DASHBOARD PAGE ──────────────────────────────────────────────────────────

function DashboardPage({ uploadResult, onNavigate }: { uploadResult: UploadResult | null; onNavigate: (p: string) => void }) {
  return (
    <div>
      <div className="hero">
        <h1>⚖️ Legal AI Platform</h1>
        <p>Analyze legal documents — high-clarity female TTS, multi-language translation, and real LLM AI Q&A engine.</p>
        <div className="hero-badges">
          <span className="badge">📄 PDF / DOCX / TXT</span>
          <span className="badge">🧠 Real LLM Q&A Engine</span>
          <span className="badge">🌐 14 Languages Translation</span>
          <span className="badge">🎙️ Speech-to-Text</span>
          <span className="badge">🔊 Clear Female Neural Voice TTS</span>
          <span className="badge">⚠️ Risk Engine</span>
        </div>
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        {[
          { icon: "📄", label: "Upload", desc: "PDF, DOCX, TXT", action: "upload" },
          { icon: "🧠", label: "Real LLM Q&A", desc: "Text & Voice Input", action: "chat" },
          { icon: "🌐", label: "Translate + TTS", desc: "14 Languages with Audio", action: "translate" },
          { icon: "🎙️", label: "Voice AI", desc: "Interactive Female TTS", action: "voice" },
          { icon: "🔍", label: "Risk Analysis", desc: "Clause & Risk Engine", action: "analysis" },
          { icon: "📝", label: "Summarize", desc: "AI Summarizer", action: "summary" },
        ].map(item => (
          <div
            key={item.action}
            className="stat-card"
            style={{ cursor: "pointer" }}
            onClick={() => onNavigate(item.action)}
          >
            <div style={{ fontSize: "2rem" }}>{item.icon}</div>
            <div className="stat-value" style={{ fontSize: "1.1rem", marginTop: 8 }}>{item.label}</div>
            <div className="stat-label">{item.desc}</div>
          </div>
        ))}
      </div>

      {uploadResult && (
        <div className="card">
          <div className="card-header">
            <span className="card-icon">✅</span>
            <span className="card-title">Current Document</span>
          </div>
          <div className="card-body">
            <div className="grid-2">
              <div>
                <div className="section-title">File Name</div>
                <div style={{ fontWeight: 600 }}>📄 {uploadResult.filename}</div>
              </div>
              <div>
                <div className="section-title">Document Type</div>
                <span className="doc-type-chip">{docIcon(uploadResult.document_type)} {uploadResult.document_type}</span>
              </div>
              <div>
                <div className="section-title">Document ID</div>
                <div style={{ fontFamily: "monospace", fontWeight: 600 }}>#{uploadResult.id}</div>
              </div>
              <div>
                <div className="section-title">Text Characters</div>
                <div style={{ fontWeight: 600 }}>{uploadResult.characters.toLocaleString()}</div>
              </div>
            </div>
            <div className="divider" />
            <div className="btn-group">
              <button className="btn btn-primary" onClick={() => onNavigate("analysis")}>🔍 Analyze Document</button>
              <button className="btn btn-secondary" onClick={() => onNavigate("chat")}>💬 Real LLM Q&A</button>
              <button className="btn btn-success" onClick={() => onNavigate("voice")}>🎙️ Voice AI</button>
              <button className="btn btn-outline" onClick={() => onNavigate("translate")}>🌐 Translate + TTS</button>
            </div>
          </div>
        </div>
      )}

      {!uploadResult && (
        <div className="card">
          <div className="card-body">
            <EmptyState
              icon="📂"
              title="No document uploaded"
              desc="Upload a legal document to get started with AI-powered analysis."
            />
            <div style={{ textAlign: "center", marginTop: 16 }}>
              <button className="btn btn-primary btn-lg" onClick={() => onNavigate("upload")}>⬆️ Upload a Document</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── APP ─────────────────────────────────────────────────────────────────────

function App() {
  const [page, setPage] = useState("dashboard");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [globalLoading, setGlobalLoading] = useState(false);

  const navItems = [
    { id: "dashboard", label: "🏠 Dashboard" },
    { id: "upload", label: "📂 Upload" },
    { id: "analysis", label: "🔍 Analysis" },
    { id: "chat", label: "💬 LLM Q&A" },
    { id: "voice", label: "🎙️ Voice AI" },
    { id: "translate", label: "🌐 Translate" },
    { id: "summary", label: "📝 Summary" },
  ];

  function renderPage() {
    switch (page) {
      case "dashboard":
        return <DashboardPage uploadResult={uploadResult} onNavigate={setPage} />;

      case "upload":
        return (
          <div>
            <div className="section-header">
              <h2>📂 Upload Document</h2>
              <p>Upload a legal document to begin AI-powered analysis</p>
            </div>
            <UploadSection
              onUploaded={r => { setUploadResult(r); setPage("analysis"); }}
              uploadResult={uploadResult}
              loading={globalLoading}
              setLoading={setGlobalLoading}
            />
          </div>
        );

      case "analysis":
        return (
          <div>
            <div className="section-header">
              <h2>🔍 Document Analysis</h2>
              <p>AI-powered risk assessment, obligation extraction, and more</p>
            </div>
            {uploadResult ? (
              <AnalysisSection docId={uploadResult.id} loading={globalLoading} setLoading={setGlobalLoading} />
            ) : (
              <div className="card"><div className="card-body">
                <EmptyState icon="📂" title="No document loaded" desc="Please upload a document first." />
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => setPage("upload")}>⬆️ Upload Document</button>
                </div>
              </div></div>
            )}
          </div>
        );

      case "chat":
        return (
          <div>
            <div className="section-header">
              <h2>💬 Real LLM Q&A Chat</h2>
              <p>Ask legal questions using natural text or Voice (STT) & hear responses in high-clarity Female TTS</p>
            </div>
            {uploadResult ? (
              <ChatSection docId={uploadResult.id} loading={globalLoading} setLoading={setGlobalLoading} />
            ) : (
              <div className="card"><div className="card-body">
                <EmptyState icon="💬" title="No document loaded" desc="Please upload a document to start chatting." />
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => setPage("upload")}>⬆️ Upload Document</button>
                </div>
              </div></div>
            )}
          </div>
        );

      case "voice":
        return (
          <div>
            <div className="section-header">
              <h2>🎙️ Voice Assistant (Clear Female Voice TTS)</h2>
              <p>Interactive voice queries powered by STT, LLM reasoning, and crystal clear female TTS</p>
            </div>
            {uploadResult ? (
              <VoiceAssistantSection docId={uploadResult.id} loading={globalLoading} setLoading={setGlobalLoading} />
            ) : (
              <div className="card"><div className="card-body">
                <EmptyState icon="🎙️" title="No document loaded" desc="Please upload a document to use Voice Assistant." />
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => setPage("upload")}>⬆️ Upload Document</button>
                </div>
              </div></div>
            )}
          </div>
        );

      case "translate":
        return (
          <div>
            <div className="section-header">
              <h2>🌐 Multi-Language Translation + Clear Female TTS</h2>
              <p>Translate your document into 14 languages with real Google Translation & High-Clarity Audio Readout</p>
            </div>
            {uploadResult ? (
              <TranslationSection docId={uploadResult.id} loading={globalLoading} setLoading={setGlobalLoading} />
            ) : (
              <div className="card"><div className="card-body">
                <EmptyState icon="🌐" title="No document loaded" desc="Please upload a document to translate." />
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => setPage("upload")}>⬆️ Upload Document</button>
                </div>
              </div></div>
            )}
          </div>
        );

      case "summary":
        return (
          <div>
            <div className="section-header">
              <h2>📝 Document Summary</h2>
              <p>Get a concise AI-generated summary of your document</p>
            </div>
            {uploadResult ? (
              <SummarySection docId={uploadResult.id} loading={globalLoading} setLoading={setGlobalLoading} />
            ) : (
              <div className="card"><div className="card-body">
                <EmptyState icon="📝" title="No document loaded" desc="Please upload a document to summarize." />
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <button className="btn btn-primary" onClick={() => setPage("upload")}>⬆️ Upload Document</button>
                </div>
              </div></div>
            )}
          </div>
        );

      default:
        return null;
    }
  }

  return (
    <div className="app">
      <header>
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚖️</span>
            Legal AI
          </div>
          <nav>
            {navItems.map(item => (
              <button
                key={item.id}
                className={`nav-btn ${page === item.id ? "active" : ""}`}
                onClick={() => setPage(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main>
        {renderPage()}
      </main>

      <footer>
        ⚖️ Legal AI Platform &nbsp;|&nbsp; AI explanations are informational only and do not constitute legal advice.
        &nbsp;|&nbsp; <a href={`http://localhost:8000/docs`} target="_blank" rel="noreferrer">API Docs</a>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);