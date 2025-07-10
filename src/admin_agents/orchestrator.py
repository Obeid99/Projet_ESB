from .intent_parser import parse_intent
from .subject_validator import is_valid_subject
from .visualization import generate_feedback_chart_from_mongo
from datetime import datetime, timedelta, date as dateclass
import random
import re

def get_feedback_counts(mongo_db, collection_feedbacks, subject, date):
    # Détermination de la période
    if date == "today":
        target = dateclass.today()
    elif date == "yesterday":
        target = dateclass.today() - timedelta(days=1)
    elif date == "tomorrow":
        target = dateclass.today() + timedelta(days=1)
    else:
        try:
            target = datetime.strptime(date, "%Y-%m-%d").date()
        except Exception:
            target = dateclass.today()
    start = datetime.combine(target, datetime.min.time()).timestamp()
    end = datetime.combine(target + timedelta(days=1), datetime.min.time()).timestamp()

    # Requête de base (sur la période)
    query = {"timestamp": {"$gte": start, "$lt": end}}
    feedbacks = list(mongo_db[collection_feedbacks].find(query))
    subject_clean = subject.strip().lower() if subject else None

    # Filtrage sur le sujet (champ ou fallback sur message)
    results = []
    for fb in feedbacks:
        # Si le champ subject existe
        if subject_clean:
            if "subject" in fb and fb["subject"]:
                if fb["subject"].strip().lower() == subject_clean:
                    results.append(fb)
            else:
                # Fallback: chercher le sujet dans le message
                msg = fb.get("message", "").lower()
                if subject_clean in msg:
                    results.append(fb)
        else:
            results.append(fb)  # Toutes matières confondues

    # Calcul stats
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for fb in results:
        sentiment = fb.get("sentiment", "neutral")
        counts[sentiment] = counts.get(sentiment, 0) + 1
    total = sum(counts.values())
    return counts, total

def handle_admin_query(message, mongo_db, collection_feedbacks, collection_admin, session):
    intent, entities = parse_intent(message)
    pending_intent = session.get('pending_intent')
    pending_data = session.get('pending_data', {})
    msg = message.lower().strip()

    # 1. Gratitude
    if intent == "gratitude":
        responses = [
            "Avec plaisir 😊 ! Si tu veux plus d'infos, je suis là.",
            "De rien, ravi d'aider !",
            "Toujours là pour toi 🙏",
            "Merci à toi ! N’hésite pas si besoin 😉",
            "C’est avec plaisir, bonne continuation !",
        ]
        session['pending_intent'] = None
        session['pending_data'] = {}
        return random.choice(responses), {}

    # 2. Confirmation OUI à une question précédente (chart/export)
    if intent in ("yes", "confirm") and pending_intent:
        if pending_intent == "get_feedback_chart":
            subject = pending_data.get("subject")
            date = pending_data.get("date", "today")
            url_chart, _ = generate_feedback_chart_from_mongo(mongo_db, subject, date)
            session['pending_intent'] = None
            session['pending_data'] = {}
            return f"Voici le graphique demandé : <br><img src='{url_chart}' />", {"chart_url": url_chart}

    # 3. Refus NON
    if intent == "refuse" and pending_intent:
        session['pending_intent'] = None
        session['pending_data'] = {}
        return "Compris 👍 ! Je n’affiche rien. Puis-je t’aider pour autre chose ?", {}

    # 4. Salutations
    if intent == "greeting":
        session['pending_intent'] = None
        session['pending_data'] = {}
        return (
            "👋 Bonjour, bienvenue sur l’interface admin ESB. "
            "Je suis là pour vous fournir toutes les informations nécessaires à propos des feedbacks des étudiants. ",
            {}
        )

    # 5. Extraction du sujet (matière) et validation (regex sur phrase utilisateur)
    subject = entities.get("subject")
    date = entities.get("date", "today")
    # Extraction manuelle si l'utilisateur écrit "pour la matière xxx"
    if not subject:
        matiere = re.search(r"mati[eè]re ([\w\s-]+)", msg)
        if matiere:
            subject = matiere.group(1).strip()
    # Validation si précisé (empêche d'aller plus loin si matière non valide)
    if subject:
        if not is_valid_subject(subject):
            session['pending_intent'] = None
            session['pending_data'] = {}
            return (f"La matière '{subject}' n'existe pas dans le syllabus ESB.", {})

    # 6. Statistiques/Chart demandé (avec ou sans matière, sur période)
    if intent in ("get_feedback_stats", "get_feedback_chart"):
        # Gestion des périodes
        if date == "today":
            target_date = dateclass.today()
        elif date == "yesterday":
            target_date = dateclass.today() - timedelta(days=1)
        elif date == "tomorrow":
            target_date = dateclass.today() + timedelta(days=1)
        else:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except Exception:
                target_date = dateclass.today()

        # Pas de feedback possible dans le futur
        if target_date > dateclass.today():
            session['pending_intent'] = None
            session['pending_data'] = {}
            return "Je ne peux pas encore prévoir les feedbacks du futur ! 😅", {}

        # Obtenir stats feedbacks (nouvelle fonction)
        counts, total = get_feedback_counts(mongo_db, collection_feedbacks, subject, date)

        # --- Aucun feedback trouvé pour la matière sur la période
        if total == 0:
            session['pending_intent'] = None
            session['pending_data'] = {}
            if subject:
                if date in ["today", "yesterday"]:
                    period_label = "aujourd'hui" if date == "today" else "hier"
                    return (f"Je n'ai trouvé aucun feedback pour la matière **{subject}** {period_label}.", {})
                else:
                    return (f"Je n'ai trouvé aucun feedback pour la matière **{subject}** sur la période demandée.", {})
            else:
                if date in ["today", "yesterday"]:
                    period_label = "aujourd'hui" if date == "today" else "hier"
                    return (f"Je n'ai trouvé aucun feedback {period_label}.", {})
                else:
                    return (f"Je n'ai trouvé aucun feedback pour la période demandée.", {})

        # --- Statistiques par matière (ou global)
        if intent == "get_feedback_stats":
            if subject:
                date_label = "aujourd'hui" if date == "today" else ( "hier" if date == "yesterday" else f"la période {date}" )
                return (
                    f"Pour la matière **{subject}** {date_label}, nous avons reçu {total} feedbacks : "
                    f"{counts['positive']} positifs, {counts['negative']} négatifs, {counts['neutral']} neutres.",
                    {}
                )
            else:
                date_label = "aujourd'hui" if date == "today" else ( "hier" if date == "yesterday" else f"la période {date}" )
                return (
                    f"Pour {date_label}, nous avons reçu {total} feedbacks : "
                    f"{counts['positive']} positifs, {counts['negative']} négatifs, {counts['neutral']} neutres.",
                    {}
                )

        # --- Proposer un graphique (matière ou global)
        if intent == "get_feedback_chart":
            session['pending_intent'] = "get_feedback_chart"
            session['pending_data'] = {"subject": subject, "date": date}
            matiere_text = f"la matière **{subject}**" if subject else "toutes les matières"
            return (
                f"Pour {matiere_text} sur la période demandée, nous avons reçu {total} feedbacks : "
                f"- 👍 {counts['positive']} positifs - 👎 {counts['negative']} négatifs - 😐 {counts['neutral']} neutres. "
                f"Souhaitez-vous voir le graphique ? Répondez par 'oui' ou 'non'.",
                {}
            )

    # 7. Export (non implémenté)
    if intent == "export_feedback":
        session['pending_intent'] = None
        session['pending_data'] = {}
        return "La fonction d’export n’est pas encore implémentée.", {}

    # 8. Fallback
    session['pending_intent'] = None
    session['pending_data'] = {}
    return (
        "Je n'ai pas compris la demande. "
        "Essaye par exemple :\n"
        "- 'Nombre de feedbacks positifs aujourd’hui'\n"
        "- 'Montre-moi le feedback chart.'\n",
        {}
    )
from datetime import datetime

def get_latest_student_feedback(mongo_db, collection_feedbacks, limit=10):
    cursor = mongo_db[collection_feedbacks].find(
        {"is_user": True}
    ).sort("timestamp", -1).limit(limit)
    feedbacks = []
    for fb in cursor:
        feedbacks.append({
            "id": str(fb.get("_id")),
            "username": fb.get("username", "") or fb.get("user_id", "") or "Etudiant inconnu",
            "title": fb.get("message")[:32] + ("..." if len(fb.get("message","")) > 32 else ""),
            "created_at": datetime.fromtimestamp(fb.get("timestamp")).strftime("%Y-%m-%d %H:%M"),
            "message": fb.get("message", "")
        })
    return feedbacks

