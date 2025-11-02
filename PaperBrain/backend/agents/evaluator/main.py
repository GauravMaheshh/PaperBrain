import os
import json
import csv
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------- Environment Setup ----------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# ---------------- Paths ----------------
INCOMING_FOLDER = "../text_recognition/Outputs"
TEMP_DIR = "./temp"
INPUTS_DIR = "./inputs"
PROMPTS_DIR = "./prompts"
RESULTS_DIR = "./results"

STUDENT_FILE = os.path.join(INPUTS_DIR, "student_answers.json")
REFERENCE_FILE = os.path.join(INPUTS_DIR, "reference_answers.json")
PROMPT_FILE = os.path.join(PROMPTS_DIR, "prompt.txt")
DOCS_FOLDER = os.path.join(INPUTS_DIR, "related_docs")
CSV_FILE = os.path.join(RESULTS_DIR, "evaluation_results.csv")
JSON_FILE = os.path.join(RESULTS_DIR, "evaluation_results.json")
CURRENT_STUDENT_FILE = os.path.join(TEMP_DIR, "current_student.json")

# Ensure directories exist
for path in [INCOMING_FOLDER, TEMP_DIR, INPUTS_DIR, PROMPTS_DIR, DOCS_FOLDER, RESULTS_DIR]:
    os.makedirs(path, exist_ok=True)

# ---------------- Helper Functions ----------------
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {} if "reference" in path else {"students": []}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- Initial Setup ----------------
reference_answers = load_json(REFERENCE_FILE)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# ---------------- Upload Related Docs ----------------
def upload_related_docs(folder_path):
    uploaded_files = []
    if not os.path.exists(folder_path):
        return uploaded_files

    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]
    print("Starting document and image upload for context...")

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"Skipping unsupported file type: {filename}")
            continue
        print(f"Uploading file: {filename}")
        try:
            uploaded_file = genai.upload_file(path=file_path)
            uploaded_files.append(uploaded_file)
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")

    print(f"Uploaded {len(uploaded_files)} context files.")
    return uploaded_files

related_docs = upload_related_docs(DOCS_FOLDER)
if not related_docs:
    print("No context documents found. Grading will rely only on prompt and answers.\n")

# ---------------- Gemini Evaluation ----------------
def evaluate_with_gemini(student_ans, ref_ans, max_marks):
    full_prompt = f"""{BASE_PROMPT}

Reference Answer:
{ref_ans}

Student Answer:
{student_ans}

Maximum Marks: {max_marks}

Use any additional context from the uploaded related documents to ensure more accurate grading.
"""

    contents = [full_prompt]
    if related_docs:
        contents.extend(related_docs)

    try:
        response = model.generate_content(contents=contents)
        text = response.text.strip()

        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            json_str = text[start:end + 1]
            result = json.loads(json_str)
            return result.get("awarded_marks", 0), result.get("feedback", "")
        else:
            return 0, f"Invalid response format. Raw text: {text[:100]}..."
    except Exception as e:
        return 0, f"API Error: {str(e)}"

# ---------------- Process One File ----------------
def process_student_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        student_entry = json.load(f)

    student_info = student_entry.get("student_info", {})
    student_answers = student_entry.get("answers", {})
    student_name = student_info.get("name", "")
    roll_no = student_info.get("roll_no", "")

    print(f"Evaluating student: {student_name} ({roll_no})")

    total_awarded = 0
    total_possible = 0
    answers = {}

    for qno, student_ans in student_answers.items():
        ref_info = reference_answers.get(str(qno))
        if not ref_info:
            answers[qno] = {
                "answer": student_ans,
                "awarded_marks": 0,
                "max_marks": 0,
                "feedback": "No reference answer found"
            }
            continue

        ref_ans = ref_info["answer"]
        max_marks = ref_info["marks"]

        print(f"Processing Question {qno}...")
        awarded, feedback = evaluate_with_gemini(student_ans, ref_ans, max_marks)

        total_awarded += awarded
        total_possible += max_marks

        answers[qno] = {
            "answer": student_ans,
            "awarded_marks": awarded,
            "max_marks": max_marks,
            "feedback": feedback
        }

    updated_data = {
        "student_info": student_info,
        "total_awarded_marks": total_awarded,
        "total_possible_marks": total_possible,
        "answers": answers
    }

    save_json(CURRENT_STUDENT_FILE, updated_data)

    os.remove(file_path)
    print(f"Removed processed file: {file_path}")

    return updated_data

# ---------------- Main Processing ----------------
def process_all_students():
    files = sorted(
        [os.path.join(INCOMING_FOLDER, f) for f in os.listdir(INCOMING_FOLDER) if f.endswith(".json")],
        key=os.path.getctime
    )

    if not files:
        print("No new student submissions found.")
        return

    print(f"Found {len(files)} submissions to process.\n")

    # Safe load of current_student.json
    if os.path.exists(CURRENT_STUDENT_FILE):
        try:
            if os.path.getsize(CURRENT_STUDENT_FILE) > 0:
                with open(CURRENT_STUDENT_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    current_data = json.loads(content) if content else {}
            else:
                current_data = {}
        except Exception as e:
            print(f"Warning: Failed to load current_student.json ({e}), starting fresh.")
            current_data = {}
    else:
        current_data = {}

    for file_path in files:
        current_data = process_student_file(file_path)

    # Save to cumulative result files
    student_data = load_json(STUDENT_FILE)
    master_results = load_json(JSON_FILE)

    student_data.setdefault("students", []).append(current_data)
    master_results.setdefault("students", []).append(current_data)
    save_json(STUDENT_FILE, student_data)
    save_json(JSON_FILE, master_results)

    csv_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not csv_exists or os.path.getsize(CSV_FILE) == 0:
            writer.writerow(["Student Name", "Roll No", "Question No", "Student Answer",
                             "Reference Answer", "Max Marks", "Awarded Marks", "Feedback"])
        for qno, details in current_data["answers"].items():
            writer.writerow([
                current_data["student_info"].get("name", ""),
                current_data["student_info"].get("roll_no", ""),
                qno,
                details["answer"],
                reference_answers.get(qno, {}).get("answer", "N/A"),
                details["max_marks"],
                details["awarded_marks"],
                details["feedback"]
            ])

    print(f"\nEvaluation complete for {current_data['student_info'].get('name', 'Unknown Student')}")
    print(f"Final Score: {current_data['total_awarded_marks']}/{current_data['total_possible_marks']}")
    print(f"Current student record saved at: {CURRENT_STUDENT_FILE}")
    print("Updated results saved in JSON and CSV.")

# ---------------- Run Script ----------------
if __name__ == "__main__":
    process_all_students()
