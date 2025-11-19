"""
Name: Emotion Recognition in Video using DeepFace
Filename: script.py
Date: 11 / 19 / 25
Purpose: Analyze video files to detect and display human emotions using DeepFace.
How to run:
1. Follow instructions in README_ENV.md to setup env
2. Run the script with a video file path or filename in the videos folder.
  2a. Example: python script.py happy_1.mp4
  2b. Example with full path: python script.py /path/to/video.mp4
  2c. Example with output video: python script.py happy_1.mp4 --output desired_filename.mp4
"""

# Packages required:
import os
import argparse
import threading
import queue
import time
import cv2
from deepface import DeepFace
from collections import Counter, deque

# Configuration defaults
VIDEO_PATH = "happy_1.mp4"      # fallback video file (used if no CLI arg given)
VIDEOS_DIR = "videos"           # default folder to look for videos when you pass a filename
SAMPLE_EVERY_N_FRAMES = 5       # sample every 5th frame (adjust for speed)
FRAME_LIMIT = None              # set to an int to limit frames processed (or None)
DISPLAY = True                  # show video window with overlay
WINDOW_NAME = "DeepFace - Emotion"
SMOOTH_WINDOW = 7               # rolling window size for smoothing predictions
MIN_CONF = 40.0                 # minimum confidence percent required to accept a prediction into the window
EMOJI_DIR = "emoji"             # folder containing emoji PNGs
EMOJI_FILES = {                 # map of label -> filename
    "happy": "happy.png",
    "neutral": "neutral.png",
    "sad": "sad.png",
}

# Map DeepFace emotion labels to your 3 classes
MAP_TO_3 = {
    "happy": "happy",
    "sad": "sad",
    "neutral": "neutral",
    # map other DeepFace emotions to neutral (or choose custom mapping)
    "angry": "neutral",
    "disgust": "neutral",
    "fear": "neutral",
    "surprise": "neutral"
}

"""
Function: analyze_video
Purpose: Analyze a video file for emotions using DeepFace, 
display overlays, and optionally write output video.
"""
def analyze_video(video_path, output_path=None):
    # open video file
    vid = cv2.VideoCapture(video_path)
    if not vid.isOpened():
        print(f"ERROR: cannot open video: {video_path}")
        return {"per_frame_counts": {}, "overall": "neutral", "frames_analyzed": 0}
    
    # get video properties
    frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = vid.get(cv2.CAP_PROP_FPS) or 25
    
    # get source frame size
    src_w = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    src_h = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    # print video properties
    print(f"Frames: {frame_count}, FPS: {fps}")
    idx = 0
    processed = 0
    results = []

    """
    Helper Function: overlay_image_alpha
    Purpose: Overlay an RGBA (or RGB) image onto a BGR frame using alpha blending
    """
    def overlay_image_alpha(img, overlay, x, y, overlay_size=None):
        # Check if overlay is valid
        if overlay is None:
            return img
        # resize overlay if requested (overlay_size is (w, h))
        if overlay_size is not None:
            try:
                overlay = cv2.resize(overlay, overlay_size, interpolation=cv2.INTER_AREA)
            except Exception:
                pass
            
        # get dimensions
        h_ol, w_ol = overlay.shape[:2]
        h_img, w_img = img.shape[:2]
        # check if overlay is within image bounds
        if x >= w_img or y >= h_img:
            return img
        
        # clip overlay to image bounds
        x1 = max(x, 0)
        y1 = max(y, 0)
        x2 = min(x + w_ol, w_img)
        y2 = min(y + h_ol, h_img)
        ol_x1 = x1 - x
        ol_y1 = y1 - y
        ol_x2 = ol_x1 + (x2 - x1)
        ol_y2 = ol_y1 + (y2 - y1)
        overlay_cropped = overlay[ol_y1:ol_y2, ol_x1:ol_x2]
        
        # blend overlay onto image
        if overlay_cropped.size == 0:
            return img
        
        # blend using alpha channel if present
        if overlay_cropped.shape[2] == 4:
            alpha = overlay_cropped[:, :, 3].astype(float) / 255.0
            alpha = alpha[..., None]
            overlay_rgb = overlay_cropped[:, :, :3].astype(float)
            roi = img[y1:y2, x1:x2].astype(float)
            blended = overlay_rgb * alpha + roi * (1 - alpha)
            img[y1:y2, x1:x2] = blended.astype(img.dtype)
        # RGB overlay without alpha
        else:
            img[y1:y2, x1:x2] = overlay_cropped[:, :, :3]
        return img

    # Prepare output writer if requested
    writer = None
    if output_path:
        # use mp4v for .mp4 output
        try:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (src_w, src_h))
            # check if writer opened successfully
            if not writer.isOpened():
                print(f"WARNING: failed to open VideoWriter for {output_path}; output will be disabled")
                writer = None
            # log output path
            else:
                print(f"Writing output video to: {output_path}")
        # catch exceptions creating writer
        except Exception as e:
            print(f"WARNING: could not create VideoWriter: {e}")
            writer = None

    # For smooth playback: use a worker thread to do heavy analysis while main thread displays frames
    frame_q = queue.Queue(maxsize=4)
    result_lock = threading.Lock()
    shared = {"label": "", "conf": 0.0, "processed": 0}
    stop_event = threading.Event()

    """
    Class: AnalyzerWorker
    Purpose: Background thread to analyze frames from the queue using DeepFace  
    """
    class AnalyzerWorker(threading.Thread):
        """
        Function: __init__
        Purpose: Initialize the worker thread with queue, shared data, lock, and stop event.
        """
        def __init__(self, q, shared, lock, stop_event):
            # Initialize the base thread class
            super().__init__(daemon=True)
            self.q = q
            self.shared = shared
            self.lock = lock
            self.stop_event = stop_event

        """
        Function: run
        Purpose: Process frames from the queue, analyze emotions, and update shared results.    
        """
        def run(self):
            # process frames until stop event is set
            while not self.stop_event.is_set():
                # get next frame from queue
                try:
                    item = self.q.get(timeout=0.5)
                # timeout -> check stop event again
                except queue.Empty:
                    continue
                
                # check for sentinel to exit
                if item is None:
                    self.q.task_done()
                    break
                frame_idx, frame = item
                
                # analyze frame
                try:
                    # Smaller frames speed up inference; keep aspect but reduce size
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = rgb.shape[:2]
                    # resize to width 320 for faster processing if larger
                    if w > 320:
                        scale = 320.0 / w
                        small = cv2.resize(rgb, (0, 0), fx=scale, fy=scale)
                    else:
                        small = rgb

                    # perform emotion analysis
                    analysis = DeepFace.analyze(small, actions=["emotion"], enforce_detection=False)
                    # handle list result
                    if isinstance(analysis, list) and len(analysis) > 0:
                        analysis = analysis[0]
                    emotion_scores = {}
                    # extract emotion scores
                    if isinstance(analysis, dict):
                        emotion_scores = analysis.get("emotion") or {}
                    mapped = None
                    score = 0.0
                    
                    # determine top emotion and map to 3-class label
                    if emotion_scores:
                        top = max(emotion_scores.items(), key=lambda x: x[1])[0]
                        mapped = MAP_TO_3.get(top, "neutral")
                        score = emotion_scores.get(top, 0.0)
                    
                    # fallback to dominant_emotion if scores missing
                    else:
                        dominant = analysis.get("dominant_emotion") if isinstance(analysis, dict) else None
                        if dominant:
                            mapped = MAP_TO_3.get(dominant, "neutral")
                            score = 0.0

                    # update shared results
                    if mapped:
                        with self.lock:
                            self.shared["label"] = mapped
                            self.shared["conf"] = score
                            self.shared["processed"] += 1
                            # record per-frame mapped labels for aggregate counts
                            try:
                                results.append(mapped)
                            except Exception:
                                pass
                            
                # handle analysis errors
                except Exception as e:
                    if frame_idx % 100 == 0:
                        print(f"worker frame {frame_idx} error: {e}")
                        
                # mark task done
                finally:
                    try:
                        self.q.task_done()
                    except Exception:
                        pass

    # start the analyzer worker thread
    worker = AnalyzerWorker(frame_q, shared, result_lock, stop_event)
    worker.start()

    # Load emoji images (if present) once to avoid repeated disk access
    emoji_imgs = {}
    try:
        for label, fname in EMOJI_FILES.items():
            path = os.path.join(EMOJI_DIR, fname)
            # load image if file exists
            if os.path.isfile(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                # warn if load failed
                if img is None:
                    print(f"WARNING: failed to load emoji: {path}")
                # store loaded image
                else:
                    emoji_imgs[label] = img
            else:
                # file not found; skip
                pass
    except Exception:
        pass

    # Prepare display window to avoid automatic OS/window scaling/zooming
    if DISPLAY:
        try:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            # try to get screen size (Windows). Fall back to source size.
            try:
                import ctypes
                user32 = ctypes.windll.user32
                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
            # fallback for other OSes
            except Exception:
                screen_w, screen_h = src_w or 800, src_h or 600

            # compute target window size preserving aspect ratio and fitting screen
            if src_w and src_h:
                scale = min(1.0, float(screen_w) / src_w, float(screen_h) / src_h)
                target_w = max(100, int(src_w * scale))
                target_h = max(100, int(src_h * scale))
                cv2.resizeWindow(WINDOW_NAME, target_w, target_h)
        except Exception:
            # window setup failed; continue without resizing
            pass

    # deques for smoothing predictions
    preds = deque(maxlen=SMOOTH_WINDOW)
    pred_confs = deque(maxlen=SMOOTH_WINDOW)
    prev_display_label = ""

    # main loop: read frames, display with overlay, enqueue for analysis
    while True:
        ret, frame = vid.read()
        if not ret:
            break
        if idx % SAMPLE_EVERY_N_FRAMES == 0:
            # enqueue sampled frames for background analysis; don't block display
            try:
                frame_q.put_nowait((idx, frame.copy()))
            except queue.Full:
                # drop this sample if worker is busy
                pass
            except Exception as e:
                # DeepFace can occasionally fail on a frame — skip
                print(f"frame {idx} analysis error: {e}")
        idx += 1
        # Build display_frame with overlays (text + emoji) regardless of display mode
        display_frame = frame.copy()
        # read latest result
        with result_lock:
            last_label = shared.get("label", "")
            last_conf = shared.get("conf", 0.0)

        # smoothing + confidence threshold: only accept predictions above MIN_CONF into the rolling window
        if last_label and (last_conf >= MIN_CONF):
            preds.append(last_label)
            pred_confs.append(last_conf)

        # choose display label: majority in window if available, otherwise keep previous label
        if len(preds) > 0:
            most = Counter(preds).most_common(1)[0]
            display_label = most[0]
            display_conf = sum(pred_confs) / len(pred_confs) if len(pred_confs) > 0 else last_conf
            prev_display_label = display_label
            text = f"{display_label} ({display_conf:.1f}%)"
        else:
            # no recent high-confidence predictions; fall back to previous displayed label to avoid flicker
            if prev_display_label:
                text = f"{prev_display_label}"
            else:
                text = "no prediction"
        cv2.putText(display_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

        # Overlay emoji image in the top-right if available for the current label
        try:
            emoji_label = None
            if len(preds) > 0:
                emoji_label = display_label
            elif prev_display_label:
                emoji_label = prev_display_label
            if emoji_label and emoji_label in emoji_imgs:
                emo_img = emoji_imgs[emoji_label]
                fw = display_frame.shape[1]
                # determine emoji width relative to frame, clamped
                ew = min(120, max(48, fw // 8))
                # preserve overlay aspect
                eh = int(ew * (emo_img.shape[0] / max(1, emo_img.shape[1])))
                x = display_frame.shape[1] - ew - 10
                y = 10
                display_frame = overlay_image_alpha(display_frame, emo_img, x, y, (ew, eh))
        except Exception:
            pass

        # write frame to output if writer is active
        if writer is not None:
            try:
                # ensure frame size matches writer expectations
                if (display_frame.shape[1], display_frame.shape[0]) != (src_w, src_h):
                    out_frame = cv2.resize(display_frame, (src_w, src_h))
                else:
                    out_frame = display_frame
                writer.write(out_frame)
            except Exception:
                pass

        # show the window if requested
        if DISPLAY:
            cv2.imshow(WINDOW_NAME, display_frame)
            # waitKey: compute a delay from FPS (but not less than 1)
            delay = max(1, int(1000.0 / fps))
            key = cv2.waitKey(delay) & 0xFF
            if key == ord('q'):
                print('User requested exit (q)')
                break
        if FRAME_LIMIT and processed >= FRAME_LIMIT:
            break

    vid.release()
    # shut down worker
    stop_event.set()
    try:
        # put sentinel to wake worker if needed
        frame_q.put_nowait(None)
    except Exception:
        pass
    worker.join(timeout=2.0)
    if DISPLAY:
        cv2.destroyAllWindows()
    # release video writer if used
    if writer is not None:
        try:
            writer.release()
            print(f"Finished writing output: {output_path}")
        except Exception:
            pass
    # Aggregate per-video label (majority vote) and per-frame counts
    # aggregate using worker-processed count if available
    counts = Counter(results)
    # try to use shared processed count as authoritative
    processed = shared.get("processed", processed)
    if len(results) == 0:
        overall = shared.get("label", "neutral") or "neutral"
    else:
        overall = counts.most_common(1)[0][0]
    return {"per_frame_counts": dict(counts), "overall": overall, "frames_analyzed": processed}

def _parse_args():
    parser = argparse.ArgumentParser(description="Analyze a video with DeepFace and display emotion overlay.")
    parser.add_argument("video", nargs="?", default=None,
                        help="Video filename located in the videos folder or a full path. If omitted, uses the default VIDEO_PATH in the script.")
    parser.add_argument("--videos-dir", default=VIDEOS_DIR, help="Folder to look for video files when a filename is provided (default: videos)")
    parser.add_argument("--sample", type=int, default=SAMPLE_EVERY_N_FRAMES, help="Sample every N frames (default from script)")
    parser.add_argument("--limit", type=int, default=FRAME_LIMIT if FRAME_LIMIT is not None else 0, help="Limit number of frames analyzed (default: none). Use 0 for no limit.")
    parser.add_argument("--window", type=int, default=SMOOTH_WINDOW, help="Smoothing window size (number of predictions to aggregate, default: 7)")
    parser.add_argument("--min-conf", type=float, default=MIN_CONF, help="Minimum confidence percent required to accept a prediction into the smoothing window (default: 40.0)")
    parser.add_argument("--no-display", action="store_true", help="Run without showing the video window (headless)")
    parser.add_argument("--output", "-o", default=None, help="Path to write output MP4 with overlays (e.g. out.mp4)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Resolve video path: accept full path or filename inside videos dir
    if args.video is None:
        video_path = VIDEO_PATH
    else:
        # if user passed a full path that exists, use it
        if os.path.isabs(args.video) or os.path.sep in args.video:
            # treat as a path
            if os.path.isfile(args.video):
                video_path = args.video
            else:
                print(f"ERROR: specified video path does not exist: {args.video}")
                raise SystemExit(1)
        else:
            # treat as filename in videos dir
            candidate = os.path.join(args.videos_dir, args.video)
            if os.path.isfile(candidate):
                video_path = candidate
            else:
                # Do NOT fall back to a default — fail fast and list available files
                print(f"ERROR: {candidate} not found.")
                if os.path.isdir(args.videos_dir):
                    files = [f for f in os.listdir(args.videos_dir) if os.path.isfile(os.path.join(args.videos_dir, f))]
                    if files:
                        print(f"Files in {args.videos_dir}:")
                        for f in files:
                            print(" -", f)
                    else:
                        print(f"No files found in {args.videos_dir}.")
                raise SystemExit(1)

    # Apply runtime overrides
    SAMPLE_EVERY_N_FRAMES = max(1, int(args.sample))
    FRAME_LIMIT = int(args.limit) if args.limit and args.limit > 0 else None
    DISPLAY = not args.no_display
    # smoothing parameters
    SMOOTH_WINDOW = max(1, int(args.window))
    MIN_CONF = float(args.min_conf)

    out = analyze_video(video_path, output_path=args.output)
    print("Frames analyzed:", out["frames_analyzed"])
    print("Per-frame counts:", out["per_frame_counts"])
    print("Overall video emotion (majority):", out["overall"])
