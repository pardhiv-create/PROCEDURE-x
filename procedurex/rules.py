def evaluate_quote(quote: dict, req) -> dict:
    if isinstance(req, dict):
        class R: pass
        r = R()
        for key,value in req.items(): setattr(r,key,value)
        req = r

    checks = []
    def check(label, actual, expected, passed):
        checks.append({"requirement":label,"actual":actual if actual is not None else "Not provided","required":expected,
                       "status":"UNKNOWN" if actual is None else ("PASS" if passed else "FAIL")})

    check("Unit price", quote.get("unit_price"), f"≤ ₹{req.max_unit_price:,.2f}",
          quote.get("unit_price") <= req.max_unit_price if quote.get("unit_price") is not None else None)
    check("RAM", quote.get("ram_gb"), f"≥ {req.min_ram_gb} GB",
          quote.get("ram_gb") >= req.min_ram_gb if quote.get("ram_gb") is not None else None)
    check("SSD", quote.get("ssd_gb"), f"≥ {req.min_ssd_gb} GB",
          quote.get("ssd_gb") >= req.min_ssd_gb if quote.get("ssd_gb") is not None else None)
    check("Warranty", quote.get("warranty_years"), f"≥ {req.min_warranty_years} years",
          quote.get("warranty_years") >= req.min_warranty_years if quote.get("warranty_years") is not None else None)
    if quote.get("processor_tier") is None:
        check("Processor class", None, "i5/Ryzen 5 class or better", None)
    else:
        check("Processor class", quote.get("processor"), "i5/Ryzen 5 class or better", quote["processor_tier"] >= 5)
    if req.max_delivery_days:
        check("Delivery", quote.get("delivery_days"), f"≤ {req.max_delivery_days} days",
              quote.get("delivery_days") <= req.max_delivery_days if quote.get("delivery_days") is not None else None)

    statuses = [c["status"] for c in checks]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "UNKNOWN" in statuses:
        overall = "NEEDS_CLARIFICATION"
    else:
        overall = "COMPLIANT"

    anomalies = []
    if quote.get("unit_price") is None: anomalies.append("Unit price is missing")
    if quote.get("quantity") is not None and quote["quantity"] != req.quantity:
        anomalies.append(f"Quoted quantity {quote['quantity']} differs from requested quantity {req.quantity}")
    if quote.get("unit_price") is not None and quote["unit_price"] < req.max_unit_price * 0.5:
        anomalies.append("Unit price is unusually low; verify scope, quality and authenticity")
    if quote.get("warranty_years") is None: anomalies.append("Warranty terms are missing or ambiguous")
    if quote.get("delivery_days") is None: anomalies.append("Delivery timeline is missing or ambiguous")
    if quote.get("tax_percent") is None: anomalies.append("Tax treatment is not stated or could not be extracted")
    if quote.get("other_fees") is None: anomalies.append("Other fees / freight / installation costs are unknown")
    if any(c["status"] == "FAIL" for c in checks): anomalies.append("At least one mandatory requirement failed")
    total = None
    if quote.get("unit_price") is not None:
        subtotal = quote["unit_price"] * req.quantity
        fees = quote.get("other_fees") or 0
        tax = quote.get("tax_percent") or 0
        total = (subtotal + fees) * (1 + tax/100)
    return {"vendor":quote.get("vendor_name") or "Unknown vendor","overall_status":overall,"checks":checks,
            "anomalies":anomalies,"estimated_total_incl_tax":round(total,2) if total is not None else None,
            "eligible":overall == "COMPLIANT"}

def rank_vendors(quotations, evaluations):
    pairs = []
    for q,e in zip(quotations,evaluations):
        if e["overall_status"] == "COMPLIANT" and e["estimated_total_incl_tax"] is not None:
            pairs.append({"vendor":q.get("vendor_name") or "Unknown vendor","estimated_total_incl_tax":e["estimated_total_incl_tax"]})
    return sorted(pairs,key=lambda x:x["estimated_total_incl_tax"])
