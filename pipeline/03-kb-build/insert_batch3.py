import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ap.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ── Misconceptions M33–M51 ──────────────────────────────────────────

misconceptions = [
    # ── Muscular System (M33–M36) ──
    (
        "Muscular", "Muscle Types",
        "All muscle tissue is the same",
        "Three distinct types exist: Skeletal (voluntary, striated, multi-nucleated, attached to bones), Cardiac (involuntary, striated, single-nucleated, intercalated discs, found only in the heart), and Smooth (involuntary, non-striated, spindle-shaped, walls of hollow organs). Each has a different structure, control mechanism, and function.",
        "Smooth muscle",
        "Students see 'muscle' as one category and don't differentiate the three tissue types that look and function very differently.",
        "TEAS 7 frequently asks you to identify muscle types by their characteristics (striation, nucleus count, voluntary vs. involuntary control).",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Muscular", "Muscle Contraction",
        "Muscles push bones to create movement",
        "Muscles ONLY pull (contract); they never push. They work in antagonistic pairs — when one muscle contracts (agonist), its partner relaxes (antagonist). Example: biceps contracts to flex the arm while triceps relaxes; the reverse extends the arm.",
        "Muscles push and pull equally",
        "Students visualize movement as a push because the bone moves outward, but the underlying mechanism is always a pull (contraction).",
        "Antagonistic muscle pairs and the pull-only mechanism of contraction are tested directly on the TEAS.",
        "McFarland et al. 2017"
    ),
    (
        "Muscular", "Origin and Insertion",
        "Origin and insertion are interchangeable terms for where muscles attach to bones",
        "Origin = attachment to the stationary (usually proximal) bone. Insertion = attachment to the moving (usually distal) bone. When a muscle contracts, it pulls the insertion toward the origin. The origin is typically the less movable attachment point.",
        "Insertion is always on the proximal bone",
        "Students memorize the terms without understanding the functional distinction between the stationary and moving attachment points.",
        "Origin vs. insertion questions appear regularly; knowing which end moves is key to answering movement-based questions.",
        "Michael et al. 2007"
    ),
    (
        "Muscular", "Cardiac Muscle Properties",
        "Cardiac muscle can cramp or spasm like skeletal muscle",
        "Cardiac muscle is autorhythmic — it generates its own impulses via pacemaker cells (SA node) and does not require nervous stimulation to contract. It cannot voluntarily cramp. Intercalated discs connect cardiac cells and allow synchronized, wave-like contraction essential for pumping blood.",
        "Cardiac muscle requires nerve signals for every beat",
        "Students extend their experience with skeletal muscle cramps to cardiac muscle, not realizing cardiac muscle has unique autorhythmic properties.",
        "Understanding cardiac muscle's autorhythmicity and intercalated discs is essential for cardiovascular system questions on the TEAS.",
        "ATI Nursing Blog Feb 2025"
    ),

    # ── Skeletal System (M37–M40) ──
    (
        "Skeletal", "Bone Composition",
        "Bones are dead, dry, inert structures",
        "Bones are living tissue with a rich blood supply, nerves, and ongoing remodeling. Osteoblasts build new bone matrix while osteoclasts break down old bone. The entire skeleton is approximately replaced every 10 years through this continuous remodeling process.",
        "Bones stop changing after growth plates close",
        "Students see skeletons in classrooms (dry, bleached) and assume living bone is the same — static and non-living.",
        "Bone remodeling, osteoblasts vs. osteoclasts, and calcium homeostasis are high-yield TEAS topics.",
        "McFarland et al. 2017"
    ),
    (
        "Skeletal", "Skull Structure",
        "The skull is one solid, unbroken bone",
        "The adult skull consists of 22 separate bones: 8 cranial bones (frontal, 2 parietal, 2 temporal, occipital, sphenoid, ethmoid) and 14 facial bones. In infants, several of these bones are not fully fused, leaving soft spots called fontanelles that allow for birth and brain growth.",
        "The skull has 14 bones total",
        "Students feel their skull as one solid structure and assume it is a single bone, overlooking the sutures and multiple bone plates.",
        "TEAS questions test skull bone count, fontanelle function, and the distinction between cranial and facial bones.",
        "Michael et al. 2007"
    ),
    (
        "Skeletal", "Skeleton Divisions",
        "Axial and appendicular skeleton are the same thing or hard to distinguish",
        "Axial skeleton = 80 bones (skull, vertebral column, rib cage/sternum) — forms the central axis. Appendicular skeleton = 126 bones (limbs and girdles — pectoral and pelvic) — attached to the axial skeleton. Total = 206 bones.",
        "The appendicular skeleton includes the skull",
        "Students mix up which bones belong to each division because the names are similar and both sound anatomical.",
        "Knowing the 80/126 split and which bones belong to each division is a classic TEAS recall question.",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Skeletal", "Joint Classification",
        "Joints are simply where two bones meet, with no functional classification",
        "Joints are classified by their degree of movement: Synovial joints = freely movable (knee, elbow, shoulder — fluid-filled cavity), Cartilaginous joints = slightly movable (vertebrae, ribs — connected by cartilage), Fibrous joints = immovable (skull sutures — connected by fibrous tissue).",
        "All joints are freely movable",
        "Students think of joints like the knee or elbow and assume all joints allow movement, missing the structural classification system.",
        "Joint classification (synovial, cartilaginous, fibrous) and examples of each type are frequently tested on the TEAS.",
        "McFarland et al. 2017"
    ),

    # ── Reproductive System (M41–M45) ──
    (
        "Reproductive", "Fertilization Location",
        "Fertilization occurs in the uterus",
        "Fertilization occurs in the fallopian tube (oviduct), typically in the ampulla region. After fertilization, the zygote travels down the fallopian tube over 3–5 days and implants in the uterine lining (endometrium). Ectopic pregnancies occur when implantation happens outside the uterus.",
        "Fertilization occurs in the ovary",
        "Students assume that since the uterus is where the baby grows, fertilization must happen there. The actual site (fallopian tube) is counterintuitive.",
        "Fertilization location is one of the most commonly tested reproductive facts on the TEAS 7.",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Reproductive", "Gamete Production",
        "Men and women produce gametes continuously throughout life",
        "Men produce sperm continuously from puberty onward (spermatogenesis). Women are born with all the oocytes they will ever have (~1–2 million at birth, ~300,000–400,000 at puberty, ~400 ovulated). This is a key difference between male and female gametogenesis.",
        "Women produce new eggs each month",
        "Students hear 'egg release' each month and assume new eggs are being created, not realizing females have a finite supply determined before birth.",
        "Understanding the difference in gamete production timelines is tested in reproductive system questions.",
        "McFarland et al. 2017"
    ),
    (
        "Reproductive", "Menstrual Cycle Phases",
        "The menstrual cycle is just the period — bleeding and nothing more",
        "The menstrual cycle has four hormone-driven phases: Menstrual phase (days 1–5, uterine lining sheds), Follicular phase (days 1–13, follicle matures, estrogen rises), Ovulation (~day 14, LH surge triggers egg release), and Luteal phase (days 15–28, corpus luteum produces progesterone). FSH, LH, estrogen, and progesterone each regulate specific phases.",
        "Ovulation happens at the end of the cycle",
        "Students simplify the cycle to 'the period' and miss the complex hormonal orchestration across the full 28-day cycle.",
        "The TEAS tests menstrual cycle phases, timing of ovulation, and which hormones control each phase.",
        "Michael et al. 2007"
    ),
    (
        "Reproductive", "Placenta Structure",
        "The placenta is part of the mother's body",
        "The placenta is a temporary organ formed from BOTH maternal tissue (decidua basalis of the uterus) and fetal tissue (chorionic villi from the embryo). It facilitates nutrient, gas, and waste exchange between maternal and fetal blood (blood does NOT mix directly). It also produces hormones including hCG, progesterone, and estrogen.",
        "The placenta is made entirely from maternal tissue",
        "Students assume the placenta belongs to the mother since it is inside her body, missing the fetal contribution and its role as a shared organ.",
        "Placenta structure and function, including its dual origin and hormone production, are tested on the TEAS.",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Reproductive", "Meiosis vs. Mitosis",
        "Meiosis and mitosis are basically the same process",
        "Mitosis = cell division for growth and repair; produces 2 identical diploid (2n) daughter cells; one division. Meiosis = cell division for gamete production; produces 4 non-identical haploid (n) daughter cells; two divisions (Meiosis I and II); includes crossing over and independent assortment for genetic diversity.",
        "Both mitosis and meiosis produce 2 identical cells",
        "Students confuse the two processes because both involve cell division, but the outcomes (diploid vs. haploid, identical vs. diverse) are fundamentally different.",
        "Comparing mitosis and meiosis — especially chromosome number, number of divisions, and genetic variation — is heavily tested on the TEAS.",
        "McFarland et al. 2017"
    ),

    # ── Integumentary System (M46–M48) ──
    (
        "Integumentary", "Skin Functions",
        "The skin is just a covering or wrapping for the body",
        "The skin (integumentary system) is the body's largest organ (~20 sq ft in adults). Its functions include: protection (physical barrier against pathogens and UV), temperature regulation (sweat production, vasodilation/vasoconstriction), sensation (touch, pain, temperature receptors), vitamin D synthesis (UV exposure converts cholesterol), and excretion (small amounts of waste via sweat).",
        "The liver is the largest organ",
        "Students underestimate the skin because it is visible and familiar, not realizing it is classified as an organ with multiple critical functions.",
        "Skin functions, especially vitamin D synthesis and thermoregulation, are direct TEAS questions.",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Integumentary", "Skin Layers",
        "All three layers of skin are basically the same tissue",
        "Epidermis (outermost) — keratinized stratified squamous epithelium, contains melanocytes, NO blood vessels (avascular). Dermis (middle) — dense irregular connective tissue with blood vessels, nerve endings, hair follicles, and sweat glands. Hypodermis (deepest) — subcutaneous fat layer for insulation and cushioning; not technically part of the integument but grouped with it.",
        "Blood vessels are found in the epidermis",
        "Students treat 'skin' as one uniform layer, not realizing each layer has distinct cell types, structures, and functions.",
        "Identifying which skin layer contains specific structures (blood vessels, melanocytes, nerve endings) is a common TEAS format.",
        "Michael et al. 2007"
    ),
    (
        "Integumentary", "Melanin Function",
        "Melanin's only purpose is to give skin its tan color",
        "Melanin is a pigment that protects skin cells from UV radiation damage. More melanin = more UV protection (darker skin = lower skin cancer risk but still needs protection). Albinism is a genetic condition where melanocytes are present but cannot produce melanin — it is NOT the absence of melanocytes. Melanin also determines hair and eye color.",
        "Melanin causes skin cancer",
        "Students associate melanin only with tanning/aesthetics and don't understand its protective biological role against UV damage.",
        "Melanin function, UV protection, and albinism are tested in integumentary system questions on the TEAS.",
        "McFarland et al. 2017"
    ),

    # ── Urinary System (M49–M51) ──
    (
        "Urinary", "Kidney Functions",
        "The kidneys just make urine and that's their only job",
        "Kidneys filter ~180 liters of blood per day but reabsorb 99% of the filtrate, producing only ~1–2 liters of urine. Beyond urine production, kidneys: regulate water and electrolyte balance (Na+, K+, Ca2+), maintain blood pH, produce erythropoietin (stimulates RBC production in bone marrow), and activate vitamin D (convert to calcitriol for calcium absorption).",
        "Kidneys only filter waste",
        "Students reduce kidney function to 'making pee' and miss the critical roles in blood pressure, pH balance, and hormone production.",
        "TEAS questions test kidney functions beyond urine — especially erythropoietin production and vitamin D activation.",
        "ATI Nursing Blog Feb 2025"
    ),
    (
        "Urinary", "Urine Composition",
        "Urine is just waste water with nothing else in it",
        "Normal urine is ~95% water. Key solutes include: urea (nitrogenous waste from protein breakdown — main nitrogenous waste in humans), salts (NaCl, KCl), creatinine (muscle metabolism waste), uric acid (purine breakdown), and urobilin (gives urine its yellow color — a breakdown product of bilirubin from hemoglobin). Changes in composition can indicate disease.",
        "Urine is 100% water",
        "Students assume urine is pure water because it is mostly liquid, overlooking the dissolved waste products that give it diagnostic value.",
        "Urine composition and the significance of specific components (urea, urobilin, creatinine) appear in TEAS questions.",
        "McFarland et al. 2017"
    ),
    (
        "Urinary", "Nephron Pathway",
        "Urine just flows through the kidney without a specific pathway",
        "Urine formation follows a specific path through the nephron: Blood enters via renal artery → afferent arteriole → glomerulus (filtration of blood) → Bowman's capsule (collects filtrate) → proximal convoluted tubule (PCT — majority of reabsorption) → Loop of Henle (concentrates urine via countercurrent multiplier) → distal convoluted tubule (DCT — fine-tuning of electrolytes) → collecting duct → renal pelvis → ureter → bladder → urethra.",
        "Filtrate goes directly from glomerulus to bladder",
        "Students skip the nephron tubule system entirely, not realizing the complex reabsorption and concentration steps between filtration and excretion.",
        "The nephron pathway and what happens at each segment (especially PCT reabsorption and Loop of Henle concentration) is heavily tested.",
        "Michael et al. 2007"
    ),
]

c.executemany(
    """INSERT INTO misconceptions
       (body_system, topic, misconception, correct_explanation,
        common_wrong_answer, why_students_err, teas_relevance, source)
       VALUES (?,?,?,?,?,?,?,?)""",
    misconceptions
)

# ── High-Yield Q&As ──────────────────────────────────────────────────

high_yield_qas = [
    (
        "Which chamber of the heart pumps oxygenated blood to the body?",
        "Left ventricle",
        "The right side of the heart pumps deoxygenated blood to the lungs (pulmonary circuit). The left ventricle is the thickest-walled chamber because it must generate enough pressure to pump oxygenated blood through the aorta to the entire systemic circulation.",
        "Cardiovascular"
    ),
    (
        "What type of blood vessel allows gas and nutrient exchange between blood and tissues?",
        "Capillaries",
        "Capillaries are the smallest blood vessels with walls only one cell thick (simple squamous epithelium). This thin wall allows for diffusion of oxygen, carbon dioxide, nutrients, and waste between blood and surrounding tissues. Arteries carry blood away from the heart; veins return blood to the heart.",
        "Cardiovascular"
    ),
    (
        "Which type of muscle tissue is found exclusively in the heart?",
        "Cardiac muscle",
        "Cardiac muscle is found only in the heart wall (myocardium). It is striated like skeletal muscle but involuntary like smooth muscle. It has intercalated discs that allow synchronized contraction. Skeletal muscle attaches to bones and is voluntary; smooth muscle lines hollow organs and is involuntary.",
        "Muscular"
    ),
    (
        "Which hormone is produced by the pancreas to lower blood sugar levels?",
        "Insulin",
        "Insulin is produced by beta cells in the pancreatic islets (islets of Langerhans). It promotes cellular uptake of glucose and storage as glycogen in the liver, lowering blood sugar. Glucagon (alpha cells) does the opposite — raises blood sugar by stimulating glycogen breakdown. Together they maintain blood glucose homeostasis.",
        "Endocrine"
    ),
    (
        "Where does fertilization of an egg by sperm normally occur?",
        "Fallopian tube (oviduct)",
        "Fertilization occurs in the fallopian tube, typically in the ampulla region. The egg is released from the ovary into the fallopian tube during ovulation. Sperm travel through the cervix and uterus to reach the fallopian tube. The fertilized zygote then travels to the uterus for implantation.",
        "Reproductive"
    ),
    (
        "What is the correct path of filtrate through the nephron?",
        "Glomerulus → Bowman's capsule → Proximal convoluted tubule (PCT) → Loop of Henle → Distal convoluted tubule (DCT) → Collecting duct",
        "Blood is filtered at the glomerulus; the filtrate enters Bowman's capsule. The PCT reabsorbs ~65% of water, Na+, and all glucose/amino acids. The Loop of Henle creates a concentration gradient via countercurrent multiplication. The DCT fine-tunes electrolyte balance under hormonal control. The collecting duct concentrates urine further before it reaches the renal pelvis.",
        "Urinary"
    ),
    (
        "Which division of the nervous system controls involuntary functions such as heart rate and digestion?",
        "Autonomic nervous system",
        "The autonomic nervous system (ANS) regulates involuntary body functions. It has two branches: sympathetic (fight or flight — increases heart rate, dilates pupils, inhibits digestion) and parasympathetic (rest and digest — decreases heart rate, stimulates digestion). The somatic nervous system controls voluntary skeletal muscle movement.",
        "Nervous"
    ),
    (
        "Which layer of the skin contains blood vessels, nerve endings, hair follicles, and sweat glands?",
        "Dermis",
        "The dermis is the thick middle layer of skin composed of dense irregular connective tissue. It houses blood vessels (supplying nutrients to both dermis and avascular epidermis), nerve endings (touch, pain, temperature receptors), hair follicles, sweat glands, and sebaceous glands. The epidermis above it has no blood vessels; the hypodermis below it is primarily fat.",
        "Integumentary"
    ),
    (
        "What is the primary function of the large intestine?",
        "Water absorption",
        "The large intestine (colon) primarily absorbs water and electrolytes from indigestible food residue, converting liquid chyme into solid feces. It also houses beneficial gut bacteria that produce vitamins K and B. Most nutrient absorption occurs in the small intestine. The large intestine does NOT produce digestive enzymes.",
        "Digestive"
    ),
    (
        "Which type of immunity is specific to a particular pathogen and has immunological memory?",
        "Adaptive (acquired) immunity",
        "Adaptive immunity is pathogen-specific and creates memory cells (B and T lymphocytes) that enable faster, stronger responses upon re-exposure. It includes humoral immunity (B cells produce antibodies) and cell-mediated immunity (T cells attack infected cells). Innate immunity is non-specific (skin, inflammation, phagocytes) and has no memory.",
        "Lymphatic/Immune"
    ),
]

c.executemany(
    """INSERT INTO high_yield_qa
       (question, correct_answer, explanation, body_system)
       VALUES (?,?,?,?)""",
    high_yield_qas
)

conn.commit()
print(f"Inserted batch 3: {conn.execute('SELECT COUNT(*) FROM misconceptions').fetchone()[0]} misconceptions, {conn.execute('SELECT COUNT(*) FROM high_yield_qa').fetchone()[0]} Q&As")
conn.close()
