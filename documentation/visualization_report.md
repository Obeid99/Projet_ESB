# visualization.py — Module Documentation

## Overview

The `visualization.py` module generates feedback analytics charts for the ESB admin chatbot. It processes feedback data from MongoDB, aggregates statistics by subject and sentiment, and produces bar and pie charts for use in the admin interface. It also provides comparative interpretations of the results.

---

## Main Functions

### 1. `normalize_subject(text)`
- **Purpose:** Normalizes subject names for robust comparison.
- **How:**
  - Converts to lowercase, removes accents, strips non-alphanumeric characters, collapses spaces.
- **Usage:** Used throughout for matching feedback messages to subjects.

### 2. `extract_subjects_list(subjects, valid_subjects)`
- **Purpose:** Converts a string or list of subject names into a normalized, validated list.
- **How:**
  - Splits on commas, "et", or "and".
  - Normalizes and matches against the valid subjects list.
  - Returns all valid subjects if none are matched.

### 3. `generate_all_feedback_charts_from_mongo(...)`
- **Purpose:** Main analytics and chart generation function.
- **Parameters:**
  - `mongo_db`: MongoDB connection.
  - `subjects`: Subjects to filter (optional).
  - `date`: Date or period ("today", "this_week", etc.).
  - `collection_name`: MongoDB collection.
  - `valid_subjects`: List of valid subjects.
  - `only_sentiment`: Filter by sentiment (optional).
- **How:**
  - Filters feedbacks by date, subject, and sentiment.
  - Aggregates statistics (positive, negative, neutral, total).
  - Generates and saves bar (total/stacked) and pie charts as PNGs.
  - Returns chart URLs and a metadata dictionary (including interpretation and raw data).

---

## Chart Types Generated

- **Bar Chart (Total):** Feedback count per subject.
- **Bar Chart (Stacked):** Feedback count per subject, split by sentiment.
- **Pie Chart:** Proportion of feedbacks per subject.

---

## Example Usage

```python
urls, meta = generate_all_feedback_charts_from_mongo(mongo_db, subjects=["finance", "marketing"], date="this_week")
# urls: {"bar_total": "/static/bar_total.png", ...}
# meta: {"most_positive": ("finance", 10), ...}
```

---

## Integration Points

- **Upstream:** Receives subject/date filters from orchestrator or intent parser.
- **Downstream:** Returns chart URLs and analytics for display in the admin web interface.

---

## Design Notes

- Handles French/English, accents, and subject variations.
- Saves charts to a static directory for easy web serving.
- Provides both raw data and human-readable interpretations.

---

## Limitations

- Assumes feedback messages contain subject names for matching.
- Chart file names are static and may be overwritten on each call.

---

## Summary Table

| Function                        | Purpose                              | Returns                |
|----------------------------------|--------------------------------------|------------------------|
| `normalize_subject`              | Normalize subject for comparison     | String                 |
| `extract_subjects_list`          | Parse/validate subject list          | List of strings        |
| `generate_all_feedback_charts_from_mongo` | Generate charts, stats, meta | (dict, dict)           |

---

## Conclusion

The `visualization.py` module is a key analytics and reporting component, enabling the ESB admin chatbot to present actionable, visual feedback insights to administrators.
