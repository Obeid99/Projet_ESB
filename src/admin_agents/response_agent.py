def format_admin_response(subject, date, counts, total):
    """
    Génère une réponse pour l'admin à partir des stats.
    """
    date_label = "aujourd'hui" if date == "today" else f"le {date}"
    resp = f"Pour le sujet **{subject}** {date_label}, nous avons reçu {total} feedbacks :\n"
    resp += f"- 👍 {counts.get('positive', 0)} positifs\n"
    resp += f"- 👎 {counts.get('negative', 0)} négatifs\n"
    resp += f"- 😐 {counts.get('neutral', 0)} neutres\n"
    resp += "\nVoulez-vous un graphique ou une exportation de ces données ?"
    return resp
