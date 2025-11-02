import cv2
import numpy as np

def run_alignment_agent(template_path, scan_path):
    """
    This is the core function for Agent 1: The Aligner.
    
    It takes a template and a scan, performs alignment, and returns
    the results required by the problem statement.
    """
    print(f"[Agent 1] Loading images: {template_path}, {scan_path}")
    
    # 1. LOAD IMAGES
    img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    img_scan = cv2.imread(scan_path, cv2.IMREAD_GRAYSCALE)

    if img_template is None or img_scan is None:
        print("[Agent 1] Error: Could not load images. Check paths.")
        return None, None, 0 # Return failure

    # 2. FEATURE DETECTION (ORB)
    orb = cv2.ORB_create(nfeatures=5000)
    kp_template, des_template = orb.detectAndCompute(img_template, None)
    kp_scan, des_scan = orb.detectAndCompute(img_scan, None)

    # 3. FEATURE MATCHING (Brute-Force)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des_template, des_scan)
    matches = sorted(matches, key=lambda x: x.distance)
    num_good_matches = int(len(matches) * 0.1)
    good_matches = matches[:num_good_matches]
    
    alignment_score = len(good_matches)
    print(f"[Agent 1] Alignment confidence score: {alignment_score}")

    # --- Minimal Validation ---
    if alignment_score < 10:
        print(f"[Agent 1] VALIDATION FAILED: Score {alignment_score} is too low. Skipping.")
        return None, None, alignment_score # Return failure

    # 4. FIND HOMOGRAPHY (Calculate Distortion)
    points_template = np.float32([kp_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    points_scan = np.float32([kp_scan[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(points_scan, points_template, cv2.RANSAC, 5.0)
    
    # 5. WARPING (Apply Correction)
    height, width = img_template.shape
    img_aligned = cv2.warpPerspective(img_scan, H, (width, height))
    print("[Agent 1] Success: Image aligned.")

    # Return all deliverables
    # H = transformation_parameters
    # alignment_score = alignment_accuracy
    return img_aligned, H, alignment_score
