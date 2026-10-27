import json
import pandas as pd
from datetime import datetime, timezone

def build_report(requirements, quotations, analysis, review, audit):
    safe_quotes = []
    for q in quotations or []:
        safe_quotes.append({k:v for k,v in q.items() if k not in {"raw_text"}})
    return {
        "project":"ProcureX",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "requirements":requirements,
        "quotations":safe_quotes,
        "analysis":analysis,
        "review":review,
        "audit_log":audit
    }

def report_json(report):
    return json.dumps(report,ensure_ascii=False,indent=2,default=str)

def comparison_csv(quotations,evaluations):
    rows=[]
    for q,e in zip(quotations,evaluations):
        rows.append({"vendor":q.get("vendor_name"),"status":e.get("overall_status"),
                     "unit_price":q.get("unit_price"),"estimated_total_incl_tax":e.get("estimated_total_incl_tax"),
                     "warranty_years":q.get("warranty_years"),"delivery_days":q.get("delivery_days"),
                     "anomalies":"; ".join(e.get("anomalies",[]))})
    return pd.DataFrame(rows).to_csv(index=False)
