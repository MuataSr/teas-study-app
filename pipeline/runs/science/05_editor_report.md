# Editor Report — TEAS 7 Science

## Counts
- Misconceptions: 26 → 27 (+1)
- Q&A pairs: 33 → 33 (+0)

## Applied SQL
```sql
-- EDITOR CHANGES FOLLOW
INSERT INTO misconceptions (body_system, topic, misconception, correct_explanation, common_wrong_answer, why_students_err, teas_relevance, source) VALUES ('Anatomy & Physiology', 'Muscular system', 'Skeletal muscle contraction occurs when the muscle fibers physically shorten and pull on the bone directly.', 'Skeletal muscle contraction occurs via the sliding filament mechanism. Actin (thin) and myosin (thick) filaments slide past each other, but the individual filaments do not shorten. The sarcomere shortens as the Z-lines are pulled closer together by cross-bridge cycling between actin and myosin, powered by ATP.', 'Selecting "the actin filaments shorten" when asked what happens during muscle contraction.', 'Students visualize muscle contraction as a simple shortening of structures rather than understanding the molecular sliding mechanism. The term "contraction" implies getting smaller, which misleads them about what is actually happening at the filament level.', 'The TEAS 7 tests understanding of the sliding filament theory and the roles of actin, myosin, and ATP in muscle contraction.', 'Marieb, E. N., & Hoehn, K. (2019). Human Anatomy & Physiology (11th ed.). Pearson.');
```

## Status
PASS
