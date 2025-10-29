import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import sys

try:
    # ================= CONFIG =================
    CSV_FILE = "results/evaluation_results.csv"
    JSON_FILE = "results/evaluation_results.json"
    OUTPUT_FOLDER = "results/visualizations"

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # ================= LOAD DATA =================
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file not found at {CSV_FILE}")
        sys.exit(1)
    
    df = pd.read_csv(CSV_FILE)

    # For some analyses, you may want JSON too
    if not os.path.exists(JSON_FILE):
        print(f"Warning: JSON file not found at {JSON_FILE}")
        json_data = None
    else:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            json_data = json.load(f)

    # ================= OVERALL STUDENT PERFORMANCE =================
    student_scores = df.groupby(["Student Name", "Roll No"]).agg(
        total_awarded=("Awarded Marks", "sum"),
        total_possible=("Max Marks", "sum")
    ).reset_index()
    student_scores["percentage"] = (student_scores["total_awarded"] / student_scores["total_possible"] * 100).round(2)

    # Barplot: Student performance %
    plt.figure(figsize=(10,6))
    sns.barplot(x="Student Name", y="percentage", data=student_scores, palette="viridis")
    plt.title("Overall Student Performance (%)")
    plt.ylabel("Percentage Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "student_performance.png"))
    plt.close()

    # ================= MOST INCORRECT QUESTIONS =================
    incorrect_q = df[df["Awarded Marks"] < df["Max Marks"]]
    incorrect_count = incorrect_q.groupby("Question No").size().reset_index(name="count")

    plt.figure(figsize=(8,5))
    sns.barplot(x="Question No", y="count", data=incorrect_count, palette="magma")
    plt.title("Most Incorrect Questions (0 or Partial Marks)")
    plt.ylabel("Number of Students with Incorrect Answer")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "most_incorrect_questions.png"))
    plt.close()

    # ================= COMMON MISTAKES =================
    from collections import Counter
    mistakes = []

    for feedback in incorrect_q["Feedback"]:
        mistakes.append(feedback)

    common_mistakes = Counter(mistakes).most_common(10)

    mistake_df = pd.DataFrame(common_mistakes, columns=["Feedback", "Count"])
    plt.figure(figsize=(10,6))
    sns.barplot(y="Feedback", x="Count", data=mistake_df, palette="coolwarm")
    plt.title("Top 10 Common Feedback / Mistakes Across Students")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "common_mistakes.png"))
    plt.close()

    # ================= QUESTION-WISE AVERAGE SCORES =================
    q_scores = df.groupby("Question No").agg(
        avg_awarded=("Awarded Marks", "mean"),
        max_marks=("Max Marks", "first")
    ).reset_index()
    q_scores["percentage"] = (q_scores["avg_awarded"] / q_scores["max_marks"] * 100).round(2)

    plt.figure(figsize=(10,6))
    sns.barplot(x="Question No", y="percentage", data=q_scores, palette="plasma")
    plt.title("Average Score (%) Per Question")
    plt.ylabel("Average Percentage")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, "avg_score_per_question.png"))
    plt.close()

    # ================= SUMMARY TABLE =================
    summary_table = student_scores[["Student Name", "total_awarded", "total_possible", "percentage"]]
    summary_table.to_csv(os.path.join(OUTPUT_FOLDER, "overall_summary.csv"), index=False)

    print("Visualizations and summaries generated in:", OUTPUT_FOLDER)
    print("Success! All visualizations created.")

except Exception as e:
    print(f"Error during visualization generation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
