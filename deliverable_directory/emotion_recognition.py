"""
Emotion Recognition Module
--------------------------
Purpose: Analyze video files to detect and display human emotions using DeepFace.
Outputs a video with emotion overlays (text + emoji) but NO audio track.
"""

import os
import cv2
import threading
import queue
from deepface import DeepFace
from collections import Counter, deque

# Configuration
SAMPLE_EVERY_N_FRAMES = 5
SMOOTH_WINDOW = 15  # Increased from 7 to 15 for more stability
MIN_CONF = 50.0  # Increased from 40 to 50 to filter out weak predictions
EMOJI_HOLD_FRAMES = 90  # Hold emoji for at least 90 frames (~3 seconds at 30fps)
EMOJI_DIR = "emoji"
EMOJI_FILES = {
    "happy": "happy.png",
    "neutral": "neutral.png",
    "sad": "sad.png",
}

# Map DeepFace emotion labels to 3 classes
MAP_TO_3 = {
    "happy": "happy",
    "sad": "sad",
    "neutral": "neutral",
    "angry": "neutral",
    "disgust": "neutral",
    "fear": "neutral",
    "surprise": "neutral"
}


def overlay_image_alpha(img, overlay, x, y, overlay_size=None):
    """Overlay an RGBA (or RGB) image onto a BGR frame using alpha blending"""
    if overlay is None:
        return img
    
    if overlay_size is not None:
        try:
            overlay = cv2.resize(overlay, overlay_size, interpolation=cv2.INTER_AREA)
        except Exception:
            pass
    
    h_ol, w_ol = overlay.shape[:2]
    h_img, w_img = img.shape[:2]
    
    if x >= w_img or y >= h_img:
        return img
    
    x1 = max(x, 0)
    y1 = max(y, 0)
    x2 = min(x + w_ol, w_img)
    y2 = min(y + h_ol, h_img)
    ol_x1 = x1 - x
    ol_y1 = y1 - y
    ol_x2 = ol_x1 + (x2 - x1)
    ol_y2 = ol_y1 + (y2 - y1)
    overlay_cropped = overlay[ol_y1:ol_y2, ol_x1:ol_x2]
    
    if overlay_cropped.size == 0:
        return img
    
    if overlay_cropped.shape[2] == 4:
        alpha = overlay_cropped[:, :, 3].astype(float) / 255.0
        alpha = alpha[..., None]
        overlay_rgb = overlay_cropped[:, :, :3].astype(float)
        roi = img[y1:y2, x1:x2].astype(float)
        blended = overlay_rgb * alpha + roi * (1 - alpha)
        img[y1:y2, x1:x2] = blended.astype(img.dtype)
    else:
        img[y1:y2, x1:x2] = overlay_cropped[:, :, :3]
    
    return img


class AnalyzerWorker(threading.Thread):
    """Background thread to analyze frames using DeepFace"""
    
    def __init__(self, q, shared, lock, stop_event, results):
        super().__init__(daemon=True)
        self.q = q
        self.shared = shared
        self.lock = lock
        self.stop_event = stop_event
        self.results = results
    
    def run(self):
        while not self.stop_event.is_set():
            try:
                item = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            
            if item is None:
                self.q.task_done()
                break
            
            frame_idx, frame = item
            
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                
                if w > 320:
                    scale = 320.0 / w
                    small = cv2.resize(rgb, (0, 0), fx=scale, fy=scale)
                else:
                    small = rgb
                
                analysis = DeepFace.analyze(small, actions=["emotion"], enforce_detection=False)
                
                if isinstance(analysis, list) and len(analysis) > 0:
                    analysis = analysis[0]
                
                emotion_scores = {}
                if isinstance(analysis, dict):
                    emotion_scores = analysis.get("emotion") or {}
                
                mapped = None
                score = 0.0
                
                if emotion_scores:
                    top = max(emotion_scores.items(), key=lambda x: x[1])[0]
                    mapped = MAP_TO_3.get(top, "neutral")
                    score = emotion_scores.get(top, 0.0)
                else:
                    dominant = analysis.get("dominant_emotion") if isinstance(analysis, dict) else None
                    if dominant:
                        mapped = MAP_TO_3.get(dominant, "neutral")
                        score = 0.0
                
                if mapped:
                    with self.lock:
                        self.shared["label"] = mapped
                        self.shared["conf"] = score
                        self.shared["processed"] += 1
                        try:
                            self.results.append(mapped)
                        except Exception:
                            pass
            
            except Exception as e:
                if frame_idx % 100 == 0:
                    print(f"Worker frame {frame_idx} error: {e}")
            
            finally:
                try:
                    self.q.task_done()
                except Exception:
                    pass


def process_video_emotions(input_video_path, output_video_path):
    """
    Process video for emotion recognition and create output video with overlays.
    Returns path to the output video (WITHOUT audio).
    """
    print(f"\nProcessing emotions for: {input_video_path}")
    
    vid = cv2.VideoCapture(str(input_video_path))
    if not vid.isOpened():
        raise ValueError(f"Cannot open video: {input_video_path}")
    
    frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = vid.get(cv2.CAP_PROP_FPS) or 25
    src_w = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties - Frames: {frame_count}, FPS: {fps}, Resolution: {src_w}x{src_h}")
    
    # Prepare video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (src_w, src_h))
    
    if not writer.isOpened():
        raise ValueError(f"Failed to open VideoWriter for {output_video_path}")
    
    print(f"Writing emotion-overlayed video to: {output_video_path}")
    
    # Load emoji images
    emoji_imgs = {}
    try:
        for label, fname in EMOJI_FILES.items():
            path = os.path.join(EMOJI_DIR, fname)
            if os.path.isfile(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    emoji_imgs[label] = img
    except Exception as e:
        print(f"Warning: Could not load some emoji images: {e}")
    
    # Threading setup
    frame_q = queue.Queue(maxsize=4)
    result_lock = threading.Lock()
    shared = {"label": "", "conf": 0.0, "processed": 0}
    stop_event = threading.Event()
    results = []
    
    worker = AnalyzerWorker(frame_q, shared, result_lock, stop_event, results)
    worker.start()
    
    # Smoothing buffers
    preds = deque(maxlen=SMOOTH_WINDOW)
    pred_confs = deque(maxlen=SMOOTH_WINDOW)
    prev_display_label = ""
    
    # Emoji stability tracking
    current_emoji = None
    emoji_frame_counter = 0
    emoji_change_threshold = 0.7  # Need 70% consensus to change emoji
    
    idx = 0
    
    # Process frames
    while True:
        ret, frame = vid.read()
        if not ret:
            break
        
        # Sample for analysis
        if idx % SAMPLE_EVERY_N_FRAMES == 0:
            try:
                frame_q.put_nowait((idx, frame.copy()))
            except queue.Full:
                pass
            except Exception as e:
                print(f"Frame {idx} analysis error: {e}")
        
        idx += 1
        display_frame = frame.copy()
        
        # Get latest result
        with result_lock:
            last_label = shared.get("label", "")
            last_conf = shared.get("conf", 0.0)
        
        # Apply smoothing
        if last_label and (last_conf >= MIN_CONF):
            preds.append(last_label)
            pred_confs.append(last_conf)
        
        # Determine display label with better smoothing
        if len(preds) > 0:
            # Get emotion counts in the window
            emotion_counts = Counter(preds)
            most = emotion_counts.most_common(1)[0]
            display_label = most[0]
            display_conf = sum(pred_confs) / len(pred_confs) if len(pred_confs) > 0 else last_conf
            
            # Check if we have strong consensus (for emoji stability)
            total_preds = len(preds)
            consensus_ratio = most[1] / total_preds if total_preds > 0 else 0
            
            # Update emoji only if we have strong consensus or hold time expired
            if current_emoji is None:
                current_emoji = display_label
                emoji_frame_counter = 0
            elif emoji_frame_counter >= EMOJI_HOLD_FRAMES:
                # Hold time expired, allow change if consensus is strong
                if consensus_ratio >= emoji_change_threshold:
                    if current_emoji != display_label:
                        current_emoji = display_label
                        emoji_frame_counter = 0
            else:
                # Still in hold period
                emoji_frame_counter += 1
            
            prev_display_label = display_label
            text = f"{display_label} ({display_conf:.1f}%)"
        else:
            if prev_display_label:
                text = f"{prev_display_label}"
            else:
                text = "analyzing..."
        
        # Draw text overlay
        cv2.putText(display_frame, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Draw emoji overlay (use current_emoji instead of display_label for stability)
        try:
            emoji_label = current_emoji if current_emoji else prev_display_label
            
            if emoji_label and emoji_label in emoji_imgs:
                emo_img = emoji_imgs[emoji_label]
                fw = display_frame.shape[1]
                ew = min(120, max(48, fw // 8))
                eh = int(ew * (emo_img.shape[0] / max(1, emo_img.shape[1])))
                x = display_frame.shape[1] - ew - 10
                y = 10
                display_frame = overlay_image_alpha(display_frame, emo_img, x, y, (ew, eh))
        except Exception:
            pass
        
        # Write frame
        try:
            if (display_frame.shape[1], display_frame.shape[0]) != (src_w, src_h):
                out_frame = cv2.resize(display_frame, (src_w, src_h))
            else:
                out_frame = display_frame
            writer.write(out_frame)
        except Exception as e:
            print(f"Error writing frame {idx}: {e}")
    
    # Cleanup
    vid.release()
    writer.release()
    
    stop_event.set()
    try:
        frame_q.put_nowait(None)
    except Exception:
        pass
    worker.join(timeout=2.0)
    
    # Statistics
    counts = Counter(results)
    processed = shared.get("processed", 0)
    
    if len(results) > 0:
        overall = counts.most_common(1)[0][0]
    else:
        overall = shared.get("label", "neutral") or "neutral"
    
    print(f"Emotion processing complete!")
    print(f"Frames analyzed: {processed}")
    print(f"Per-frame counts: {dict(counts)}")
    print(f"Overall video emotion: {overall}")
    
    return output_video_path