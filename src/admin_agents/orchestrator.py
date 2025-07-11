from .intent_parser import parse_intent
from .visualization import generate_all_feedback_charts_from_mongo
from .subject_validator import is_valid_subject, normalize_subject, VALID_SUBJECTS
from datetime import datetime, timedelta, date as dateclass
import random
import re
import unicodedata

def strip_accents(text):
    """Supprime les accents pour matcher toutes les variantes."""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_feedback_counts(mongo_db, collection_feedbacks, subject, date):
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
    query = {"timestamp": {"$gte": start, "$lt": end}}
    feedbacks = list(mongo_db[collection_feedbacks].find(query))
    subject_clean = subject.strip().lower() if isinstance(subject, str) and subject else None
    results = []
    for fb in feedbacks:
        if subject_clean:
            msg = fb.get("message", "").lower()
            if subject_clean in msg:
                results.append(fb)
        else:
            results.append(fb)
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for fb in results:
        sentiment = fb.get("sentiment", "neutral")
        counts[sentiment] = counts.get(sentiment, 0) + 1
    total = sum(counts.values())
    return counts, total

def handle_admin_query(message, mongo_db, collection_feedbacks, collection_admin, session):
    from .visualization import generate_all_feedback_charts_from_mongo  # Pour éviter les cycles
    from .subject_validator import VALID_SUBJECTS
    from datetime import datetime, timedelta, date as dateclass
    import re
    import random

    intent, entities = parse_intent(message)
    pending_intent = session.get('pending_intent')
    pending_data = session.get('pending_data', {})
    msg = message.lower().strip()

    # 1. Bloc feedbacks positifs / négatifs / neutres (liste brute des messages)
    if intent in ("get_positive_feedbacks", "get_negative_feedbacks", "get_neutral_feedbacks"):
        date = entities.get("date", "today")
        sentiment_map = {
            "get_positive_feedbacks": "positive",
            "get_negative_feedbacks": "negative",
            "get_neutral_feedbacks": "neutral"
        }
        only_sentiment = sentiment_map[intent]
        _, meta = generate_all_feedback_charts_from_mongo(
            mongo_db, None, date=date, collection_name=collection_feedbacks,
            valid_subjects=VALID_SUBJECTS, only_sentiment=only_sentiment
        )
        fbs = meta.get("raw_feedbacks", [])
        if not fbs:
            label = {"positive": "positif", "negative": "négatif", "neutral": "neutre"}[only_sentiment]
            if date == "today":
                return f"Pour aujourd'hui, il n'y a eu aucun feedback {label}.", {}
            elif date == "yesterday":
                return f"Pour hier, il n'y a eu aucun feedback {label}.", {}
            else:
                return f"Il n'y a eu aucun feedback {label} pour la période demandée.", {}
        # Affichage : juste les messages filtrés
        html = ""
        for fb in fbs:
            m = fb.get("message")
            if m:
                html += f"- {m}<br>"
        return html, {}

    # 2. Bloc : matière la plus positive/négative/neutre (corrigé pour ne pas sortir "0" si tout à zéro)
    if intent in ("get_most_negative_subject", "get_most_positive_subject", "get_most_neutral_subject"):
        date = entities.get("date", "today")
        _, meta = generate_all_feedback_charts_from_mongo(
            mongo_db,
            subjects=None,
            date=date,
            collection_name=collection_feedbacks,
            valid_subjects=VALID_SUBJECTS
        )
        texte = meta.get("interpretation", "")
        if intent == "get_most_negative_subject":
            if "Aucune matière n’a reçu de feedback <b>négatif</b>" in texte or "Aucune donnée disponible" in texte:
                return "Aucune matière n’a reçu de feedback négatif sur la période.", {}
            match = re.search(r"n.gative.*?<b>(.*?)</b> \((\d+)", texte)
            if match and int(match.group(2)) > 0:
                return f"La matière la plus négative est <b>{match.group(1)}</b> ({match.group(2)} feedbacks négatifs)", {}
            else:
                return "Aucune matière n’a reçu de feedback négatif sur la période.", {}
        elif intent == "get_most_positive_subject":
            if "Aucune matière n’a reçu de feedback <b>positif</b>" in texte or "Aucune donnée disponible" in texte:
                return "Aucune matière n’a reçu de feedback positif sur la période.", {}
            match = re.search(r"positive.*?<b>(.*?)</b> \((\d+)", texte)
            if match and int(match.group(2)) > 0:
                return f"La matière la plus positive est <b>{match.group(1)}</b> ({match.group(2)} feedbacks positifs)", {}
            else:
                return "Aucune matière n’a reçu de feedback positif sur la période.", {}
        elif intent == "get_most_neutral_subject":
            if "Aucune matière n’a reçu de feedback <b>neutre</b>" in texte or "Aucune donnée disponible" in texte:
                return "Aucune matière n’a reçu de feedback neutre sur la période.", {}
            match = re.search(r"neutre.*?<b>(.*?)</b> \((\d+)", texte)
            if match and int(match.group(2)) > 0:
                return f"La matière la plus neutre est <b>{match.group(1)}</b> ({match.group(2)} feedbacks neutres)", {}
            else:
                return "Aucune matière n’a reçu de feedback neutre sur la période.", {}


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
            urls, _ = generate_all_feedback_charts_from_mongo(mongo_db, subject, date)
            session['pending_intent'] = None
            session['pending_data'] = {}
            html = "Voici les graphiques demandés :<br>"
            for label, url in urls.items():
                html += f"<b>{label.capitalize()}</b><br><img src='{url}' style='max-width:300px;max-height:300px;'/><br>"
            return html, {"chart_urls": urls}

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

    # 5. Top matière avec plus de feedbacks (get_top_subjects)
    if intent == "get_top_subjects":
        date = entities.get("date", "today")
        top_n = entities.get("top_n", 1)
        # Période Mongo
        if date == "today":
            target = dateclass.today()
        elif date == "yesterday":
            target = dateclass.today() - timedelta(days=1)
        elif date == "tomorrow":
            target = dateclass.today() + timedelta(days=1)
        elif re.match(r"\d{4}-\d{2}-\d{2}", date):
            target = datetime.strptime(date, "%Y-%m-%d").date()
        elif date == "this_week":
            target = dateclass.today() - timedelta(days=dateclass.today().weekday())
        elif date == "this_month":
            target = dateclass.today().replace(day=1)
        else:
            target = dateclass.today()

        if date == "this_week":
            start = datetime.combine(target, datetime.min.time()).timestamp()
            end = datetime.combine(target + timedelta(days=7), datetime.min.time()).timestamp()
        elif date == "this_month":
            next_month = (target.replace(day=28) + timedelta(days=4)).replace(day=1)
            start = datetime.combine(target, datetime.min.time()).timestamp()
            end = datetime.combine(next_month, datetime.min.time()).timestamp()
        else:
            start = datetime.combine(target, datetime.min.time()).timestamp()
            end = datetime.combine(target + timedelta(days=1), datetime.min.time()).timestamp()

        feedbacks = list(mongo_db[collection_feedbacks].find({"timestamp": {"$gte": start, "$lt": end}}))
        matieres = {}
        for fb in feedbacks:
            message = fb.get("message", "")
            msg_norm = normalize_subject(message)
            for matiere in VALID_SUBJECTS:
                mat_norm = normalize_subject(matiere)
                if mat_norm in msg_norm:
                    matieres[mat_norm] = matieres.get(mat_norm, 0) + 1
        if not matieres:
            return "Aucune matière officielle n'a reçu de feedback sur la période demandée.", {}


        # 6. Tri des matières par nombre de feedbacks

        sorted_matières = sorted(matieres.items(), key=lambda x: x[1], reverse=True)
        top_subjects = [mat for mat, _ in sorted_matières[:top_n]]
        session['last_subjects'] = top_subjects  # <-- Stocke les matières top N dans la session

        date_label = "aujourd'hui" if date == "today" else ("hier" if date == "yesterday" else f"la période {date}")
        if top_n == 1:
            top_matiere, count = sorted_matières[0]
            return f"La matière avec le plus de feedbacks {date_label} est **{top_matiere}** ({count} feedbacks).", {}
        top_reponses = [f"- **{mat}** ({c} feedbacks)" for mat, c in sorted_matières[:top_n]]
        return f"Voici le top {top_n} matières ayant reçu le plus de feedbacks {date_label} :\n" + "\n".join(top_reponses), {}

    subjects = entities.get("subject")
    date = entities.get("date", "today")
    # Correction pour toujours avoir une liste
    if isinstance(subjects, str):
        subjects = [s.strip() for s in re.split(r",| et | and ", subjects) if s.strip()]
    elif not isinstance(subjects, list):
        subjects = []
        
    # 6. Demande de graphique comparatif entre les matières demandées
    if intent in ("compare_subjects", "get_top_subjects_chart") or \
        (intent == "get_feedback_chart" and subjects and len(subjects) >= 1):
        urls, meta = generate_all_feedback_charts_from_mongo(
            mongo_db, subjects, date=date
        )
        if not urls:
            return meta.get("error", "Aucune donnée trouvée."), {}
        info = []
        if "most_positive" in meta:
            info.append(f"La matière la plus **positive** est **{meta['most_positive'][0]}** ({meta['most_positive'][1]} feedbacks positifs)")
        if "most_negative" in meta:
            info.append(f"La matière la plus **négative** est **{meta['most_negative'][0]}** ({meta['most_negative'][1]} feedbacks négatifs)")
        if "most_neutral" in meta:
            info.append(f"La matière la plus **neutre** est **{meta['most_neutral'][0]}** ({meta['most_neutral'][1]} feedbacks neutres)")
        html = f"Voici plusieurs graphiques demandés pour la/les matière(s) **{', '.join(subjects)}** ({date}) :<br>"
        for label, url in urls.items():
            html += f"<b>{label.capitalize()}</b><br><img src='{url}' style='max-width:350px;max-height:350px;'/><br>"
        return html, {"chart_urls": urls}


    # 7. Extraction du sujet (matière) et validation, gestion "ces matières"
    subject = entities.get("subject")
    date = entities.get("date", "today")

    # 8. ---- Bloc spécifique: stats positives / négatives / neutres uniquement ----
    if intent in ("get_positive_feedbacks", "get_negative_feedbacks", "get_neutral_feedbacks"):
        date = entities.get("date", "today")
        sentiment_map = {
            "get_positive_feedbacks": "positive",
            "get_negative_feedbacks": "negative",
            "get_neutral_feedbacks": "neutral"
        }
        only_sentiment = sentiment_map[intent]
        _, meta = generate_all_feedback_charts_from_mongo(
            mongo_db, None, date=date, collection_name=collection_feedbacks,
            valid_subjects=VALID_SUBJECTS
        )
        data_table = meta.get("data_table", [])
        matieres_with_sentiment = []
        for entry in data_table:
            if entry[only_sentiment] > 0:
                matieres_with_sentiment.append(f"- {entry['label']} ({entry[only_sentiment]} feedbacks)")
        if not matieres_with_sentiment:
            label = {"positive": "positif", "negative": "négatif", "neutral": "neutre"}[only_sentiment]
            # Texte période
            if date == "today":
                period_label = "aujourd'hui"
            elif date == "yesterday":
                period_label = "hier"
            elif date == "this_week":
                period_label = "cette semaine"
            elif date == "this_month":
                period_label = "ce mois-ci"
            else:
                period_label = f"la période {date}"
            return f"Aucune matière n’a reçu de feedback {label} {period_label}.", {}
        else:
            label = {"positive": "positifs", "negative": "négatifs", "neutral": "neutres"}[only_sentiment]
            # Texte période
            if date == "today":
                period_label = "aujourd'hui"
            elif date == "yesterday":
                period_label = "hier"
            elif date == "this_week":
                period_label = "cette semaine"
            elif date == "this_month":
                period_label = "ce mois-ci"
            else:
                period_label = f"la période {date}"
            html = (
                f"Voici les matières qui ont reçu des feedbacks {label} {period_label} :<br>"
                + "<br>".join(matieres_with_sentiment)
            )
            return html, {}



    # 9. Analyse analytique (désactive validation du subject ici !)
    if intent in ("get_most_negative_subject", "get_most_positive_subject", "get_most_neutral_subject"):
        date = entities.get("date", "today")
        urls, meta = generate_all_feedback_charts_from_mongo(
            mongo_db,
            subjects=None,
            date=date,
            collection_name=collection_feedbacks,
            valid_subjects=VALID_SUBJECTS
        )
        texte = meta.get("interpretation", "")
        if intent == "get_most_negative_subject":
                if "Aucune matière n’a reçu de feedback" in texte or "Aucune matière" in texte:
                    return "Aucune matière n’a reçu de feedback négatif sur la période.", {}
                match = re.search(r"n.gative.*?<b>(.*?)</b> \((\d+)", texte)
                if match and int(match.group(2)) > 0:
                    return f"La matière la plus négative est <b>{match.group(1)}</b> ({match.group(2)} feedbacks négatifs)", {}
                else:
                    return "Aucune matière n’a reçu de feedback négatif sur la période.", {}

        elif intent == "get_most_positive_subject":
            match = re.search(r"positive.*?<b>(.*?)</b> \((\d+)", texte)
            if match:
                return f"La matière la plus positive est <b>{match.group(1)}</b> ({match.group(2)} feedbacks positifs)", {}
            else:
                return "Aucune matière n’a reçu de feedback positif sur la période.", {}
        elif intent == "get_most_neutral_subject":
            match = re.search(r"neutre.*?<b>(.*?)</b> \((\d+)", texte)
            if match:
                return f"La matière la plus neutre est <b>{match.group(1)}</b> ({match.group(2)} feedbacks neutres)", {}
            else:
                return "Aucune matière n’a reçu de feedback neutre sur la période.", {}

    # 9. Gestion "ces matières"
    if subject and isinstance(subject, str) and subject.lower().strip() in [
        "ces matieres", "ces matières", "les matieres", "les matières"
    ]:
        last_subjects = session.get("last_subjects")
        if last_subjects:
            subject = last_subjects  # Passe la liste pour le graphique/stat
        else:
            return "Je n'ai pas trouvé la liste des matières précédentes. Refais un top matières d'abord.", {}

    # 10. Validation subject unique (ne valide pas si c'est une liste !) — DÉSACTIVÉ pour les intents analytiques
    if intent not in ("get_most_negative_subject", "get_most_positive_subject", "get_most_neutral_subject"):
        if subject and isinstance(subject, str):
            if not is_valid_subject(subject):
                session['pending_intent'] = None
                session['pending_data'] = {}
                return (f"La matière '{subject}' n'existe pas dans le syllabus ESB.", {})

    # 11. Statistiques/Chart demandé (avec ou sans matière, sur période)
    if intent in ("get_feedback_stats", "get_feedback_chart"):
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
        if target_date > dateclass.today():
            session['pending_intent'] = None
            session['pending_data'] = {}
            return "Je ne peux pas encore prévoir les feedbacks du futur ! 😅", {}

        counts, total = get_feedback_counts(mongo_db, collection_feedbacks, subject, date)
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
        # Statistiques par matière (ou global)
        if intent == "get_feedback_stats":
            if subject:
                date_label = "aujourd'hui" if date == "today" else ("hier" if date == "yesterday" else f"la période {date}")
                if isinstance(subject, list):
                    return (
                        f"Pour les matières {', '.join(subject)} {date_label}, nous avons reçu {total} feedbacks : "
                        f"{counts['positive']} positifs, {counts['negative']} négatifs, {counts['neutral']} neutres.",
                        {}
                    )
                else:
                    return (
                        f"Pour la matière **{subject}** {date_label}, nous avons reçu {total} feedbacks : "
                        f"{counts['positive']} positifs, {counts['negative']} négatifs, {counts['neutral']} neutres.",
                        {}
                    )
            else:
                date_label = "aujourd'hui" if date == "today" else ("hier" if date == "yesterday" else f"la période {date}")
                return (
                    f"Pour {date_label}, nous avons reçu {total} feedbacks : "
                    f"{counts['positive']} positifs, {counts['negative']} négatifs, {counts['neutral']} neutres.",
                    {}
                )
        # Plusieurs visuels pour la demande de graphique (accepte liste)
        if intent == "get_feedback_chart":
            urls, meta = generate_all_feedback_charts_from_mongo(mongo_db, subject, date)
            matiere_text = (
                f"les matières {', '.join(subject)}" if isinstance(subject, list)
                else (f"la matière **{subject}**" if subject else "toutes les matières")
            )
            session['pending_intent'] = None
            session['pending_data'] = {}
            html = (
                f"Pour {matiere_text} sur la période demandée, voici plusieurs graphiques pour {total} feedbacks : "
                f"- 👍 {counts['positive']} positifs - 👎 {counts['negative']} négatifs - 😐 {counts['neutral']} neutres.<br>"
            )
            for label, url in urls.items():
                html += f"<b>{label.capitalize()}</b><br><img src='{url}' style='max-width:300px;max-height:300px;'/><br>"
            return html, {"chart_urls": urls}

    # 12. Fallback graphique
    if any(w in msg for w in ["graphique", "chart", "camembert", "bar", "donut", "diagramme"]):
        date_fallback = "today"
        if "hier" in msg:
            date_fallback = "yesterday"
        subject_fallback = None
        matiere = re.search(r"mati[eè]re ([\w\s-]+)", msg)
        if matiere:
            subject_fallback = matiere.group(1).strip()
        urls, _ = generate_all_feedback_charts_from_mongo(
            mongo_db, subject_fallback, date_fallback
        )
        matiere_text = f"la matière **{subject_fallback}**" if subject_fallback else "toutes les matières"
        session['pending_intent'] = None
        session['pending_data'] = {}
        html = (
            f"Voici plusieurs graphiques demandés pour {matiere_text} ({date_fallback}) :<br>"
        )
        for label, url in urls.items():
            html += f"<b>{label.capitalize()}</b><br><img src='{url}' style='max-width:300px;max-height:300px;'/><br>"
        return html, {"chart_urls": urls}

    # 13. Aide / Fonctionnalités possibles (robuste et sans accent)
    msg_ascii = strip_accents(msg)
    HELP_PATTERNS = [
        r"que ?peux.?tu.*faire",
        r"qu.?est.?ce ?que ?tu ?peux ?faire",
        r"qu.?est.?ce ?que ?tu ?sais ?faire",
        r"quelles? (sont )?(tes|vos|les)? ?fonctionnalit",
        r"aide", r"help",
        r"comment tu peux m.?aider",
        r"que proposes.?tu",
        r"comment utiliser",
        r"tu fais quoi",
        r"tu sais faire quoi",
        r"quel service",
        r"quels services",
    ]
    for pattern in HELP_PATTERNS:
        if re.search(pattern, msg_ascii):
            return (
    "Voici tout ce que je peux faire pour toi :<br>"
    "📊 Donne-moi le feedback chart.<br>"
    "🟢🔴😐 Afficher le détail des <b>feedbacks positifs, négatifs ou neutres</b> sur une période donnée ou par matière.<br>"
    "📈 Afficher des <b>graphiques</b> (camembert, barres, donut) pour toutes les matières ou une matière précise.<br>"
    "⚖️ Comparer plusieurs matières sur leurs feedbacks (nombre, positifs, négatifs, neutres).<br>"
    "🏆 Afficher le <b>top N matières</b> ayant reçu le plus de feedbacks sur une période.<br>"
    "🤖 Répondre à toutes tes questions sur les statistiques de feedbacks étudiants.<br>"

    "<br>Tu peux essayer par exemple :<br>"
    "• 👉 « Afficher les details de feedbacks positifs aujourd'hui. »<br>"
    "• 👉 « Afficher les details de feedbacks pour la matière machine learning. »<br>"
    "• 👉 « Donne-moi les feedbacks négatifs cette semaine. »<br>"
    "• 👉 « Affiche moi des graphiques pour la matiere machine learning et la matiere business.»<br>"
    "• 👉 « Donne-moi les graphiques des feedbacks pour la matière finance hier. »<br>"
    "• 👉 « Donne moi les top 3 matières de cette semaine. »<br>"
    "• 👉 « Donne-moi le chart comparatif des feedbacks par matière. »"
, {})



    # 14. Fallback standard
    session['pending_intent'] = None
    session['pending_data'] = {}
    return (
        "Je n'ai pas compris la demande. "
        "Essaye par exemple :\n"
        "- 'Nombre de feedbacks positifs aujourd’hui'\n"
        "- 'Montre-moi le feedback chart.'\n",
        {}
    )
