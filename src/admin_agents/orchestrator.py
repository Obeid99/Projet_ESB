from .intent_parser import parse_intent
from .subject_validator import is_valid_subject
from .response_agent import format_admin_response
from .visualization import generate_feedback_chart
from datetime import datetime, timedelta

def handle_admin_query(message, mongo_db, collection_feedbacks, collection_admin):
    intent, entities = parse_intent(message)
    subject = entities.get("subject")
    date = entities.get("date", "today")

    # DEBUG: pour voir ce que ton intent parser détecte (en dev seulement)
    # return f"Intent détecté : {intent}. Entités : {entities}", {}

    if intent == "greeting":
        return (
            "👋 Bonjour, bienvenue sur l’interface admin ESB. "
            "Vous pouvez demander, par exemple :\n"
            "- 'Statistiques feedbacks aujourd’hui'\n"
            "- 'Montre-moi le feedback chart.'",
            {}
        )

    if subject and not is_valid_subject(subject):
        return (f"Le sujet '{subject}' n'existe pas dans le syllabus ESB.", {})

    if intent in ("get_feedback_stats", "get_feedback_chart"):
        today = datetime.now().date() if date == "today" else datetime.strptime(date, "%Y-%m-%d").date()
        tomorrow = today + timedelta(days=1)
        feedbacks = list(mongo_db[collection_feedbacks].find({
            "subject": subject,
            "timestamp": {
                "$gte": datetime.combine(today, datetime.min.time()).timestamp(),
                "$lt": datetime.combine(tomorrow, datetime.min.time()).timestamp()
            }
        }))
        counts = {"positive": 0, "negative": 0, "neutral": 0}
        for fb in feedbacks:
            sentiment = fb.get("sentiment", "neutral")
            counts[sentiment] = counts.get(sentiment, 0) + 1

        total = sum(counts.values())
        text = format_admin_response(subject, date, counts, total)
        meta = {"sentiment_counts": counts}

        if intent == "get_feedback_chart":
            url_chart = generate_feedback_chart(counts)
            meta["chart_url"] = url_chart

        return text, meta

    if intent == "export_feedback":
        return "La fonction d’export n’est pas encore implémentée.", {}

    # Fallback explicite avec exemples
    return (
        "Je n'ai pas compris la demande. "
        "Essayez par exemple :\n"
        "- 'Nombre de feedbacks positifs aujourd’hui'\n"
        "- 'Montre-moi le feedback chart.'\n"
        "- 'Hi' ou 'Bonjour' pour une salutation.",
        {}
    )
