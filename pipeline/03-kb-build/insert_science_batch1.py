#!/usr/bin/env python3
"""Insert TEAS science questions directly into science.db high_yield_qa table.
Batch 1: Anatomy & Physiology (Cardiovascular, Nervous, Endocrine, Muscular) — 32 questions."""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline", "runs", "science", "data", "science.db")

QUESTIONS = [
    # ── Cardiovascular system (8) ──
    {"q": "Which chamber of the heart pumps oxygenated blood to the body?", "a": "Left ventricle", "e": "The left ventricle has the thickest walls and pumps oxygenated blood through the aorta to systemic circulation.", "t": "Cardiovascular system"},
    {"q": "What is the correct pathway of blood flow through the heart?", "a": "Right atrium → right ventricle → lungs → left atrium → left ventricle → body", "e": "Deoxygenated blood enters the right atrium via the vena cava, flows to the right ventricle, goes to the lungs for gas exchange, returns to the left atrium, then left ventricle pumps it to the body.", "t": "Cardiovascular system"},
    {"q": "Which blood vessels carry oxygenated blood away from the heart?", "a": "Arteries", "e": "Arteries (except the pulmonary artery) carry oxygenated blood away from the heart to body tissues.", "t": "Cardiovascular system"},
    {"q": "The pulmonary artery carries what type of blood?", "a": "Deoxygenated blood", "e": "The pulmonary artery is the only artery that carries deoxygenated blood — from the right ventricle to the lungs.", "t": "Cardiovascular system"},
    {"q": "Which valve prevents backflow between the left ventricle and the aorta?", "a": "Aortic valve", "e": "The aortic (semilunar) valve prevents blood from flowing back into the left ventricle after contraction.", "t": "Cardiovascular system"},
    {"q": "What structure separates the left and right sides of the heart?", "a": "Septum", "e": "The interventricular and interatrial septa prevent mixing of oxygenated and deoxygenated blood.", "t": "Cardiovascular system"},
    {"q": "During which phase of the cardiac cycle does the heart relax?", "a": "Diastole", "e": "Diastole is the relaxation phase when the heart chambers fill with blood. Systole is the contraction phase.", "t": "Cardiovascular system"},
    {"q": "Which component of blood is responsible for clotting?", "a": "Platelets", "e": "Platelets (thrombocytes) are cell fragments essential for blood clot formation at injury sites.", "t": "Cardiovascular system"},

    # ── Nervous system (8) ──
    {"q": "Which part of the brain controls balance and coordination?", "a": "Cerebellum", "e": "The cerebellum, located at the base of the brain, coordinates voluntary movement, balance, and posture.", "t": "Nervous system"},
    {"q": "What is the function of the myelin sheath?", "a": "It insulates axons and speeds up nerve impulse transmission", "e": "The myelin sheath is a fatty layer around axons that allows saltatory conduction, dramatically increasing signal speed.", "t": "Nervous system"},
    {"q": "Which division of the autonomic nervous system is responsible for 'rest and digest'?", "a": "Parasympathetic", "e": "The parasympathetic nervous system promotes digestion, slows heart rate, and conserves energy — the opposite of the sympathetic 'fight or flight' response.", "t": "Nervous system"},
    {"q": "Neurotransmitters are released from the:", "a": "Presynaptic terminal", "e": "Neurotransmitters are stored in vesicles in the presynaptic terminal and released into the synaptic cleft when an action potential arrives.", "t": "Nervous system"},
    {"q": "Which lobe of the cerebrum is primarily responsible for processing visual information?", "a": "Occipital lobe", "e": "The occipital lobe at the back of the brain contains the primary visual cortex and processes visual stimuli.", "t": "Nervous system"},
    {"q": "What type of neuron carries signals from the central nervous system to muscles?", "a": "Motor neuron", "e": "Motor (efferent) neurons transmit impulses from the CNS to effectors like muscles and glands.", "t": "Nervous system"},
    {"q": "The blood-brain barrier is formed primarily by:", "a": "Tight junctions between endothelial cells of brain capillaries", "e": "The BBB is formed by endothelial cells with tight junctions that restrict passage of substances from the bloodstream into brain tissue.", "t": "Nervous system"},
    {"q": "Which cranial nerve controls the muscles of facial expression?", "a": "Facial nerve (CN VII)", "e": "The facial nerve (cranial nerve VII) is a motor nerve that innervates the muscles of facial expression.", "t": "Nervous system"},

    # ── Endocrine system (8) ──
    {"q": "Which gland is known as the 'master gland' of the endocrine system?", "a": "Pituitary gland", "e": "The pituitary gland secretes hormones that regulate other endocrine glands, including TSH, ACTH, and FSH.", "t": "Endocrine system"},
    {"q": "Insulin is produced by which cells in the pancreas?", "a": "Beta cells of the islets of Langerhans", "e": "Beta (β) cells in the pancreatic islets produce insulin, which lowers blood glucose by promoting cellular glucose uptake.", "t": "Endocrine system"},
    {"q": "Which hormone is responsible for the 'fight or flight' response?", "a": "Epinephrine", "e": "Epinephrine (adrenaline) from the adrenal medulla increases heart rate, blood pressure, and blood glucose during stress.", "t": "Endocrine system"},
    {"q": "What is the primary function of antidiuretic hormone (ADH)?", "a": "It promotes water reabsorption in the kidneys", "e": "ADH (vasopressin) acts on the kidneys to increase water reabsorption, concentrating urine and reducing water loss.", "t": "Endocrine system"},
    {"q": "Which hormone regulates calcium levels in the blood?", "a": "Parathyroid hormone (PTH)", "e": "PTH from the parathyroid glands increases blood calcium by stimulating bone resorption, kidney reabsorption, and intestinal absorption.", "t": "Endocrine system"},
    {"q": "Thyroid-stimulating hormone (TSH) is released by which gland?", "a": "Anterior pituitary", "e": "TSH is produced by the anterior pituitary and stimulates the thyroid gland to produce T3 and T4 hormones.", "t": "Endocrine system"},
    {"q": "Which endocrine gland sits atop the kidneys?", "a": "Adrenal glands", "e": "The adrenal (suprarenal) glands are located on top of each kidney and produce cortisol, aldosterone, and epinephrine.", "t": "Endocrine system"},
    {"q": "Oxytocin is produced by which structure?", "a": "Hypothalamus (stored and released by posterior pituitary)", "e": "Oxytocin is synthesized in the hypothalamus but stored in and released from the posterior pituitary gland. It stimulates uterine contractions and milk ejection.", "t": "Endocrine system"},

    # ── Muscular system (8) ──
    {"q": "Which type of muscle tissue is found in the walls of hollow organs like the stomach?", "a": "Smooth muscle", "e": "Smooth muscle is involuntary, non-striated muscle found in the walls of hollow organs, blood vessels, and the digestive tract.", "t": "Muscular system"},
    {"q": "What is the functional unit of a muscle fiber?", "a": "Sarcomere", "e": "The sarcomere is the repeating contractile unit between Z-lines in a myofibril, composed of actin (thin) and myosin (thick) filaments.", "t": "Muscular system"},
    {"q": "During muscle contraction, which protein binds to calcium ions?", "a": "Troponin", "e": "Troponin binds calcium, causing a conformational change that moves tropomyosin away from actin's myosin-binding sites, allowing contraction.", "t": "Muscular system"},
    {"q": "Which energy source is used first during intense muscle contraction?", "a": "ATP stored in muscle cells", "e": "Muscles use stored ATP first (enough for ~3 seconds), then creatine phosphate, then glycogen via anaerobic glycolysis, then aerobic respiration.", "t": "Muscular system"},
    {"q": "What is the role of acetylcholine at the neuromuscular junction?", "a": "It stimulates the muscle fiber to contract", "e": "Acetylcholine released from the motor neuron binds to receptors on the muscle fiber membrane, triggering an action potential and muscle contraction.", "t": "Muscular system"},
    {"q": "Which type of muscle contraction occurs when the muscle lengthens while generating force?", "a": "Eccentric contraction", "e": "Eccentric contractions lengthen the muscle while under tension (e.g., lowering a weight). Concentric shortens the muscle, and isometric maintains length.", "t": "Muscular system"},
    {"q": "The origin of a muscle is attached to:", "a": "The immovable (or less movable) bone", "e": "The origin is the tendon attachment on the more stable bone; the insertion attaches to the bone that moves during contraction.", "t": "Muscular system"},
    {"q": "Which protein makes up the thick filaments in a sarcomere?", "a": "Myosin", "e": "Myosin forms the thick filaments. During contraction, myosin heads bind to actin (thin filaments) and pull them toward the center of the sarcomere.", "t": "Muscular system"},
]

def main():
    conn = sqlite3.connect(DB_PATH)
    count = 0
    for q in QUESTIONS:
        conn.execute(
            "INSERT INTO high_yield_qa (question, correct_answer, explanation, body_system, created_at) VALUES (?, ?, ?, ?, ?)",
            (q["q"], q["a"], q["e"], q["t"], int(time.time())),
        )
        count += 1
    conn.commit()
    conn.close()
    print(f"Inserted {count} questions")

if __name__ == "__main__":
    main()
