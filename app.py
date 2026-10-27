import json
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from procurex.config import get_settings
from procurex.documents import parse_uploaded_file
from procurex.schemas import Requirements
from procurex.agent import ProcurementAgent
from procurex.rules import evaluate_quote, rank_vendors
from procurex.reporting import build_report, report_json, comparison_csv

st.set_page_config(page_title="ProcureX | AI Procurement Agent", page_icon="🧾", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1450px;}
[data-testid="stMetric"] {background: rgba(120,120,120,.06); padding: 14px; border-radius: 12px;}
.procurex-subtitle {color: #777; margin-top: -12px;}
</style>
""", unsafe_allow_html=True)

def init_state():
    defaults = {"quotes": [], "analysis": None, "audit": [], "requirements": None, "review": None, "agent_trace": []}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
init_state()

settings = get_settings()
st.title("🧾 ProcureX")
st.markdown('<p class="procurex-subtitle">LLM-powered procurement intelligence · Constraint-first decisions · Human approval</p>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Workspace")
    st.caption("Hackathon MVP · AI extraction with deterministic policy checks")
    api_ready = bool(settings.openai_api_key)
    st.markdown(f"**LLM status:** {'🟢 API key configured' if api_ready else '🟠 Demo mode / no API key'}")
    st.caption(f"Model: `{settings.openai_model}`")
    st.divider()
    st.markdown("**Safety design**")
    st.write("• Mandatory constraints are evaluated in Python.")
    st.write("• Unknown values are never silently treated as passing.")
    st.write("• No purchase order or email is sent automatically.")
    if st.button("Reset workspace", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

tab_req, tab_docs, tab_analysis, tab_approval = st.tabs([
    "① Requirements", "② Quotations", "③ Agent analysis", "④ Approval & audit"
])

with tab_req:
    st.subheader("Define the purchase")
    default_text = "100 laptops with at least 16 GB RAM, 512 GB SSD, Intel Core i5 / AMD Ryzen 5 or better, 3-year warranty, and target unit price below ₹60,000."
    req_text = st.text_area("Natural-language requirement", value=st.session_state.get("req_text", default_text), height=90)
    cols = st.columns(3)
    with cols[0]:
        quantity = st.number_input("Quantity", min_value=1, value=100, step=1)
        min_ram = st.number_input("Minimum RAM (GB)", min_value=1, value=16, step=1)
    with cols[1]:
        min_ssd = st.number_input("Minimum SSD (GB)", min_value=1, value=512, step=128)
        min_warranty = st.number_input("Minimum warranty (years)", min_value=0, value=3, step=1)
    with cols[2]:
        budget = st.number_input("Maximum unit price (₹)", min_value=1, value=60000, step=1000)
        delivery_limit = st.number_input("Preferred max delivery (days; 0 = no limit)", min_value=0, value=21, step=1)
    prefs = st.text_input("Optional preferences", value="On-site warranty, reputable vendor, clear tax and delivery terms")
    if st.button("Save procurement requirements", type="primary"):
        try:
            req = Requirements(
                natural_language=req_text, quantity=int(quantity), min_ram_gb=int(min_ram),
                min_ssd_gb=int(min_ssd), min_warranty_years=int(min_warranty),
                max_unit_price=float(budget), max_delivery_days=int(delivery_limit) if delivery_limit else None,
                preferences=prefs
            )
            st.session_state.requirements = req.model_dump()
            st.session_state.req_text = req_text
            st.session_state.audit.append({"time": datetime.now(timezone.utc).isoformat(), "action": "requirements_saved", "detail": req.model_dump()})
            st.success("Requirements saved. Upload quotations or use the demo set.")
        except Exception as exc:
            st.error(f"Could not save requirements: {exc}")
    if st.session_state.requirements:
        st.markdown("#### Structured requirement")
        st.json(st.session_state.requirements)

with tab_docs:
    st.subheader("Add vendor quotations")
    st.write("Upload text-based PDF, DOCX, XLSX, CSV, TXT, EML, or Markdown. Scanned PDFs may need OCR.")
    uploads = st.file_uploader("Quotation files", type=["pdf","docx","xlsx","xls","csv","txt","eml","md"], accept_multiple_files=True)
    left, right = st.columns([1, 2])
    with left:
        if st.button("Load sample quotations", use_container_width=True):
            st.session_state.quotes = [
                {
                    "vendor_name":"Alpha Systems", "unit_price":57500, "currency":"INR", "quantity":100,
                    "ram_gb":16, "ssd_gb":512, "processor":"Intel Core i5-1335U", "processor_tier":5,
                    "warranty_years":3, "warranty_type":"On-site", "delivery_days":14, "tax_percent":18,
                    "other_fees":0, "model_number":"AlphaBook A15", "confidence":0.96,
                    "evidence":[
                        {"field":"unit_price","quote":"Unit price: ₹57,500","location":"Demo quotation"},
                        {"field":"ram_gb","quote":"16 GB RAM","location":"Demo quotation"},
                        {"field":"ssd_gb","quote":"512 GB SSD","location":"Demo quotation"},
                        {"field":"warranty_years","quote":"3-year on-site warranty","location":"Demo quotation"}
                    ],
                    "missing_fields":[], "source_file":"demo_alpha.txt",
                    "raw_text":"Vendor: Alpha Systems\nQuantity: 100 laptops\nUnit price: ₹57,500\n16 GB RAM, 512 GB SSD, Intel Core i5-1335U\n3-year on-site warranty\nDelivery within 14 days\nGST: 18%"
                },
                {
                    "vendor_name":"Budget Computing", "unit_price":52500, "currency":"INR", "quantity":100,
                    "ram_gb":8, "ssd_gb":512, "processor":"Intel Core i5-1235U", "processor_tier":5,
                    "warranty_years":1, "warranty_type":"Carry-in", "delivery_days":10, "tax_percent":18,
                    "other_fees":0, "model_number":"BudgetPro 14", "confidence":0.94,
                    "evidence":[
                        {"field":"unit_price","quote":"Unit price: ₹52,500","location":"Demo quotation"},
                        {"field":"ram_gb","quote":"8 GB RAM","location":"Demo quotation"},
                        {"field":"warranty_years","quote":"1-year carry-in warranty","location":"Demo quotation"}
                    ],
                    "missing_fields":[], "source_file":"demo_budget.txt",
                    "raw_text":"Vendor: Budget Computing\nQuantity: 100 laptops\nUnit price: ₹52,500\n8 GB RAM, 512 GB SSD, Intel Core i5-1235U\n1-year carry-in warranty\nDelivery within 10 days\nGST: 18%"
                },
                {
                    "vendor_name":"NextGen Devices", "unit_price":59000, "currency":"INR", "quantity":100,
                    "ram_gb":16, "ssd_gb":512, "processor":"Intel Core i7-1355U", "processor_tier":7,
                    "warranty_years":None, "warranty_type":None, "delivery_days":None, "tax_percent":18,
                    "other_fees":None, "model_number":"NextGen Pro", "confidence":0.84,
                    "evidence":[
                        {"field":"unit_price","quote":"Unit price: ₹59,000","location":"Demo quotation"},
                        {"field":"ram_gb","quote":"16 GB RAM","location":"Demo quotation"},
                        {"field":"warranty_years","quote":"Warranty terms to be confirmed","location":"Demo quotation"}
                    ],
                    "missing_fields":["warranty_years","delivery_days","other_fees"],
                    "source_file":"demo_nextgen.txt",
                    "raw_text":"Vendor: NextGen Devices\nQuantity: 100 laptops\nUnit price: ₹59,000\n16 GB RAM, 512 GB SSD, Intel Core i7-1355U\nGST: 18%\nWarranty and delivery terms to be confirmed."
                }
            ]
            st.session_state.audit.append({"time": datetime.now(timezone.utc).isoformat(), "action":"sample_quotes_loaded", "detail":"3 demo quotations"})
            st.success("Loaded three sample quotations.")
    with right:
        if st.button("Parse uploaded quotations", type="primary", disabled=not uploads, use_container_width=True):
            new_quotes = []
            agent = ProcurementAgent()
            progress = st.progress(0, text="Reading documents…")
            errors = []
            for idx, uploaded in enumerate(uploads):
                try:
                    parsed = parse_uploaded_file(uploaded.name, uploaded.getvalue())
                    with st.spinner(f"Extracting fields from {uploaded.name}…"):
                        extracted = agent.extract_quotation(parsed["text"], uploaded.name)
                    data = extracted.model_dump()
                    data["source_file"] = uploaded.name
                    data["raw_text"] = parsed["text"][:30000]
                    data["document_metadata"] = parsed["metadata"]
                    new_quotes.append(data)
                    st.session_state.audit.append({"time": datetime.now(timezone.utc).isoformat(), "action":"quotation_extracted", "detail":{"file":uploaded.name,"vendor":data.get("vendor_name"),"method":extracted.extraction_method}})
                except Exception as exc:
                    errors.append(f"{uploaded.name}: {exc}")
                progress.progress((idx + 1) / len(uploads), text=f"Processed {idx+1}/{len(uploads)}")
            if new_quotes:
                st.session_state.quotes = new_quotes
                st.success(f"Extracted {len(new_quotes)} quotation(s).")
            for error in errors:
                st.error(error)
    if st.session_state.quotes:
        st.markdown("#### Extracted quotation summary")
        rows = []
        for q in st.session_state.quotes:
            rows.append({
                "Vendor": q.get("vendor_name") or "Unknown vendor",
                "Unit price": f"₹{q['unit_price']:,.2f}" if q.get("unit_price") is not None else "Unknown",
                "RAM": f"{q['ram_gb']} GB" if q.get("ram_gb") is not None else "Unknown",
                "SSD": f"{q['ssd_gb']} GB" if q.get("ssd_gb") is not None else "Unknown",
                "Warranty": f"{q['warranty_years']} years" if q.get("warranty_years") is not None else "Unknown",
                "Delivery": f"{q['delivery_days']} days" if q.get("delivery_days") is not None else "Unknown",
                "Extraction confidence": q.get("confidence", "n/a")
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with tab_analysis:
    st.subheader("Agent workflow and vendor evaluation")
    req_data = st.session_state.requirements
    quotes = st.session_state.quotes
    if not req_data:
        st.info("Save the requirement in tab ① first.")
    elif not quotes:
        st.info("Upload quotations or load the sample quotations in tab ②.")
    else:
        if st.button("Run ProcureX agent", type="primary"):
            req = Requirements(**req_data)
            deterministic = []
            for q in quotes:
                deterministic.append(evaluate_quote(q, req))
            ranked = rank_vendors(quotes, deterministic)
            with st.spinner("Synthesizing evidence-backed recommendation…"):
                try:
                    synthesis = ProcurementAgent().recommend(req, quotes, deterministic, ranked)
                    st.session_state.analysis = {
                        "evaluations": deterministic, "ranking": ranked,
                        "synthesis": synthesis.model_dump(), "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    st.session_state.agent_trace = [
                        {"step":1,"name":"Requirement check","status":"complete","detail":"Loaded structured constraints"},
                        {"step":2,"name":"Document extraction","status":"complete","detail":f"Processed {len(quotes)} quotation(s)"},
                        {"step":3,"name":"Deterministic validation","status":"complete","detail":"Evaluated mandatory fields as PASS / FAIL / UNKNOWN"},
                        {"step":4,"name":"Trade-off synthesis","status":"complete","detail":"LLM generated recommendation constrained by validation results"},
                        {"step":5,"name":"Human approval","status":"pending","detail":"Awaiting reviewer decision"}
                    ]
                    st.session_state.audit.append({"time":datetime.now(timezone.utc).isoformat(),"action":"analysis_completed","detail":{"recommendation":synthesis.recommended_vendor,"llm_enabled":synthesis.llm_used}})
                except Exception as exc:
                    st.error(f"Agent analysis failed: {exc}")
        analysis = st.session_state.analysis
        if analysis:
            synthesis = analysis["synthesis"]
            m1,m2,m3 = st.columns(3)
            m1.metric("Quotations evaluated", len(quotes))
            m2.metric("Compliant vendors", sum(1 for e in analysis["evaluations"] if e["overall_status"] == "COMPLIANT"))
            m3.metric("Recommendation", synthesis.get("recommended_vendor") or "No compliant option")
            if synthesis.get("llm_used"):
                st.caption("Recommendation narrative generated with the configured LLM. Mandatory compliance statuses were calculated independently.")
            else:
                st.caption("Fallback mode: recommendation narrative was generated without a successful LLM call. Configure OPENAI_API_KEY for live AI.")
            st.markdown("### Recommendation")
            st.write(synthesis.get("recommendation_summary","No summary available."))
            if synthesis.get("recommended_vendor"):
                st.success(f"Recommended for review: {synthesis['recommended_vendor']}")
            else:
                st.warning("No vendor is currently eligible for recommendation. Resolve failures or unknown mandatory fields.")
            st.markdown("### Comparison")
            comparison_rows = []
            for quote, ev in zip(quotes, analysis["evaluations"]):
                comparison_rows.append({
                    "Vendor": quote.get("vendor_name") or "Unknown",
                    "Status": ev["overall_status"],
                    "Unit price": f"₹{quote['unit_price']:,.2f}" if quote.get("unit_price") is not None else "Unknown",
                    "Est. total incl. stated GST": f"₹{ev['estimated_total_incl_tax']:,.2f}" if ev.get("estimated_total_incl_tax") is not None else "Unknown",
                    "Warranty": f"{quote['warranty_years']} yr" if quote.get("warranty_years") is not None else "Unknown",
                    "Delivery": f"{quote['delivery_days']} days" if quote.get("delivery_days") is not None else "Unknown",
                    "Flags": len(ev["anomalies"])
                })
            st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)
            st.markdown("### Mandatory requirement checks")
            for quote, ev in zip(quotes, analysis["evaluations"]):
                with st.expander(f"{quote.get('vendor_name') or 'Unknown vendor'} — {ev['overall_status']}"):
                    st.dataframe(pd.DataFrame(ev["checks"]), use_container_width=True, hide_index=True)
                    if ev["anomalies"]:
                        st.markdown("**Anomalies / clarification needs**")
                        for anomaly in ev["anomalies"]:
                            st.warning(anomaly)
                    evidence = quote.get("evidence") or []
                    if evidence:
                        st.markdown("**Extracted evidence**")
                        st.dataframe(pd.DataFrame(evidence), use_container_width=True, hide_index=True)
                    with st.expander("Source text"):
                        st.text(quote.get("raw_text","")[:10000])
            st.markdown("### Trade-off analysis")
            for item in synthesis.get("tradeoffs", []):
                st.markdown(f"- **{item.get('vendor','Vendor')}:** {item.get('analysis','')}")
            st.markdown("### Clarification questions")
            questions = synthesis.get("clarification_questions", [])
            if questions:
                for question in questions:
                    st.info(question)
            else:
                st.write("No clarification questions generated.")
            st.markdown("### Agent trace")
            st.dataframe(pd.DataFrame(st.session_state.agent_trace), use_container_width=True, hide_index=True)

with tab_approval:
    st.subheader("Human decision and audit trail")
    current = st.session_state.analysis
    rec = current["synthesis"].get("recommended_vendor") if current else None
    st.write(f"**Current recommendation:** {rec or 'Not available — run analysis first'}")
    st.warning("This action records a reviewer decision only. The prototype does not send emails, issue purchase orders, or spend money.")
    reviewer = st.text_input("Reviewer name / role", value="Procurement reviewer")
    decision = st.radio("Decision", ["Pending review","Approve recommendation","Reject recommendation","Request clarification / changes"], horizontal=True)
    notes = st.text_area("Decision notes", placeholder="Explain approval conditions or list questions for the vendor.")
    if st.button("Record human decision", type="primary"):
        review = {"time":datetime.now(timezone.utc).isoformat(),"reviewer":reviewer,"decision":decision,"recommended_vendor":rec,"notes":notes}
        st.session_state.review = review
        st.session_state.audit.append({"time":review["time"],"action":"human_review_recorded","detail":review})
        st.success("Review decision recorded in the current session.")
    if st.session_state.review:
        st.markdown("#### Latest review")
        st.json(st.session_state.review)
    st.markdown("#### Audit log")
    if st.session_state.audit:
        st.dataframe(pd.DataFrame(st.session_state.audit), use_container_width=True, hide_index=True)
    else:
        st.caption("No actions recorded yet.")
    report = build_report(
        requirements=st.session_state.requirements,
        quotations=st.session_state.quotes,
        analysis=st.session_state.analysis,
        review=st.session_state.review,
        audit=st.session_state.audit
    )
    st.download_button("Download full audit report (JSON)", report_json(report), "procurex_audit_report.json", "application/json")
    if st.session_state.analysis:
        st.download_button("Download vendor comparison (CSV)", comparison_csv(st.session_state.quotes, st.session_state.analysis["evaluations"]), "procurex_comparison.csv", "text/csv")

st.divider()
st.caption("ProcureX hackathon MVP · Verify every extracted field against the original quotation. AI output is advisory; mandatory rules and human approval govern the decision.")
