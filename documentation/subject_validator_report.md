# subject_validator.py — Module Documentation

## Overview

The `subject_validator.py` module provides subject normalization and validation utilities for the ESB admin chatbot. It ensures that subject names (matières) extracted from user/admin queries are matched robustly against the official list, regardless of accents, case, or minor variations.

---

## Main Components

### 1. `VALID_SUBJECTS`
- **Purpose:** Set of all official subject names (matières) recognized by the system.
- **Usage:** Used for validation and normalization checks throughout the pipeline.

### 2. `strip_accents(text)`
- **Purpose:** Removes all accents from a string for robust comparison.
- **How:** Uses Unicode normalization to strip diacritics.

### 3. `normalize_subject(subject)`
- **Purpose:** Normalizes a subject string for comparison.
- **How:**
  - Strips whitespace, converts to lowercase.
  - Removes accents.
  - Collapses multiple spaces.
- **Usage:** Used before any subject comparison or validation.

### 4. `is_valid_subject(subject)`
- **Purpose:** Checks if a given subject matches any in the official list.
- **How:**
  - Normalizes the input subject and all valid subjects.
  - Returns `True` if a match is found, else `False`.

---

## Example Usage

```python
is_valid = is_valid_subject("Mathématiques")  # True
norm = normalize_subject("Comptabilité")      # "comptabilite"
```

---

## Integration Points

- **Upstream:** Receives subject strings from intent/entity extraction modules.
- **Downstream:** Used by orchestrator and visualization modules to ensure only valid subjects are processed.

---

## Design Notes

- Handles French/English, accents, and common spelling variations.
- Centralizes subject validation logic for consistency across the system.

---

## Limitations

- The list of valid subjects is static and must be updated manually if the curriculum changes.

---

## Summary Table

| Function             | Purpose                        | Returns         |
|----------------------|--------------------------------|-----------------|
| `strip_accents`      | Remove accents from string     | String          |
| `normalize_subject`  | Normalize subject for compare  | String          |
| `is_valid_subject`   | Validate subject against list  | Boolean         |

---

## Conclusion

The `subject_validator.py` module is essential for robust, user-friendly subject handling in the ESB admin chatbot, ensuring that all subject-based queries are matched accurately and consistently.
