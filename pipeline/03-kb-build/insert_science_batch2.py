#!/usr/bin/env python3
"""Insert TEAS science questions — Batch 2: Anatomy & Physiology (Urinary, Blood typing, Tissue types, Immune) + Life Science — 32 questions."""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline", "runs", "science", "data", "science.db")

QUESTIONS = [
    # ── Urinary system (6) ──
    {"q": "Which structure carries urine from the kidneys to the bladder?", "a": "Ureters", "e": "The ureters are muscular tubes that propel urine from the renal pelvis to the urinary bladder via peristalsis.", "t": "Urinary system"},
    {"q": "The functional unit of the kidney is the:", "a": "Nephron", "e": "The nephron is the kidney's functional unit, consisting of the renal corpuscle (glomerulus + Bowman's capsule) and renal tubule.", "t": "Urinary system"},
    {"q": "Which process occurs primarily in the glomerulus?", "a": "Filtration", "e": "Blood pressure forces water and small solutes through the glomerular capillary walls into Bowman's capsule — this is filtration.", "t": "Urinary system"},
    {"q": "What hormone increases water reabsorption in the collecting duct?", "a": "Antidiuretic hormone (ADH)", "e": "ADH makes the collecting duct more permeable to water via aquaporin channels, allowing more water to be reabsorbed into the blood.", "t": "Urinary system"},
    {"q": "Normal urine is primarily composed of:", "a": "Water, urea, and salts", "e": "Urine is about 95% water, with urea (waste product of protein metabolism), salts, creatinine, and uric acid making up the remainder.", "t": "Urinary system"},
    {"q": "Which part of the nephron is responsible for the countercurrent multiplier?", "a": "Loop of Henle", "e": "The descending and ascending limbs of the Loop of Henle create a concentration gradient in the medulla, essential for producing concentrated urine.", "t": "Urinary system"},

    # ── Blood typing and compatibility (6) ──
    {"q": "A person with type AB blood has which antibodies?", "a": "Neither anti-A nor anti-B antibodies", "e": "Type AB individuals are 'universal recipients' — they have both A and B antigens on their RBCs but neither antibody in their plasma.", "t": "Blood typing and compatibility"},
    {"q": "Which blood type is the 'universal donor'?", "a": "Type O negative", "e": "Type O negative RBCs have neither A nor B antigens and no Rh factor, so they won't trigger immune reactions in any recipient.", "t": "Blood typing and compatibility"},
    {"q": "The Rh factor refers to the presence or absence of which antigen?", "a": "RhD antigen", "e": "The Rh (Rhesus) factor, specifically RhD, determines whether blood is Rh-positive (has the antigen) or Rh-negative (lacks it).", "t": "Blood typing and compatibility"},
    {"q": "If a person with type B blood receives type A blood, what happens?", "a": "Agglutination (clumping) occurs", "e": "Anti-A antibodies in the type B recipient's plasma will bind to A antigens on the donated RBCs, causing agglutination and potentially a transfusion reaction.", "t": "Blood typing and compatibility"},
    {"q": "Erythroblastosis fetalis can occur when:", "a": "An Rh-negative mother carries an Rh-positive fetus", "e": "If maternal anti-Rh antibodies cross the placenta, they attack fetal Rh-positive RBCs. This is prevented with RhoGAM injections.", "t": "Blood typing and compatibility"},
    {"q": "Which blood component is most important for determining blood type?", "a": "Antigens on the surface of red blood cells", "e": "Blood type is determined by the presence (A, B, AB) or absence (O) of specific glycoprotein antigens on RBC membranes.", "t": "Blood typing and compatibility"},

    # ── Tissue types (6) ──
    {"q": "Which type of tissue lines body surfaces and cavities?", "a": "Epithelial tissue", "e": "Epithelial tissue forms protective coverings and linings of body surfaces, organs, and cavities. It can be simple (one layer) or stratified (multiple layers).", "t": "Tissue types"},
    {"q": "Which connective tissue type stores energy and provides insulation?", "a": "Adipose tissue", "e": "Adipose (fat) tissue stores energy in triglycerides, insulates the body, and cushions organs.", "t": "Tissue types"},
    {"q": "Which tissue type is characterized by voluntary control and striations?", "a": "Skeletal muscle", "e": "Skeletal muscle is striated (has alternating bands) and voluntary (consciously controlled). Cardiac is also striated but involuntary.", "t": "Tissue types"},
    {"q": "Which type of epithelium is best suited for diffusion and filtration?", "a": "Simple squamous epithelium", "e": "Simple squamous epithelium is a single flat cell layer that allows rapid diffusion — found in alveoli of lungs and glomerular capillaries.", "t": "Tissue types"},
    {"q": "Cartilage is an example of which type of connective tissue?", "a": "Supportive connective tissue", "e": "Cartilage is a supportive connective tissue with a firm extracellular matrix. Types include hyaline, elastic, and fibrocartilage.", "t": "Tissue types"},
    {"q": "Which tissue type has the greatest capacity for regeneration?", "a": "Epithelial tissue", "e": "Epithelial tissue regenerates rapidly due to stem cells near the basement membrane. Cardiac muscle and nervous tissue have very limited regenerative capacity.", "t": "Tissue types"},

    # ── Immune system (6) ──
    {"q": "Which type of immune cell produces antibodies?", "a": "B lymphocytes (B cells)", "e": "B cells differentiate into plasma cells that secrete antibodies (immunoglobulins) specific to a particular antigen.", "t": "Immune system - types of immunity"},
    {"q": "What is the difference between active and passive immunity?", "a": "Active immunity involves antibody production by your own body; passive immunity involves receiving pre-made antibodies", "e": "Active immunity (vaccination or infection) is long-lasting. Passive immunity (maternal antibodies, antivenom) provides temporary protection.", "t": "Immune system - types of immunity"},
    {"q": "Which immune cell is most effective at destroying virus-infected cells?", "a": "Cytotoxic T cells", "e": "Cytotoxic (CD8+) T cells recognize and kill virus-infected cells and cancer cells by releasing perforin and granzymes.", "t": "Immune system - types of immunity"},
    {"q": "The inflammatory response is triggered by which chemical?", "a": "Histamine", "e": "Mast cells release histamine, which causes vasodilation and increased capillary permeability, leading to redness, heat, swelling, and pain.", "t": "Immune system - types of immunity"},
    {"q": "Which immunoglobulin is the most abundant in the blood and provides secondary immune response?", "a": "IgG", "e": "IgG is the most abundant antibody in serum, crosses the placenta, and is the main antibody of the secondary (memory) immune response.", "t": "Immune system - types of immunity"},
    {"q": "What type of immunity does a vaccine provide?", "a": "Artificial active immunity", "e": "Vaccines provide artificial active immunity by exposing the immune system to antigens, stimulating antibody production and memory cell formation without causing disease.", "t": "Immune system - types of immunity"},

    # ── Cell theory and cell types (4) ──
    {"q": "Which statement is NOT part of the cell theory?", "a": "All cells contain a nucleus", "e": "Cell theory states: all living things are made of cells, cells are the basic unit of life, and all cells come from pre-existing cells. Prokaryotes lack a nucleus.", "t": "Cell theory and cell types"},
    {"q": "Which organelle is the 'powerhouse of the cell'?", "a": "Mitochondria", "e": "Mitochondria produce ATP through aerobic cellular respiration. They have their own DNA and are thought to have originated from endosymbiotic bacteria.", "t": "Cell theory and cell types"},
    {"q": "What is the primary difference between prokaryotic and eukaryotic cells?", "a": "Eukaryotic cells have a membrane-bound nucleus; prokaryotic cells do not", "e": "Eukaryotes (animals, plants, fungi) have a true nucleus and membrane-bound organelles. Prokaryotes (bacteria, archaea) lack these.", "t": "Cell theory and cell types"},
    {"q": "Which organelle is responsible for protein synthesis?", "a": "Ribosome", "e": "Ribosomes translate mRNA into proteins. They exist free in the cytoplasm or bound to the rough endoplasmic reticulum.", "t": "Cell theory and cell types"},
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
