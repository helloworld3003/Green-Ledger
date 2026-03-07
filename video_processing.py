import cv2
import numpy as np
import os

def analyze_farm_video(video_path, farm_area_polygon=None):
    """
    Reads an .mp4 file, extracts frames at 1 frame per second, applies an ROI mask,
    detects green plant clusters, and calculates plant health.
    
    Args:
        video_path (str): Path to the video file.
        farm_area_polygon (list or np.ndarray, optional): Polygon list defining the farm area.
            e.g. [(x1,y1), (x2,y2), ...]. If None, the entire frame is used.
            
    Returns:
        tuple: (plant_count: int, average_green_density: float)
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return 0, 0.0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video '{video_path}'.")
        return 0, 0.0

    # Determine frames per second to process at 1 FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps != fps or fps <= 0:
        fps = 30.0 # Standard fallback
        
    frame_interval = int(round(fps))
    
    frame_count = 0
    total_plant_count = 0
    total_green_density = 0.0
    processed_frames = 0
    
    debug_frame_saved = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Extract frames (1 frame per second)
        if frame_count % frame_interval == 0:
            height, width = frame.shape[:2]
            
            # 1. Apply a polygon mask to define the "Region of Interest" (ROI)
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            
            if farm_area_polygon is not None:
                roi_corners = np.array([farm_area_polygon], dtype=np.int32)
                cv2.fillPoly(mask, roi_corners, 255)
            else:
                # If no farm area is provided, use the entire frame
                mask.fill(255)
            
            roi_frame = cv2.bitwise_and(frame, frame, mask=mask)
            
            # 2. Convert to HSV color space and apply green threshold
            hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
            
            # Broad HSV range for yellow-green to dark-green vegetation
            lower_green = np.array([15, 30, 30])
            upper_green = np.array([100, 255, 255])
            
            green_mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Calculate average green density (NDVI simulation) based on the ROI area
            roi_area_pixels = np.count_nonzero(mask)
            green_area_pixels = np.count_nonzero(green_mask)
            
            if roi_area_pixels > 0:
                green_density = green_area_pixels / roi_area_pixels
            else:
                green_density = 0.0
                
            total_green_density += green_density
            
            # Clean up the mask using morphology to remove noise
            kernel = np.ones((5, 5), np.uint8)
            cleaned_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
            cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
            
            # 3. Use cv2.findContours to detect individual plant clusters
            contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by minimum area to ignore tiny speckles
            min_area = 50
            valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            plants_in_frame = len(valid_contours)
            total_plant_count += plants_in_frame
            processed_frames += 1
            
            # 4. Bonus: Save one debug frame with bounding boxes
            if not debug_frame_saved and plants_in_frame > 0:
                debug_img = frame.copy()
                for cnt in valid_contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Draw a red bounding box
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                # Save the frame to disk
                cv2.imwrite("debug_plants.jpg", debug_img)
                debug_frame_saved = True

        frame_count += 1

    cap.release()
    
    # Calculate the averages over all sampled frames
    avg_plants = int(round(total_plant_count / processed_frames)) if processed_frames > 0 else 0
    avg_health = total_green_density / processed_frames if processed_frames > 0 else 0.0

    return avg_plants, avg_health
