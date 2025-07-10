def parse_intent(message):
    msg = message.lower().strip()
    # Greetings
    if msg in ("hi", "hello", "salut", "bonjour"):
        return "greeting", {}
    # Feedback stats
    if "stat" in msg or "feedback" in msg:
        return "get_feedback_stats", {}
    if "chart" in msg or "graph" in msg:
        return "get_feedback_chart", {}
    if "export" in msg:
        return "export_feedback", {}
    # Add more rules if needed

    # Default fallback
    return "unknown", {}
