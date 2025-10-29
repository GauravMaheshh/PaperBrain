import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

# --- 1. Setup Your Inputs ---
BLANK_IMAGE_PATH = '../preprocessor/question_paper_templates/template_1_question.jpg'
FILLED_IMAGE_FOLDER = '../preprocessor/aligned_outputs'

os.makedirs("evaluation_results", exist_ok=True)

# --- 2. Automatically Find All Image Paths ---
print(f"Scanning for images in: {FILLED_IMAGE_FOLDER}")

image_extensions = ('*.jpg', '*.jpeg', '*.png')
FILLED_IMAGE_PATHS = []
for ext in image_extensions:
    FILLED_IMAGE_PATHS.extend(glob.glob(os.path.join(FILLED_IMAGE_FOLDER, ext)))

if not FILLED_IMAGE_PATHS:
    print(f"FATAL ERROR: No images found in {FILLED_IMAGE_FOLDER}")
    exit()

print(f"Found {len(FILLED_IMAGE_PATHS)} images to process.")

# --- 3. Load and Pre-process BLANK Image (Once) ---
print(f"\nLoading blank reference image: {BLANK_IMAGE_PATH}")
img_blank = cv2.imread(BLANK_IMAGE_PATH)

if img_blank is None:
    print(f"FATAL ERROR: Could not read blank image at {BLANK_IMAGE_PATH}")
    exit()

gray_blank = cv2.cvtColor(img_blank, cv2.COLOR_BGR2GRAY)
h, w = gray_blank.shape
gray_blank = cv2.GaussianBlur(gray_blank, (5,5), 0)
print("Blank image processed successfully.")

# --- 4. Start Loop to Process Each Answer Sheet ---
print("\n--- Starting batch processing ---")

for image_path in FILLED_IMAGE_PATHS:
    print(f"\nProcessing image: {image_path}")
    
    # --- 4a. Load FILLED Image ---
    img_filled = cv2.imread(image_path)
    
    if img_filled is None:
        print(f"Skipping image, could not be loaded.")
        continue 

    # --- 4b. Pre-process FILLED Image ---
    gray_filled = cv2.cvtColor(img_filled, cv2.COLOR_BGR2GRAY)
    gray_filled = cv2.resize(gray_filled, (w, h))
    gray_filled = cv2.GaussianBlur(gray_filled, (5,5), 0)
    
    # ✅ RESIZE ONCE - Create img_with_boxes at the SAME size as processing
    img_with_boxes = cv2.resize(img_filled.copy(), (w, h))

    # --- 4c. Find Differences ---
    diff = cv2.absdiff(gray_blank, gray_filled)

    # --- 4d. Threshold and Clean Up ---
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((7,7), np.uint8)
    clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Merge words on the same line
    kernel_h = np.ones((5, 100), np.uint8)
    merged_regions = cv2.dilate(clean, kernel_h, iterations=1)

    # --- 4e. Find and Sort Regions ---
    contours, _ = cv2.findContours(merged_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bounding_boxes = []
    for c in contours:
        x, y, w_c, h_c = cv2.boundingRect(c)
        if (w_c * h_c) > 100:
            bounding_boxes.append((x, y, w_c, h_c))

    bounding_boxes.sort(key=lambda box: box[1])

    # --- 4f. Output Coordinates and Visualize ---
    print(f"Found {len(bounding_boxes)} answer regions:")

    for j, (x, y, w_box, h_box) in enumerate(bounding_boxes):
        print(f"  Region {j+1}: [x={x}, y={y}, w={w_box}, h={h_box}]")
        # ✅ Draw on the ALREADY RESIZED image - NO scaling needed
        cv2.rectangle(img_with_boxes, (x, y), (x+w_box, y+h_box), (0, 255, 0), 2)
        cv2.putText(img_with_boxes, str(j+1), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # --- 4g. Save the Result ---
    base_name = os.path.basename(image_path)
    file_name_only = os.path.splitext(base_name)[0]
    output_filename = f"evaluation_results/{file_name_only}_result.png"
    
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(img_with_boxes, cv2.COLOR_BGR2RGB))
    plt.title(f"Detected Regions for {base_name}")
    plt.axis("off")
    plt.savefig(output_filename)
    plt.close()
    
    print(f"Saved result to {output_filename}")

print("\n--- Batch processing complete. ---")