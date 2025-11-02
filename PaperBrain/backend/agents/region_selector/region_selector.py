import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import json
import base64

# --- 1. Setup Inputs ---
TEMPLATE_FOLDER = '../preprocessor/question_paper_templates'
FILLED_IMAGE_FOLDER = '../preprocessor/aligned_outputs'

# --- 2. Create Output Directories ---
os.makedirs("evaluation_results", exist_ok=True)
os.makedirs("agent1_output", exist_ok=True)  # For Agent 2 JSON data

# --- 3. Auto-select Template ---
print(f"Scanning for template images in: {TEMPLATE_FOLDER}")
TEMPLATE_PATHS = []
for ext in ['jpg', 'jpeg', 'png']:
    pattern = os.path.join(TEMPLATE_FOLDER, f"template_*.{ext}")
    TEMPLATE_PATHS.extend(glob.glob(pattern))

if not TEMPLATE_PATHS:
    print(f"FATAL ERROR: No template images found in {TEMPLATE_FOLDER}")
    exit()

BLANK_IMAGE_PATH = TEMPLATE_PATHS[0]
if len(TEMPLATE_PATHS) > 1:
    print(f"Found {len(TEMPLATE_PATHS)} template files. Using: {os.path.basename(BLANK_IMAGE_PATH)}")

# --- 4. Find all filled images ---
print(f"\nScanning for images in: {FILLED_IMAGE_FOLDER}")
image_extensions = ('*.jpg', '*.jpeg', '*.png')
FILLED_IMAGE_PATHS = []
for ext in image_extensions:
    FILLED_IMAGE_PATHS.extend(glob.glob(os.path.join(FILLED_IMAGE_FOLDER, ext)))

if not FILLED_IMAGE_PATHS:
    print(f"FATAL ERROR: No images found in {FILLED_IMAGE_FOLDER}")
    exit()

print(f"Found {len(FILLED_IMAGE_PATHS)} images to process.")

# --- 5. Load & preprocess blank template ---
print(f"\nLoading blank reference image: {BLANK_IMAGE_PATH}")
img_blank = cv2.imread(BLANK_IMAGE_PATH)
if img_blank is None:
    print(f"FATAL ERROR: Could not read blank image at {BLANK_IMAGE_PATH}")
    exit()

gray_blank = cv2.cvtColor(img_blank, cv2.COLOR_BGR2GRAY)
h, w = gray_blank.shape
gray_blank = cv2.GaussianBlur(gray_blank, (5, 5), 0)
print("Blank image processed successfully.")

# --- 6. Process each filled image ---
print("\n--- Starting batch processing ---")
for image_path in FILLED_IMAGE_PATHS:
    print(f"\nProcessing image: {image_path}")

    # Load filled image
    img_filled = cv2.imread(image_path)
    if img_filled is None:
        print(f"Skipping image, could not be loaded.")
        continue

    # Resize filled image to match blank
    img_filled_resized = cv2.resize(img_filled.copy(), (w, h))

    # Grayscale for diff processing
    gray_filled = cv2.cvtColor(img_filled_resized, cv2.COLOR_BGR2GRAY)
    gray_filled = cv2.GaussianBlur(gray_filled, (5, 5), 0)

    # Image for drawing boxes
    img_with_boxes = img_filled_resized.copy()

    # Compute difference
    diff = cv2.absdiff(gray_blank, gray_filled)

    # Threshold & cleanup
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((7, 7), np.uint8)
    clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Merge words on the same line
    kernel_h = np.ones((5, 100), np.uint8)
    merged_regions = cv2.dilate(clean, kernel_h, iterations=1)

    # Find & sort bounding boxes
    contours, _ = cv2.findContours(merged_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bounding_boxes = []
    for c in contours:
        x, y, w_c, h_c = cv2.boundingRect(c)
        if (w_c * h_c) > 100:
            bounding_boxes.append((int(x), int(y), int(w_c), int(h_c)))
    bounding_boxes.sort(key=lambda box: box[1])

    # Draw boxes and labels
    print(f"Found {len(bounding_boxes)} answer regions:")
    for j, (x, y, w_box, h_box) in enumerate(bounding_boxes):
        print(f"  Region {j+1}: [x={x}, y={y}, w={w_box}, h={h_box}]")
        cv2.rectangle(img_with_boxes, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)
        cv2.putText(img_with_boxes, str(j + 1), (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Save debug image
    base_name = os.path.basename(image_path)
    file_name_only = os.path.splitext(base_name)[0]
    output_filename = f"evaluation_results/{file_name_only}_result.png"
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(img_with_boxes, cv2.COLOR_BGR2RGB))
    plt.title(f"Detected Regions for {base_name}")
    plt.axis("off")
    plt.savefig(output_filename)
    plt.close()
    print(f"Saved debug image to {output_filename}")

    # --- Save JSON for Agent 2 (raw resized image) ---
    _, buffer = cv2.imencode('.jpg', img_filled_resized)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    data_for_agent_2 = {
        "image_base64": image_base64,
        "rois": bounding_boxes
    }
    json_filename = f"agent1_output/{file_name_only}_data.json"
    with open(json_filename, 'w') as f:
        json.dump(data_for_agent_2, f)
    print(f"Saved data for Agent 2 to {json_filename}")

print("\n--- Batch processing complete. ---")
