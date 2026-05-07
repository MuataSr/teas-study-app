#!/usr/bin/env python3
"""Insert TEAS science questions — Batch 3: Life Science (Cell division, DNA, Photosynthesis, Ecology, Macromolecules) + Physical Science — 40 questions."""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline", "runs", "science", "data", "science.db")

QUESTIONS = [
    # ── Cell division (6) ──
    {"q": "During which phase of mitosis do chromosomes align at the cell equator?", "a": "Metaphase", "e": "In metaphase, chromosomes line up at the metaphase plate (cell equator) with spindle fibers attached to centromeres.", "t": "Cell division"},
    {"q": "What is the result of meiosis?", "a": "Four non-identical haploid cells", "e": "Meiosis produces four genetically unique haploid (n) cells (gametes), each with half the original chromosome number.", "t": "Cell division"},
    {"q": "Which phase of the cell cycle involves DNA replication?", "a": "S phase (Synthesis)", "e": "During the S phase of interphase, each chromosome is replicated to form two sister chromatids held together at the centromere.", "t": "Cell division"},
    {"q": "Crossing over occurs during which stage of meiosis?", "a": "Prophase I", "e": "Crossing over (exchange of genetic material between homologous chromosomes) occurs during prophase I of meiosis, increasing genetic variation.", "t": "Cell division"},
    {"q": "A cell with 46 chromosomes undergoes mitosis. How many chromosomes will each daughter cell have?", "a": "46", "e": "Mitosis produces two genetically identical diploid daughter cells, each with the same chromosome number as the parent cell.", "t": "Cell division"},
    {"q": "Cytokinesis in animal cells involves the formation of a:", "a": "Cleavage furrow", "e": "Animal cells divide by forming a cleavage furrow (pinching inward). Plant cells form a cell plate instead due to their rigid cell wall.", "t": "Cell division"},

    # ── DNA structure and replication (6) ──
    {"q": "The two strands of DNA are held together by:", "a": "Hydrogen bonds between complementary nitrogenous bases", "e": "Adenine pairs with thymine (2 H-bonds) and guanine pairs with cytosine (3 H-bonds). The sugar-phosphate backbone is held by covalent bonds.", "t": "DNA structure and replication"},
    {"q": "In DNA, adenine always pairs with:", "a": "Thymine", "e": "Chargaff's rule: A pairs with T, and G pairs with C. In RNA, uracil replaces thymine and pairs with adenine.", "t": "DNA structure and replication"},
    {"q": "Which enzyme is responsible for unzipping the DNA double helix during replication?", "a": "Helicase", "e": "Helicase breaks hydrogen bonds between base pairs, unwinding the double helix at the replication fork.", "t": "DNA structure and replication"},
    {"q": "DNA replication is called 'semi-conservative' because:", "a": "Each new DNA molecule contains one original strand and one new strand", "e": "Proven by the Meselson-Stahl experiment, each daughter DNA molecule retains one parent strand and gets one newly synthesized strand.", "t": "DNA structure and replication"},
    {"q": "The sugar in DNA is:", "a": "Deoxyribose", "e": "DNA contains deoxyribose sugar (lacks an oxygen at the 2' carbon). RNA contains ribose sugar.", "t": "DNA structure and replication"},
    {"q": "What is the role of DNA polymerase?", "a": "It synthesizes new DNA strands by adding nucleotides", "e": "DNA polymerase reads the template strand and adds complementary nucleotides in the 5' to 3' direction during replication.", "t": "DNA structure and replication"},

    # ── Photosynthesis and cellular respiration (6) ──
    {"q": "Where does photosynthesis primarily occur in plant cells?", "a": "Chloroplasts", "e": "Chloroplasts contain chlorophyll and are the site of photosynthesis. The light reactions occur in thylakoid membranes; the Calvin cycle in the stroma.", "t": "Photosynthesis and cellular respiration"},
    {"q": "What are the products of the light-dependent reactions of photosynthesis?", "a": "ATP, NADPH, and oxygen", "e": "Light energy splits water (photolysis), releasing O₂, and generates ATP and NADPH to power the Calvin cycle.", "t": "Photosynthesis and cellular respiration"},
    {"q": "During which stage of cellular respiration is the most ATP produced?", "a": "Electron transport chain (oxidative phosphorylation)", "e": "The ETC produces about 34 ATP. Glycolysis produces 2 ATP net, and the Krebs cycle produces 2 ATP. Total: ~38 ATP per glucose.", "t": "Photosynthesis and cellular respiration"},
    {"q": "The final electron acceptor in aerobic cellular respiration is:", "a": "Oxygen", "e": "Oxygen accepts electrons at the end of the electron transport chain, combining with hydrogen to form water (H₂O).", "t": "Photosynthesis and cellular respiration"},
    {"q": "Which process converts glucose to pyruvate?", "a": "Glycolysis", "e": "Glycolysis splits one glucose (6-carbon) into two pyruvate (3-carbon) molecules, yielding a net gain of 2 ATP and 2 NADH. It occurs in the cytoplasm.", "t": "Photosynthesis and cellular respiration"},
    {"q": "The Calvin cycle takes place in which part of the chloroplast?", "a": "Stroma", "e": "The Calvin cycle (light-independent reactions) occurs in the stroma, using ATP and NADPH from the light reactions to fix CO₂ into glucose.", "t": "Photosynthesis and cellular respiration"},

    # ── Ecology (6) ──
    {"q": "Which trophic level contains the most energy?", "a": "Producers (autotrophs)", "e": "Energy decreases at each trophic level (~10% rule). Producers have the most energy because they capture it directly from the sun.", "t": "Ecology"},
    {"q": "What is a keystone species?", "a": "A species whose removal would dramatically change the ecosystem", "e": "Keystone species (e.g., sea otters, wolves) have a disproportionate impact on ecosystem structure relative to their abundance.", "t": "Ecology"},
    {"q": "Which type of relationship benefits one organism and harms the other?", "a": "Parasitism", "e": "In parasitism, the parasite benefits at the expense of the host. Commensalism benefits one and doesn't affect the other. Mutualism benefits both.", "t": "Ecology"},
    {"q": "The process by which nitrogen is converted from atmospheric N₂ to a usable form is called:", "a": "Nitrogen fixation", "e": "Nitrogen-fixing bacteria convert atmospheric N₂ into ammonia (NH₃), which plants can use. This is done by bacteria in soil or root nodules.", "t": "Ecology"},
    {"q": "Which biome is characterized by low precipitation and extreme temperature variations?", "a": "Desert", "e": "Deserts receive <25 cm of precipitation annually and have large daily temperature swings due to lack of moisture in the air.", "t": "Ecology"},
    {"q": "What does a food web represent?", "a": "Interconnected food chains showing multiple feeding relationships in an ecosystem", "e": "A food web shows the complex network of feeding relationships among organisms in an ecosystem, unlike a linear food chain.", "t": "Ecology"},

    # ── Macromolecules (4) ──
    {"q": "Which macromolecule serves as the primary energy storage molecule in animals?", "a": "Lipids (fats)", "e": "Lipids store more energy per gram (9 kcal/g) than carbohydrates or proteins (4 kcal/g). In animals, fats are the primary long-term energy storage.", "t": "Macromolecules"},
    {"q": "Proteins are made up of monomers called:", "a": "Amino acids", "e": "There are 20 amino acids that combine in various sequences to form proteins. The sequence determines the protein's shape and function.", "t": "Macromolecules"},
    {"q": "Which type of bond holds amino acids together in a protein?", "a": "Peptide bonds", "e": "Peptide bonds form between the amino group of one amino acid and the carboxyl group of another through dehydration synthesis.", "t": "Macromolecules"},
    {"q": "Which macromolecule is the primary component of cell membranes?", "a": "Phospholipids", "e": "Phospholipids form the bilayer of cell membranes, with hydrophilic phosphate heads facing outward and hydrophobic fatty acid tails facing inward.", "t": "Macromolecules"},

    # ── Chemical bonds (5) ──
    {"q": "Which type of bond involves the sharing of electrons between atoms?", "a": "Covalent bond", "e": "In covalent bonds, atoms share electrons to achieve stable electron configurations. Ionic bonds involve electron transfer, not sharing.", "t": "Chemical bonds"},
    {"q": "What happens when sodium (Na) and chlorine (Cl) form a bond?", "a": "Sodium transfers an electron to chlorine, forming Na⁺ and Cl⁻", "e": "This is an ionic bond. Na (1 valence electron) loses an electron to become Na⁺, and Cl (7 valence electrons) gains it to become Cl⁻.", "t": "Chemical bonds"},
    {"q": "Water molecules are held together by which type of bond?", "a": "Hydrogen bonds", "e": "The partially positive hydrogen of one water molecule is attracted to the partially negative oxygen of another, forming hydrogen bonds.", "t": "Chemical bonds"},
    {"q": "Which type of bond is the strongest?", "a": "Covalent bond", "e": "Covalent bonds (sharing electrons) are the strongest chemical bonds. Ionic bonds are strong but weaker than covalent. Hydrogen bonds are the weakest.", "t": "Chemical bonds"},
    {"q": "A polar covalent bond occurs when:", "a": "Electrons are shared unequally between atoms with different electronegativities", "e": "In polar bonds (like H₂O), the more electronegative atom attracts electrons more strongly, creating partial charges (δ+ and δ−).", "t": "Chemical bonds"},

    # ── Acids, bases, and pH (5) ──
    {"q": "What is the pH of a neutral solution?", "a": "7", "e": "A pH of 7 is neutral. Below 7 is acidic (high H⁺ concentration), above 7 is basic (low H⁺ concentration). The pH scale is logarithmic.", "t": "Acids, bases, and pH"},
    {"q": "Which of the following is a strong acid?", "a": "Hydrochloric acid (HCl)", "e": "HCl is a strong acid that completely dissociates in water. Weak acids (like acetic acid/vinegar) only partially dissociate.", "t": "Acids, bases, and pH"},
    {"q": "A solution with a pH of 3 is how many times more acidic than a solution with a pH of 5?", "a": "100 times", "e": "The pH scale is logarithmic: each unit change represents a 10-fold change in H⁺ concentration. A difference of 2 = 10² = 100 times.", "t": "Acids, bases, and pH"},
    {"q": "Which pH range is optimal for most human enzymes?", "a": "pH 7.0 – 7.8", "e": "Most human enzymes function optimally near neutral pH (around 7.4). Pepsin in the stomach is an exception, working best at pH 2.", "t": "Acids, bases, and pH"},
    {"q": "Bases are substances that:", "a": "Accept protons (H⁺ ions)", "e": "According to the Brønsted-Lowry definition, bases accept protons. Bases also increase OH⁻ concentration in aqueous solutions.", "t": "Acids, bases, and pH"},

    # ── Periodic table trends (5) ──
    {"q": "As you move from left to right across a period on the periodic table, atomic radius generally:", "a": "Decreases", "e": "Increasing nuclear charge pulls electrons closer to the nucleus, decreasing atomic radius across a period. It increases down a group.", "t": "Periodic table trends"},
    {"q": "Which group on the periodic table contains the most reactive metals?", "a": "Group 1 (alkali metals)", "e": "Alkali metals (Li, Na, K) have one valence electron that they readily lose, making them the most reactive metals. Reactivity increases down the group.", "t": "Periodic table trends"},
    {"q": "Electronegativity generally increases:", "a": "From left to right across a period and decreases down a group", "e": "Fluorine is the most electronegative element. Electronegativity increases with nuclear charge and decreases with atomic size.", "t": "Periodic table trends"},
    {"q": "Elements in the same column of the periodic table have similar properties because they:", "a": "Have the same number of valence electrons", "e": "Valence electrons determine chemical behavior. Elements in the same group share the same valence electron configuration.", "t": "Periodic table trends"},
    {"q": "Noble gases are largely unreactive because:", "a": "They have a full outer electron shell", "e": "Noble gases (Group 18) have a stable octet configuration, so they rarely form compounds under normal conditions.", "t": "Periodic table trends"},

    # ── States of matter and phase changes (5) ──
    {"q": "During which phase change does a solid become a liquid?", "a": "Melting", "e": "Melting (fusion) occurs when thermal energy overcomes intermolecular forces in a solid, allowing molecules to move more freely.", "t": "States of matter and phase changes"},
    {"q": "What happens to the temperature of water during boiling?", "a": "It remains constant until all water has vaporized", "e": "During a phase change, added energy breaks intermolecular bonds rather than increasing temperature. This is called the latent heat of vaporization.", "t": "States of matter and phase changes"},
    {"q": "Which state of matter has molecules that are close together but can slide past one another?", "a": "Liquid", "e": "Liquids have molecules close together (like solids) but with enough energy to move and slide past each other, giving them a fixed volume but variable shape.", "t": "States of matter and phase changes"},
    {"q": "Sublimation is the process where a substance changes directly from:", "a": "Solid to gas", "e": "Sublimation skips the liquid phase (e.g., dry ice/CO₂). Deposition is the reverse — gas to solid.", "t": "States of matter and phase changes"},
    {"q": "Which type of bonding is responsible for the high boiling point of water?", "a": "Hydrogen bonding", "e": "Strong hydrogen bonds between water molecules require significant energy to break, giving water an unusually high boiling point for its molecular weight.", "t": "States of matter and phase changes"},

    # ── Metric system and conversions (5) ──
    {"q": "How many milliliters are in 1 liter?", "a": "1,000 mL", "e": "The metric prefix 'milli-' means 1/1000. So 1 L = 1000 mL. Other common conversions: 1 m = 100 cm = 1000 mm.", "t": "Metric system and conversions"},
    {"q": "Which metric prefix means 'one millionth'?", "a": "Micro (μ)", "e": "Micro (μ) = 10⁻⁶. Other prefixes: milli (10⁻³), centi (10⁻²), kilo (10³), mega (10⁶).", "t": "Metric system and conversions"},
    {"q": "Convert 0.5 kilograms to grams.", "a": "500 grams", "e": "1 kg = 1000 g, so 0.5 kg × 1000 = 500 g.", "t": "Metric system and conversions"},
    {"q": "What is the base unit of mass in the metric system?", "a": "Kilogram", "e": "The kilogram (kg) is the SI base unit of mass. The gram is commonly used in chemistry and medicine but is a derived unit.", "t": "Metric system and conversions"},
    {"q": "A patient's temperature is 38.5°C. What is this in Fahrenheit?", "a": "101.3°F", "e": "°F = (°C × 9/5) + 32 = (38.5 × 1.8) + 32 = 69.3 + 32 = 101.3°F. Normal body temperature is 37°C (98.6°F).", "t": "Metric system and conversions"},
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
