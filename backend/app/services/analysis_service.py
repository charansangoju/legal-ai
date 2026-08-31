from ai_engine.risk.risk_engine import analyze_risk
from ai_engine.extraction.obligation_extractor import extract_obligations
from ai_engine.extraction.date_extractor import extract_dates
from ai_engine.extraction.money_extractor import extract_money
from ai_engine.simplification.legal_simplifier import simplify
from ai_engine.summarization.document_summarizer import summarize
def analyze(text):
    return {"summary":summarize(text),"risk":analyze_risk(text),"obligations":extract_obligations(text),"dates":extract_dates(text),"money":extract_money(text),"simplified":simplify(text)}
