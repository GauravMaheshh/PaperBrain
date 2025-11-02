import cv2
import matplotlib.pyplot as plt
from alignment_agent import run_alignment_agent # Import your new agent

# --- 1. DEFINE FILE PATHS ---
# template_path = "templates/2.jpg"
# scan_path = "scans/scan_2.jpg"

# --- 2. RUN AGENT 1 ---
# This one line runs all the logic from your old script
img_aligned, H, score = run_alignment_agent(template_path, scan_path)

# --- Initial Setup ---
if img_aligned is not None:
    print(f"\n--- Agent 1 Succeeded ---")
    print(f"Alignment Score: {score}")
    print(f"Transformation (H): \n{H}")
    
    # Save the output (optional)
    cv2.imwrite("aligned_output.jpg", img_aligned)
    print("Saved aligned image as 'aligned_output.jpg'")

    # --- 4. VISUALIZE RESULTS ---
    # Load originals just for plotting
    img_template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    img_scan_orig = cv2.imread(scan_path, cv2.IMREAD_GRAYSCALE)

    plt.figure(figsize=(20, 10))
    
    plt.subplot(1, 3, 1)
    plt.imshow(img_template_orig, cmap='gray')
    plt.title("1. Original Template")

    plt.subplot(1, 3, 2)
    plt.imshow(img_scan_orig, cmap='gray')
    plt.title("2. Distorted Scan")

    plt.subplot(1, 3, 3)
    plt.imshow(img_aligned, cmap='gray')
    plt.title("3. Aligned Result (SUCCESS)")

    plt.suptitle("Alignment Agent Output")
    plt.show()

    # --- 5. NEXT STEP ---
    print("This 'img_aligned' object is now ready to be passed to Agent 2 (Difference Finder).")

else:
    print(f"\n--- Agent 1 FAILED ---")
    print(f"Alignment Score: {score}")
    print("Could not align image. See logs above.")
    
    # (Optional: Visualize the failure)
    plt.figure(figsize=(20, 10))
    img_template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    img_scan_orig = cv2.imread(scan_path, cv2.IMREAD_GRAYSCALE)

    plt.subplot(1, 2, 1)
    plt.imshow(img_template_orig, cmap='gray')
    plt.title("1. Original Template")
    
    plt.subplot(1, 2, 2)
    plt.imshow(img_scan_orig, cmap='gray')
    plt.title("2. Distorted Scan (Alignment FAILED)")
    plt.show()
