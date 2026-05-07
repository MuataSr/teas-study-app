"""Insert batch 1: misconceptions M1–M16 into the TEAS A&P Knowledge Base."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ap.db')
conn = sqlite3.connect(DB_PATH)

misconceptions = [
    # ── Cardiovascular System (M1–M6) ──────────────────────────────────────
    (
        "Cardiovascular", "Blood Vessels",
        "Arteries ALWAYS carry oxygenated blood and veins ALWAYS carry deoxygenated blood.",
        "Pulmonary arteries carry deoxygenated blood from the right ventricle to the lungs, and pulmonary veins carry oxygenated blood from the lungs to the left atrium. The defining feature of arteries and veins is direction of blood flow (away from vs. toward the heart), not oxygenation status.",
        "Pulmonary arteries carry oxygenated blood",
        "Students memorize the rule 'arteries = oxygenated, veins = deoxygenated' from diagrams of systemic circulation and overgeneralize it to the entire circulatory system without accounting for the pulmonary circuit.",
        "TEAS 7 frequently tests the pulmonary circuit and asks students to identify exceptions to the general artery/vein rule.",
        "ATI Nursing Blog (2025)",
    ),
    (
        "Cardiovascular", "Blood Composition",
        "Deoxygenated blood is blue.",
        "Blood is always red. Deoxygenated blood is dark red due to reduced hemoglobin; oxygenated blood is bright red due to oxyhemoglobin. Veins appear blue through the skin because of how light penetrates and scatters through tissue, not because the blood itself is blue.",
        "Blue",
        "Textbooks sometimes use blue and red to color-code vessels in diagrams, leading students to believe deoxygenated blood is literally blue.",
        "Understanding blood composition and hemoglobin oxygenation is tested directly on TEAS 7 science questions.",
        "Michael et al. (2002)",
    ),
    (
        "Cardiovascular", "Coronary Circulation",
        "The heart pumps blood to itself.",
        "The heart does not pump blood to itself directly from its chambers. Coronary arteries branch off the base of the aorta just above the aortic valve and supply the myocardium with oxygenated blood. Blockage of a coronary artery causes a myocardial infarction (heart attack) because heart muscle is deprived of oxygen.",
        "Blood from the left ventricle flows directly into heart muscle",
        "Students assume that because the heart is full of blood, it automatically nourishes its own tissue. They overlook the separate coronary circulation that serves the myocardium.",
        "Coronary circulation is a high-yield TEAS 7 topic; questions may ask about coronary artery disease, heart attacks, and the pathway of coronary blood flow.",
        "McFarland et al. (2017)",
    ),
    (
        "Cardiovascular", "Heart Chambers",
        "Both sides of the heart pump blood to the same place.",
        "The right side of the heart pumps deoxygenated blood to the lungs via the pulmonary circuit. The left side of the heart pumps oxygenated blood to the entire body via the systemic circuit. Each side has a distinct function and serves a different circulation.",
        "Both ventricles pump blood to the body",
        "Students see the heart as a single pump rather than two parallel pumps. They may confuse which ventricle is thicker (left, for systemic pressure) or which side handles oxygenated vs. deoxygenated blood.",
        "TEAS 7 commonly asks students to trace blood flow through the heart and distinguish pulmonary from systemic circulation.",
        "ATI Nursing Blog (2025)",
    ),
    (
        "Cardiovascular", "Heart Structures",
        "Heart chambers and heart valves are the same thing or serve the same purpose.",
        "Heart chambers (atria and ventricles) receive and pump blood. Heart valves (tricuspid, mitral/bicuspid, pulmonary, aortic) prevent backflow between chambers and into vessels. For example, the right atrium receives deoxygenated blood from the body, while the mitral (bicuspid) valve prevents backflow from the left ventricle into the left atrium.",
        "The mitral valve receives deoxygenated blood from the body",
        "Students conflate chambers (containers) with valves (one-way doors) because they learn them together in the same diagram. On multiple choice, they may pick a valve when asked about a chamber or vice versa.",
        "Distinguishing chambers from valves and knowing their names/functions is a repeated TEAS 7 test item.",
        "Modell et al. (2005)",
    ),
    (
        "Cardiovascular", "Blood Vessels",
        "Capillaries are the strongest blood vessels because they connect arteries and veins.",
        "Capillaries are the thinnest blood vessels — their walls are only one cell (endothelium) thick. This thinness allows gas exchange, nutrient diffusion, and waste removal. Arteries have the thickest walls (three layers including thick smooth muscle and elastic tissue) to withstand high blood pressure from the heart.",
        "Capillaries have the thickest walls to handle high pressure",
        "Students associate importance or critical function with physical strength. Since capillaries are where the 'important work' of exchange happens, they assume capillaries must be the strongest vessels.",
        "TEAS 7 tests the structural differences between vessel types and asks students to match structure to function.",
        "Michael et al. (2007)",
    ),

    # ── Respiratory System (M7–M11) ────────────────────────────────────────
    (
        "Respiratory", "Gas Composition",
        "We breathe in oxygen and breathe out carbon dioxide — that's all there is in air.",
        "Inhaled air is ~78% nitrogen, ~21% oxygen, ~0.04% CO2, and trace gases. Exhaled air is ~78% nitrogen, ~16% oxygen, ~4% CO2, and water vapor. The percentages of oxygen and CO2 change, but nitrogen remains nearly constant and is the dominant gas in both.",
        "Exhaled air is mostly carbon dioxide",
        "The simplified narrative of 'oxygen in, CO2 out' leads students to believe exhaled air is predominantly CO2, when in fact the majority of exhaled air is still nitrogen.",
        "TEAS 7 may include questions about gas composition of inhaled vs. exhaled air or Dalton's law of partial pressures.",
        "Michael et al. (2002)",
    ),
    (
        "Respiratory", "Respiratory Muscles",
        "The diaphragm is a muscle in the stomach area.",
        "The diaphragm is a dome-shaped skeletal muscle that separates the thoracic cavity (containing lungs and heart) from the abdominal cavity (containing digestive organs). During inhalation, it contracts and flattens, increasing thoracic volume and decreasing pressure to draw air into the lungs.",
        "The diaphragm is located in the stomach and aids digestion",
        "Students confuse 'diaphragm' with the digestive system because of its location near the abdomen and its unfamiliar name. The term sounds digestive to many learners.",
        "The diaphragm's role in negative-pressure breathing is a core TEAS 7 concept tested in both science and anatomy questions.",
        "McFarland et al. (2017)",
    ),
    (
        "Respiratory", "Airway Structures",
        "Bronchi and bronchioles are the same thing.",
        "Bronchi (singular: bronchus) are the large passageways that branch from the trachea into each lung; they contain cartilage rings for structural support. Bronchioles are smaller branches downstream of the bronchi that lack cartilage and lead directly to alveolar sacs. Gas exchange occurs only at the alveoli, not in bronchi or bronchioles.",
        "Gas exchange occurs in the bronchioles",
        "The similar names and adjacent positions cause students to treat bronchi and bronchioles as interchangeable. They also incorrectly assume gas exchange happens throughout the airway rather than only at alveoli.",
        "TEAS 7 frequently asks students to identify where gas exchange occurs and to distinguish bronchi from bronchioles structurally.",
        "Modell et al. (2005)",
    ),
    (
        "Respiratory", "Gas Exchange",
        "Oxygen is actively pulled into the blood during breathing.",
        "Oxygen and CO2 move across the alveolar-capillary membrane by passive diffusion driven by concentration (partial pressure) gradients. Oxygen diffuses from alveoli (high PO2) into pulmonary capillaries (low PO2), and CO2 diffuses from capillaries (high PCO2) into alveoli (low PCO2). No energy is required for this process.",
        "Oxygen is actively transported into blood by the lungs",
        "Students assume that because breathing is an active process (muscle contraction), the actual gas exchange must also be active. They fail to separate the mechanical act of ventilation from the passive process of diffusion.",
        "Understanding passive diffusion vs. active transport in gas exchange is a high-yield distinction on TEAS 7 science questions.",
        "Michael et al. (2007)",
    ),
    (
        "Respiratory", "Lung Volumes",
        "Tidal volume, vital capacity, and residual volume all refer to normal breathing amounts.",
        "Tidal volume (~500 mL) is the amount of air inhaled or exhaled during normal, quiet breathing. Vital capacity is the maximum amount of air that can be exhaled after a maximum inhalation (~4,500–5,500 mL). Residual volume (~1,200 mL) is the air that remains in the lungs after maximum exhalation, preventing lung collapse.",
        "Vital capacity is the same as tidal volume",
        "All three terms describe 'amounts of air in lungs,' so students group them together without recognizing the distinct conditions each measures (normal breath vs. maximum effort vs. air that never leaves).",
        "TEAS 7 regularly tests lung volumes and capacities, often asking students to calculate or identify them from a spirometry graph.",
        "ATI Nursing Blog (2025)",
    ),

    # ── Digestive System (M12–M16) ─────────────────────────────────────────
    (
        "Digestive", "Nutrient Absorption",
        "The stomach does most of the nutrient absorption.",
        "The stomach primarily digests proteins using hydrochloric acid (HCl) and pepsin. Very limited absorption occurs here (water, alcohol, some medications). Over 90% of nutrient absorption — carbohydrates, proteins, fats, vitamins, minerals — occurs in the small intestine, specifically the jejunum and ileum, aided by villi and microvilli.",
        "The stomach absorbs most nutrients",
        "Students associate the stomach with food processing and assume 'processing' includes absorption. The stomach's prominent role in digestion leads them to overestimate its absorptive function.",
        "TEAS 7 frequently asks where nutrient absorption occurs and which organs are responsible for digestion vs. absorption.",
        "McFarland et al. (2017)",
    ),
    (
        "Digestive", "Large Intestine Function",
        "The large intestine absorbs nutrients from food.",
        "The large intestine (colon) primarily absorbs water and electrolytes (sodium, chloride) from indigestible material, forming solid feces. It houses beneficial gut bacteria that produce some vitamins (K, B), but it does not perform significant nutrient absorption from ingested food. Virtually all nutrient absorption is complete by the time chyme reaches the large intestine.",
        "The colon absorbs proteins and carbohydrates",
        "Students see the large intestine as a later stage in the digestive tract and assume it continues absorbing nutrients, just 'more thoroughly.' The word 'intestine' triggers the same association as 'small intestine.'",
        "Distinguishing the functions of the small vs. large intestine is a consistent TEAS 7 topic, often appearing as a direct comparison question.",
        "Michael et al. (2002)",
    ),
    (
        "Digestive", "Accessory Organs",
        "The pancreas, liver, and gallbladder all produce digestive enzymes that do the same thing.",
        "These three accessory organs have distinct roles. The pancreas produces digestive enzymes (lipase, amylase, trypsin) and bicarbonate to neutralize stomach acid. The liver produces bile, which emulsifies fats. The gallbladder stores and concentrates bile, releasing it into the small intestine when needed. None of them perform the same function.",
        "The liver produces digestive enzymes like the pancreas",
        "All three are accessory organs that contribute to digestion, so students group them as 'enzyme producers.' They don't differentiate between enzyme production (pancreas), bile production (liver), and bile storage (gallbladder).",
        "TEAS 7 tests the specific roles of each accessory organ and may ask students to match an organ to its secretory product.",
        "Modell et al. (2005)",
    ),
    (
        "Digestive", "Intestinal Anatomy",
        "The small intestine is called 'small' because it's short.",
        "The small intestine is approximately 20 feet (6 meters) long — much longer than the large intestine (~5 feet). It is called 'small' because of its narrow diameter (~1 inch), compared to the large intestine's wider diameter (~2.5 inches). Its length, combined with villi and microvilli, provides enormous surface area for absorption.",
        "The small intestine is shorter than the large intestine",
        "Students assume the name reflects length because that is the more intuitive interpretation. They may also guess that the large intestine is longer because 'large' implies bigger in every dimension.",
        "TEAS 7 may include questions about intestinal length, diameter, or surface area adaptations (villi/microvilli) for absorption.",
        "ATI Nursing Blog (2025)",
    ),
    (
        "Digestive", "Digestive Motility",
        "Peristalsis and segmentation are the same type of movement in the digestive tract.",
        "Peristalsis is wave-like, one-directional muscular contractions that propel food forward through the GI tract (esophagus to anus). Segmentation is rhythmic, back-and-forth contractions in the small intestine that mix chyme with digestive enzymes but do not move food forward. Both are essential but serve different purposes.",
        "Segmentation moves food through the intestines like peristalsis",
        "Both involve smooth muscle contractions in the digestive tract, so students treat them as interchangeable. They may not realize that segmentation is localized mixing while peristalsis is directional propulsion.",
        "TEAS 7 may ask students to differentiate peristalsis from segmentation or identify which process propels food vs. mixes it.",
        "Michael et al. (1999)",
    ),
]

conn.executemany(
    """INSERT INTO misconceptions
       (body_system, topic, misconception, correct_explanation,
        common_wrong_answer, why_students_err, teas_relevance, source)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    misconceptions,
)

conn.commit()
print(f"Inserted batch 1: {conn.execute('SELECT COUNT(*) FROM misconceptions').fetchone()[0]} total rows")
conn.close()
