import re

def clean_message(msg):
    msg = msg.strip().lower()
    msg = msg.replace("’", "'")
    msg = re.sub(r'[\"“”\'’]', '', msg)
    msg = re.sub(r'[^\w\s]', ' ', msg)
    return msg

def parse_intent(message):
    msg = clean_message(message)

    # 1. Salutation
    GREETINGS = [
        "hi", "hello", "hey", "salut", "bonjour", "yo", "coucou", "bonsoir", "good morning", "good evening"
    ]
    if any(word in msg.split() for word in GREETINGS):
        return "greeting", {}

    # 2. Confirmation OUI
    CONFIRM = [
        "oui", "yes", "ok", "okay", "d'accord", "ouais", "yep", "yup", "of course", "certainement", "absolument"
    ]
    if msg in CONFIRM or any(msg.startswith(x) for x in CONFIRM):
        return "confirm", {}

    # 3. Refus NON
    REFUSE = [
        "non", "no", "pas maintenant", "plus tard", "not now", "later", "nope", "nah"
    ]
    if msg in REFUSE or any(msg.startswith(x) for x in REFUSE):
        return "refuse", {}

    # 4. Gratitude
    GRATITUDE = [
        "merci", "thank you", "thx", "thanks", "cimer", "super", "top", "génial", "parfait",
        "cool", "bravo", "nickel", "merci beaucoup", "thanks a lot", "appreciate", "awesome"
    ]
    if any(word in msg for word in GRATITUDE):
        return "gratitude", {}

    # 5. Statistiques feedback (+ extraction date & sentiment)
    if re.search(r"(stat|stats|statistique|statistiques|nombre|count|feedback|récap)", msg):
        entities = {}
        # Sentiment
        if "positif" in msg or "positive" in msg:
            entities["sentiment"] = "positive"
        elif "negatif" in msg or "négatif" in msg or "negative" in msg:
            entities["sentiment"] = "negative"
        elif "neutre" in msg or "neutral" in msg:
            entities["sentiment"] = "neutral"
        # Date (ordre: futur → semaine/mois → hier/auj)
        if "demain" in msg or "tomorrow" in msg:
            entities["date"] = "tomorrow"
        elif "semaine" in msg or "week" in msg:
            entities["date"] = "this_week"
        elif "mois" in msg or "month" in msg:
            entities["date"] = "this_month"
        elif "hier" in msg or "yesterday" in msg:
            entities["date"] = "yesterday"
        elif "aujourd" in msg or "today" in msg:
            entities["date"] = "today"
        return "get_feedback_stats", entities

    # 6. Graphique/chart (chart, graphe, camembert, etc)
    if any(word in msg for word in [
        "chart", "graphiq", "graph", "camembert", "diagramme", "visualise", "visualisation"
    ]):
        # Extraction date si précisé
        entities = {}
        if "demain" in msg or "tomorrow" in msg:
            entities["date"] = "tomorrow"
        elif "semaine" in msg or "week" in msg:
            entities["date"] = "this_week"
        elif "mois" in msg or "month" in msg:
            entities["date"] = "this_month"
        elif "hier" in msg or "yesterday" in msg:
            entities["date"] = "yesterday"
        elif "aujourd" in msg or "today" in msg:
            entities["date"] = "today"
        return "get_feedback_chart", entities

    # 7. Export
    if any(word in msg for word in ["export", "télécharge", "download", "xls", "excel", "csv", "report"]):
        return "export_feedback", {}

    # 8. Fallback
    return "unknown", {}

# ---- EXEMPLE DE TEST ----
if __name__ == "__main__":
    tests = [
        "Salut !", "ok", "non", "merci", "bonjour",
        "Donne moi le nombre de feedbacks positifs demain",
        "Montre-moi le chart des feedbacks cette semaine",
        "feedback chart", "Statistiques feedbacks aujourd'hui", "Export excel des feedbacks"
    ]
    for t in tests:
        print(f"{t:50} => {parse_intent(t)}")
