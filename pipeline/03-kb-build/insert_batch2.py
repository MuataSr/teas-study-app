"""Insert misconceptions M17–M32 into the A&P knowledge base (batch 2)."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ap.db')
conn = sqlite3.connect(DB_PATH)

rows = [
    # ── Nervous System (M17–M22) ──────────────────────────────────────────

    # M17
    (
        "Nervous",
        "Neural Signaling",
        "The brain sends electrical signals through the body at the speed of light.",
        "Neural signals travel 1–120 m/s in myelinated neurons and 0.5–2 m/s in unmyelinated neurons. "
        "This is fast but nowhere near the speed of light (~300,000,000 m/s).",
        "Speed of light",
        "Students equate 'electrical' with 'as fast as electricity/light' without considering the biological medium and resistance of neural tissue.",
        "TEAS 7 frequently tests the difference between neural conduction speed and electrical signal speed in physics-adjacent questions.",
        "ATI Nursing Blog Feb 2025",
    ),
    # M18
    (
        "Nervous",
        "Afferent vs Efferent Pathways",
        "Sensory neurons and motor neurons are the same thing — they just go in different directions.",
        "Afferent (sensory) neurons carry signals TOWARD the CNS. Efferent (motor) neurons carry signals AWAY from the CNS. "
        "Mnemonic: 'Afferent Arrives, Efferent Exits.'",
        "They both carry signals to and from the brain",
        "The terms afferent/efferent sound similar and both describe signal direction, so students merge them into one concept.",
        "Afferent vs efferent is a classic TEAS 7 discrimination item. Appears in both standalone questions and diagram-labeling formats.",
        "McFarland et al. 2017",
    ),
    # M19
    (
        "Nervous",
        "Reflex Arcs",
        "Reflexes don't involve the brain at all — they bypass all higher processing.",
        "Reflexes travel through the spinal cord via a reflex arc: receptor → sensory neuron → interneuron → motor neuron → effector. "
        "The brain is notified afterward via ascending pathways but is NOT part of the reflex loop itself.",
        "Reflexes skip the spinal cord too",
        "Students hear 'reflexes are automatic' and assume that means zero CNS involvement. They forget the spinal cord is CNS tissue.",
        "Reflex arc components are directly tested on TEAS 7. Students must identify the correct sequence and distinguish spinal vs cranial reflexes.",
        "Michael et al. 2007",
    ),
    # M20
    (
        "Nervous",
        "Autonomic Nervous System",
        "Sympathetic and parasympathetic systems can both be active at the same time.",
        "Sympathetic = 'fight or flight' (↑ heart rate, dilates pupils, inhibits digestion). "
        "Parasympathetic = 'rest and digest' (↓ heart rate, constricts pupils, stimulates digestion). "
        "They are antagonistic — one dominates while the other is suppressed.",
        "Both systems speed up heart rate",
        "Students think 'balance' means both systems are equally active simultaneously, when in reality they take turns dominating.",
        "Autonomic nervous system comparisons appear on nearly every TEAS 7 exam. High-yield for matching and 'which of the following' questions.",
        "ATI Nursing Blog Feb 2025",
    ),
    # M21
    (
        "Nervous",
        "CNS vs PNS Division",
        "The CNS includes all nerves in the body.",
        "CNS = brain and spinal cord ONLY. PNS = everything else: cranial nerves, spinal nerves, and ganglia.",
        "CNS includes spinal nerves",
        "Students hear 'central' and assume it encompasses all nerves because nerves seem centrally important.",
        "CNS vs PNS division is foundational for TEAS 7. Misidentifying which structures belong where leads to cascading errors.",
        "Modell et al. 2005",
    ),
    # M22
    (
        "Nervous",
        "Myelin and Saltatory Conduction",
        "Myelin speeds up nerve signals by making the electrical signal stronger.",
        "Myelin speeds signals via saltatory conduction — the action potential 'jumps' between Nodes of Ranvier. "
        "Myelin does NOT amplify the signal strength; it insulates the axon, reducing signal degradation and increasing conduction velocity.",
        "Myelin increases signal strength",
        "Students associate 'faster' with 'stronger' and don't distinguish conduction speed from signal amplitude.",
        "Saltatory conduction is a named process on TEAS 7. Students who don't understand the mechanism pick distractors about signal strength.",
        "McFarland et al. 2017",
    ),

    # ── Endocrine System (M23–M27) ────────────────────────────────────────

    # M23
    (
        "Endocrine",
        "Hormone Function",
        "Hormones work instantly, just like nerve signals.",
        "Hormones are slower-acting (seconds to hours for onset) but longer-lasting (hours to weeks). "
        "The nervous system is fast (milliseconds) and short-duration. Endocrine signals are blood-borne, widespread, and sustained.",
        "Hormones act within milliseconds",
        "Students see hormones as 'chemical signals' and chemical reactions as fast, conflating endocrine signaling with neurotransmission speed.",
        "TEAS 7 directly compares nervous and endocrine systems. Choosing 'instant' for hormone action is a common wrong answer.",
        "ATI Nursing Blog Feb 2025",
    ),
    # M24
    (
        "Endocrine",
        "Hypothalamus-Pituitary Axis",
        "The pituitary gland is the 'master gland' that controls all other glands independently.",
        "The pituitary IS called the master gland, but it is itself controlled by the hypothalamus — a brain region that regulates pituitary hormone release. "
        "The hypothalamus-pituitary axis is a two-way regulatory loop, not a one-way command chain.",
        "The pituitary works alone to control all hormones",
        "Textbooks label the pituitary as 'master gland,' and students stop reading there without noting the hypothalamus above it.",
        "TEAS 7 tests the hierarchical relationship: hypothalamus → pituitary → target glands. Omitting the hypothalamus is a frequent error.",
        "Michael et al. 2007",
    ),
    # M25
    (
        "Endocrine",
        "Feedback Mechanisms",
        "Positive feedback is the 'good' type of feedback that keeps things stable.",
        "Negative feedback is the MOST common mechanism and reverses a change to maintain homeostasis (e.g., thermostat, insulin/glucagon). "
        "Positive feedback amplifies a change until an external event ends it (e.g., childbirth contractions, blood clotting cascade). "
        "'Positive' in physiology means amplification, not 'good.'",
        "Positive feedback maintains homeostasis",
        "Students interpret 'positive' and 'negative' as value judgments rather than directional descriptors of change.",
        "Feedback mechanisms are heavily tested on TEAS 7. Confusing positive with negative feedback is one of the most common wrong-answer patterns.",
        "Modell et al. 2005",
    ),
    # M26
    (
        "Endocrine",
        "Gland-Hormone Pairings",
        "All glands produce the same types of hormones — it doesn't matter which gland is which.",
        "Each endocrine gland produces specific hormones: Thyroid → thyroxine (metabolism), calcitonin (calcium). "
        "Adrenal cortex → cortisol (stress), aldosterone (sodium). Adrenal medulla → epinephrine/norepinephrine. "
        "Pancreas → insulin (↓ blood sugar), glucagon (↑ blood sugar). Ovaries → estrogen, progesterone. "
        "Testes → testosterone. Pineal → melatonin (sleep). Thymus → thymosin (T-cell maturation).",
        "The thyroid produces insulin",
        "Students memorize hormone names but don't anchor them to specific glands. The sheer number of hormones causes interference and mixing.",
        "Gland-hormone matching is a staple TEAS 7 format. This misconception alone can cost 2–3 questions on a single exam.",
        "ATI Nursing Blog Feb 2025",
    ),
    # M27
    (
        "Endocrine",
        "Insulin Mechanism",
        "Insulin lowers blood sugar by burning glucose for energy.",
        "Insulin causes cells (especially muscle and liver) to take up glucose from the bloodstream. "
        "It also promotes glycogen synthesis (storage). Insulin facilitates uptake and storage — it does not itself 'burn' glucose.",
        "Insulin directly breaks down glucose",
        "Students know insulin lowers blood sugar and connect 'lowering' with 'using up/burning' rather than the cellular uptake mechanism.",
        "Insulin/glucagon dynamics are high-yield on TEAS 7. Understanding uptake vs metabolism prevents selecting plausible distractors.",
        "McFarland et al. 2017",
    ),

    # ── Immune/Lymphatic System (M28–M32) ─────────────────────────────────

    # M28
    (
        "Immune",
        "White Blood Cell Types",
        "White blood cells are all the same — they all do the same job of fighting infection.",
        "WBCs have distinct roles: Neutrophils are first responders against bacteria. Lymphocytes (T cells and B cells) handle adaptive immunity and memory. "
        "Monocytes/Macrophages perform phagocytosis and antigen presentation. Eosinophils target parasites and allergies. "
        "Basophils release histamine and promote inflammation.",
        "All WBCs engulf bacteria equally",
        "Students learn 'WBCs fight infection' as a single fact and don't differentiate the five major types and their specialized functions.",
        "TEAS 7 asks students to match WBC types to their functions. Treating all WBCs as identical makes these questions unanswerable.",
        "ATI Nursing Blog Feb 2025",
    ),
    # M29
    (
        "Immune",
        "Antibody Function",
        "Antibodies directly kill pathogens on contact.",
        "Antibodies tag pathogens for destruction (opsonization), neutralize toxins, and activate the complement cascade. "
        "They do NOT kill directly — they mark targets so phagocytes or complement proteins can destroy them.",
        "Antibodies lyse pathogen cells directly",
        "Students see 'antibodies destroy pathogens' in simplified explanations and assume direct killing rather than a tagging/flagging role.",
        "Antibody mechanism questions appear regularly on TEAS 7. Confusing direct vs indirect action leads to wrong answer selection.",
        "Michael et al. 2007",
    ),
    # M30
    (
        "Immune",
        "Innate vs Adaptive Immunity",
        "Innate and adaptive immunity are basically the same system.",
        "Innate immunity is non-specific, acts immediately, and has no memory (skin, mucous membranes, inflammation, phagocytes). "
        "Adaptive immunity is highly specific, takes days to activate, and has immunological memory (B cells/antibodies, T cells). "
        "They work together but are distinct systems.",
        "Innate immunity creates memory cells",
        "Both systems 'fight infection,' so students treat them as interchangeable. The shared outcome masks the different mechanisms.",
        "TEAS 7 directly contrasts innate and adaptive immunity. Students must identify which response is innate vs adaptive in clinical scenarios.",
        "Modell et al. 2005",
    ),
    # M31
    (
        "Immune",
        "Lymphatic-Immune Relationship",
        "The lymphatic system and immune system are completely separate body systems.",
        "The lymphatic system IS a core part of the immune system. Lymph nodes filter pathogens from lymph, the spleen filters blood-borne pathogens, "
        "and the thymus matures T cells. The lymphatic system also returns excess interstitial fluid to the bloodstream.",
        "The lymphatic system only moves fluid",
        "Anatomy textbooks list them as separate chapters, so students assume separate functions without recognizing the overlap.",
        "TEAS 7 expects students to identify lymphatic structures (nodes, spleen, thymus) as immune organs. This crossover is frequently tested.",
        "McFarland et al. 2017",
    ),
    # M32
    (
        "Immune",
        "Vaccine Mechanism",
        "Vaccines give you a mild version of the disease so your body can fight it.",
        "Vaccines expose the immune system to antigens from dead or weakened pathogens (or mRNA instructions for antigen production) "
        "to stimulate memory cell creation WITHOUT causing the actual disease. The immune response builds protection for future encounters.",
        "Vaccines contain live, fully active pathogens",
        "Students hear 'exposure to the pathogen' and conflate antigen exposure with actual infection. Media misinformation reinforces this.",
        "Vaccine questions appear on TEAS 7 in the context of adaptive immunity and memory cells. Understanding the mechanism prevents selecting fear-based distractors.",
        "ATI Nursing Blog Feb 2025",
    ),
]

conn.executemany(
    """INSERT INTO misconceptions
       (body_system, topic, misconception, correct_explanation,
        common_wrong_answer, why_students_err, teas_relevance, source)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    rows,
)

conn.commit()
total = conn.execute("SELECT COUNT(*) FROM misconceptions").fetchone()[0]
print(f"Inserted batch 2: {total} total rows")
conn.close()
