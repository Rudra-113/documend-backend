import re


def to_number(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace(",", "").strip()

    # Extract the first numeric value from strings such as:
    # "20%", "₹36,300", "36300"
    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return None

    return float(match.group())


def analyze_insurance(documents):
    bill = None
    policy = None

    for document in documents:
        data = document.get("extracted_data", {})
        document_type = data.get("document_type")

        if document_type == "hospital_bill":
            bill = data

        elif document_type == "insurance_policy":
            policy = data

    if not bill or not policy:
        return {
            "status": "insufficient_documents",
            "message": "Upload both a hospital bill and insurance policy for coverage analysis."
        }

    bill_total = to_number(bill.get("total"))
    copay = to_number(policy.get("copay_percent"))

    if bill_total is None or copay is None:
        return {
            "status": "needs_review",
            "message": "The bill total or policy copay could not be interpreted reliably.",
            "debug": {
                "bill_total_extracted": bill.get("total"),
                "copay_extracted": policy.get("copay_percent")
            }
        }

    patient_share = bill_total * (copay / 100)
    insurance_share = bill_total - patient_share

    return {
        "status": "estimated",
        "bill_total": bill_total,
        "copay_percent": copay,
        "estimated_insurance_share": insurance_share,
        "estimated_patient_share": patient_share,
        "disclaimer": (
            "Coverage estimates are based on extracted policy terms and uploaded "
            "documents. Final claim decisions are made by the insurer."
        )
    }