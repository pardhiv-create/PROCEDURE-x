from procurex.schemas import Requirements
from procurex.rules import evaluate_quote, rank_vendors

def requirements():
    return Requirements(natural_language="100 laptops",quantity=100,min_ram_gb=16,min_ssd_gb=512,
                        min_warranty_years=3,max_unit_price=60000,max_delivery_days=21,preferences="")

def quote(**overrides):
    data={"vendor_name":"Alpha","unit_price":57500,"quantity":100,"ram_gb":16,"ssd_gb":512,
          "processor":"Intel Core i5","processor_tier":5,"warranty_years":3,"delivery_days":14,
          "tax_percent":18,"other_fees":0}
    data.update(overrides)
    return data

def test_compliant_quote_passes():
    result=evaluate_quote(quote(),requirements())
    assert result["overall_status"]=="COMPLIANT"
    assert all(c["status"]=="PASS" for c in result["checks"])

def test_cheaper_vendor_fails_mandatory_ram():
    result=evaluate_quote(quote(unit_price=50000,ram_gb=8),requirements())
    assert result["overall_status"]=="FAIL"

def test_missing_warranty_is_unknown():
    result=evaluate_quote(quote(warranty_years=None),requirements())
    assert result["overall_status"]=="NEEDS_CLARIFICATION"

def test_only_compliant_vendors_ranked():
    qs=[quote(vendor_name="Good"),quote(vendor_name="Bad",ram_gb=8)]
    es=[evaluate_quote(q,requirements()) for q in qs]
    assert [v["vendor"] for v in rank_vendors(qs,es)]==["Good"]
