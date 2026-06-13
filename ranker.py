
import json, csv, math
from collections import Counter

JD_KEYWORDS = {
    "embeddings":10,"retrieval":10,"ranking":10,"llm":8,"vector":8,
    "pinecone":6,"milvus":6,"qdrant":6,"faiss":6,"python":8,
    "evaluation":6,"ndcg":6,"mrr":6,"map":6,"rag":8,
    "sentence-transformers":8,"weaviate":6,"opensearch":6,"elasticsearch":6
}

CONSULTING = {"tcs","infosys","wipro","accenture","cognizant","capgemini"}

def text(c):
    parts=[c["profile"].get("headline",""),c["profile"].get("summary","")]
    for h in c.get("career_history",[]):
        parts.append(h.get("title",""))
        parts.append(h.get("description",""))
    for s in c.get("skills",[]):
        parts.append(s.get("name",""))
    return " ".join(parts).lower()

def score(c):
    s=0.0
    t=text(c)

    exp=c["profile"].get("years_of_experience",0)
    if 5<=exp<=9: s+=20
    elif 4<=exp<=11: s+=10

    for k,w in JD_KEYWORDS.items():
        if k in t: s+=w

    sig=c["redrob_signals"]
    s+=sig.get("profile_completeness_score",0)/10
    s+=sig.get("recruiter_response_rate",0)*10
    s+=sig.get("interview_completion_rate",0)*10
    s+=max(sig.get("github_activity_score",-1),0)/5

    if sig.get("open_to_work_flag"): s+=5
    if sig.get("willing_to_relocate"): s+=3

    notice=sig.get("notice_period_days",90)
    s+=max(0,10-notice/15)

    companies=" ".join(x.get("company","").lower() for x in c.get("career_history",[]))
    if any(x in companies for x in CONSULTING):
        s-=5

    if "langchain" in t and not any(x in t for x in ["retrieval","ranking","embeddings"]):
        s-=10

    return round(s,4)

def reasoning(c):
    exp=c["profile"].get("years_of_experience",0)
    title=c["profile"].get("current_title","")
    return f"{exp} years experience as {title}; shows relevance to retrieval/ranking AI systems and positive engagement signals."

rows=[]
with open("candidates.jsonl","r",encoding="utf-8") as f:
    for line in f:
        c=json.loads(line)
        rows.append((score(c),c))

rows.sort(key=lambda x:x[0],reverse=True)

with open("submission.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f)
    w.writerow(["candidate_id","rank","score","reasoning"])
    for rank,(sc,c) in enumerate(rows[:100],1):
        w.writerow([c["candidate_id"],rank,sc,reasoning(c)])
print("submission.csv created")
