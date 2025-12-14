def qc_decision(has_solar, confidence):
    if not has_solar:
        return "NOT_VERIFIABLE", ["no solar detected"]

    if confidence >= 0.6:
        return "VERIFIABLE", [
            "clear roof view",
            "distinct solar panels detected"
        ]

    return "NOT_VERIFIABLE", [
        "low confidence detection",
        "possible shadow or occlusion"
    ]
