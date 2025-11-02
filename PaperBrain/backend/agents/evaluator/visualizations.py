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
    # Use all students from CSV - for each unique student, calculate their latest/aggregated score
    # If there are multiple submissions per student, we'll take the latest one (by row position)
    # First, ensure we have all unique students with their complete data
    student_scores = df.groupby(["Student Name", "Roll No"]).agg(
        total_awarded=("Awarded Marks", "sum"),
        total_possible=("Max Marks", "sum")
    ).reset_index()
    student_scores["percentage"] = (student_scores["total_awarded"] / student_scores["total_possible"] * 100).round(2)
    
    # Ensure we're using ALL students from the CSV
    print(f"Total rows in CSV: {len(df)}")
    print(f"Unique students found: {len(student_scores)}")
    print(f"Students: {student_scores['Student Name'].tolist()}")

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

    # ================= CURRENT STUDENT VISUALIZATIONS =================
    CURRENT_STUDENT_FILE = "temp/current_student.json"
    if os.path.exists(CURRENT_STUDENT_FILE):
        with open(CURRENT_STUDENT_FILE, "r", encoding="utf-8") as f:
            current_student = json.load(f)
        
        current_student_name = current_student.get("student_info", {}).get("name", "Current Student")
        current_answers = current_student.get("answers", {})
        
        if current_answers:
            # Current Student - Question-wise Performance
            current_q_data = []
            for qno, qdata in current_answers.items():
                max_marks = qdata.get("max_marks", 1)
                awarded = qdata.get("awarded_marks", 0)
                percentage = (awarded / max_marks * 100) if max_marks > 0 else 0
                current_q_data.append({
                    "Question No": qno,
                    "Percentage": percentage,
                    "Awarded": awarded,
                    "Max": max_marks
                })
            
            if current_q_data:
                current_q_df = pd.DataFrame(current_q_data)
                current_q_df = current_q_df.sort_values("Question No")
                
                plt.figure(figsize=(10,6))
                sns.barplot(x="Question No", y="Percentage", data=current_q_df, palette="viridis")
                plt.title(f"Current Student ({current_student_name}) - Score Per Question (%)")
                plt.ylabel("Percentage Score")
                plt.ylim(0, 100)
                plt.tight_layout()
                plt.savefig(os.path.join(OUTPUT_FOLDER, "current_student_performance.png"))
                plt.close()
                
                print(f"✅ Generated current student visualization for {current_student_name}")

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
