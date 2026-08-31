def analyze_risk(text):
    flags=[]
    for term,level in [("unlimited liability","high"),("indemnif","high"),("penalty","medium"),("terminate","medium"),("sole discretion","high")]:
        if term in text.lower(): flags.append({"term":term,"level":level})
    score=min(100,len(flags)*25)
    return {"score":score,"level":"high" if score>=50 else "medium" if score else "low","flags":flags}
