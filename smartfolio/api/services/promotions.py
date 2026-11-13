def summarize(decisions):
    """Counts + current champion, derived only from Student 3's decision log."""
    real = [d for d in decisions if d["decision"] in ("PROMOTED", "REJECTED")]
    counts = {k: sum(d["decision"] == k for d in decisions)
              for k in ("PROMOTED", "REJECTED", "SKIPPED")}
    champion = real[0]["champion_version"] if real else None
    for d in real:
        if d["decision"] == "PROMOTED":
            champion = d["challenger_version"]
    flagged = sum(1 for d in real
                  if d["decision"] == "REJECTED" and d.get("accuracy_improved"))
    return {"current_champion": champion, "counts": counts,
            "accuracy_improved_but_rejected": flagged, "decisions": decisions}