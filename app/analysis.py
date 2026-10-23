from collections import defaultdict

def analyze_case(documents):
    findings = []

    for document in documents:
        data = document.get("extracted_data", {})
        if data.get("document_type") != "hospital_bill":
            continue

        items = data.get("items", []) or []

        # Deterministic arithmetic validation
        for item in items:
            quantity = item.get("quantity")
            unit_price = item.get("unit_price")
            total = item.get("total")

            if all(isinstance(x, (int, float)) for x in [quantity, unit_price, total]):
                expected = quantity * unit_price
                if abs(expected - total) > 1:
                    findings.append({
                        "type": "arithmetic_discrepancy",
                        "severity": "high",
                        "description": f"{item.get('description', 'Line item')} calculates to {expected}, but the bill shows {total}.",
                        "amount": abs(expected - total),
                        "evidence": [{
                            "document": document["filename"],
                            "page": item.get("page")
                        }]
                    })

        # Potential exact duplicate validation
        seen = defaultdict(list)
        for item in items:
            description = str(item.get("description", "")).lower().strip()
            total = item.get("total")
            if description and total is not None:
                seen[(description, total)].append(item)

        for (_, _), matches in seen.items():
            if len(matches) > 1:
                findings.append({
                    "type": "potential_duplicate",
                    "severity": "medium",
                    "description": f"Potential duplicate charge: {matches[0].get('description')}",
                    "amount": matches[0].get("total"),
                    "evidence": [
                        {"document": document["filename"], "page": x.get("page")}
                        for x in matches
                    ]
                })

    return findings
