#!/usr/bin/env python3
"""Insert TEAS science questions — Batch 4: Scientific Reasoning (24 questions)."""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline", "runs", "science", "data", "science.db")

QUESTIONS = [
    # ── Experimental design (6) ──
    {"q": "In a controlled experiment, the group that does NOT receive the treatment is called the:", "a": "Control group", "e": "The control group receives no treatment or a placebo, providing a baseline to compare against the experimental group that receives the treatment.", "t": "Experimental design"},
    {"q": "A double-blind study means:", "a": "Neither the participants nor the researchers know who receives the treatment", "e": "Double-blind design eliminates both participant and researcher bias, ensuring that expectations don't influence the results.", "t": "Experimental design"},
    {"q": "Why is sample size important in an experiment?", "a": "Larger samples reduce the impact of random variation and increase reliability", "e": "A larger sample size decreases the margin of error and increases statistical power, making results more representative of the population.", "t": "Experimental design"},
    {"q": "What is a placebo?", "a": "An inactive treatment given to the control group", "e": "Placebos look like the real treatment but have no active effect. They help determine if results are due to the treatment itself or the participant's expectations.", "t": "Experimental design"},
    {"q": "Which type of study observes subjects over a long period of time?", "a": "Longitudinal study", "e": "Longitudinal studies track the same subjects over extended periods. Cross-sectional studies observe subjects at a single point in time.", "t": "Experimental design"},
    {"q": "Random assignment in an experiment is used to:", "a": "Minimize confounding variables between groups", "e": "Random assignment ensures each participant has an equal chance of being in any group, distributing potential confounding variables evenly.", "t": "Experimental design"},

    # ── Identifying variables (6) ──
    {"q": "In an experiment testing whether caffeine affects heart rate, the independent variable is:", "a": "The amount of caffeine given", "e": "The independent variable is the factor the experimenter deliberately changes. The dependent variable (heart rate) is what is measured.", "t": "Identifying variables"},
    {"q": "A confounding variable is:", "a": "An uncontrolled variable that influences the results", "e": "Confounding variables are factors other than the independent variable that affect the dependent variable, potentially leading to incorrect conclusions.", "t": "Identifying variables"},
    {"q": "In a plant growth experiment, if a student forgets to water some plants equally, this introduces:", "a": "A confounding variable", "e": "Unequal watering becomes an uncontrolled variable that could affect plant growth, making it impossible to determine if the original independent variable caused the results.", "t": "Identifying variables"},
    {"q": "The dependent variable is the factor that is:", "a": "Measured or observed in the experiment", "e": "The dependent variable 'depends' on the independent variable. It is the outcome that is measured to see the effect of the experimental treatment.", "t": "Identifying variables"},
    {"q": "A controlled variable (constant) in an experiment is one that:", "a": "Is kept the same for all groups to ensure a fair test", "e": "Controlled variables are held constant so that any observed changes can be attributed to the independent variable alone.", "t": "Identifying variables"},
    {"q": "If researchers test a new drug and find patients improve, but the patients also exercised more during the study, exercise is a:", "a": "Confounding variable", "e": "Exercise could independently affect the outcome, making it unclear whether the drug, the exercise, or both caused the improvement.", "t": "Identifying variables"},

    # ── Interpreting data (6) ──
    {"q": "A graph shows a line sloping upward from left to right. This indicates:", "a": "A positive correlation between the variables", "e": "An upward slope means as the x-variable increases, the y-variable also increases — a positive (direct) correlation.", "t": "Interpreting data"},
    {"q": "If a data set has a mean of 50 and a median of 50, the distribution is likely:", "a": "Symmetrical (normal)", "e": "When mean and median are equal, the data is typically symmetrically distributed. A skewed distribution would cause mean and median to differ.", "t": "Interpreting data"},
    {"q": "What does a p-value less than 0.05 indicate?", "a": "The results are statistically significant", "e": "A p-value < 0.05 means there is less than a 5% probability that the observed results occurred by chance alone, indicating statistical significance.", "t": "Interpreting data"},
    {"q": "In a bar graph, the height of each bar represents:", "a": "The value of the variable being measured for each category", "e": "Bar graphs use bar height (or length) to show values for discrete categories, making comparisons between groups easy to visualize.", "t": "Interpreting data"},
    {"q": "The range of a data set is:", "a": "The difference between the highest and lowest values", "e": "Range = maximum value − minimum value. It measures the spread of data but is sensitive to outliers.", "t": "Interpreting data"},
    {"q": "A scatter plot with points forming a tight cluster around a downward-sloping line shows:", "a": "A strong negative correlation", "e": "Points clustered tightly around a downward line indicate a strong negative (inverse) relationship — as x increases, y decreases consistently.", "t": "Interpreting data"},

    # ── Drawing conclusions (6) ──
    {"q": "A study finds that ice cream sales and drowning rates increase together. The most accurate conclusion is:", "a": "Both are correlated with a third variable (hot weather)", "e": "This is a classic example of correlation vs. causation. Hot weather increases both ice cream sales and swimming, leading to more drowning. One does not cause the other.", "t": "Drawing conclusions"},
    {"q": "Which statement best describes the difference between correlation and causation?", "a": "Correlation means two variables are related; causation means one directly causes the other", "e": "Correlation does not imply causation. Two variables can be related without one causing the other (confounding variables may be involved).", "t": "Drawing conclusions"},
    {"q": "A hypothesis that has been extensively tested and supported by evidence becomes a:", "a": "Scientific theory", "e": "A scientific theory is a well-substantiated explanation supported by extensive evidence (e.g., theory of evolution). It is NOT a guess or hypothesis.", "t": "Drawing conclusions"},
    {"q": "Which of the following is the strongest conclusion from a single experiment?", "a": "The data supports the hypothesis, but further testing is needed", "e": "No single experiment definitively proves anything. Strong conclusions require replication, peer review, and consistent results across multiple studies.", "t": "Drawing conclusions"},
    {"q": "An experiment yields results opposite to the hypothesis. The researcher should:", "a": "Accept the results and consider revising the hypothesis", "e": "Science progresses by testing and potentially falsifying hypotheses. Unexpected results are valuable data that may lead to new understanding.", "t": "Drawing conclusions"},
    {"q": "Which statement describes a scientific law?", "a": "A description of a consistent natural phenomenon (e.g., gravity always pulls objects down)", "e": "Laws describe WHAT happens (observable patterns), while theories explain WHY it happens. Laws don't explain mechanisms — theories do.", "t": "Drawing conclusions"},
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
