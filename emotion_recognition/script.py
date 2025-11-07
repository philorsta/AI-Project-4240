# pip install deepface opencv-python
# pip install tf-keras
import os
import argparse
import threading
import queue
import time
import cv2
from deepface import DeepFace
from collections import Counter, deque

VIDEO_PATH = "happy_1.mp4"   # fallback video file (used if no CLI arg given)
VIDEOS_DIR = "videos"        # default folder to look for videos when you pass a filename
SAMPLE_EVERY_N_FRAMES = 5       # sample every 5th frame (adjust for speed)
FRAME_LIMIT = None              # set to an int to limit frames processed (or None)
DISPLAY = True                  # show video window with overlay
WINDOW_NAME = "DeepFace - Emotion"
SMOOTH_WINDOW = 7               # rolling window size for smoothing predictions
MIN_CONF = 40.0                 # minimum confidence percent required to accept a prediction into the window

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

def analyze_video(video_path):
    vid = cv2.VideoCapture(video_path)
    if not vid.isOpened():
        print(f"ERROR: cannot open video: {video_path}")
        return {"per_frame_counts": {}, "overall": "neutral", "frames_analyzed": 0}
    frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = vid.get(cv2.CAP_PROP_FPS) or 25
    # get source frame size
    src_w = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    src_h = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    print(f"Frames: {frame_count}, FPS: {fps}")
    idx = 0
    processed = 0
    results = []

    # For smooth playback: use a worker thread to do heavy analysis while main thread displays frames
    frame_q = queue.Queue(maxsize=4)
    result_lock = threading.Lock()
    shared = {"label": "", "conf": 0.0, "processed": 0}
    stop_event = threading.Event()

    class AnalyzerWorker(threading.Thread):
        def __init__(self, q, shared, lock, stop_event):
            super().__init__(daemon=True)
            self.q = q
            self.shared = shared
            self.lock = lock
            self.stop_event = stop_event

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
                    # Smaller frames speed up inference; keep aspect but reduce size
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = rgb.shape[:2]
                    # resize to width 320 for faster processing if larger
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
                            # record per-frame mapped labels for aggregate counts
                            try:
                                results.append(mapped)
                            except Exception:
                                pass
                except Exception as e:
                    # occasional failures are expected; log sparsely
                    if frame_idx % 100 == 0:
                        print(f"worker frame {frame_idx} error: {e}")
                finally:
                    try:
                        self.q.task_done()
                    except Exception:
                        pass

    worker = AnalyzerWorker(frame_q, shared, result_lock, stop_event)
    worker.start()

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
            except Exception:
                screen_w, screen_h = src_w or 800, src_h or 600

            # compute target window size preserving aspect ratio and fitting screen
            if src_w and src_h:
                scale = min(1.0, float(screen_w) / src_w, float(screen_h) / src_h)
                target_w = max(100, int(src_w * scale))
                target_h = max(100, int(src_h * scale))
                cv2.resizeWindow(WINDOW_NAME, target_w, target_h)
        except Exception:
            # best-effort: continue without crashing if window ops fail
            pass

    # deques for smoothing predictions
    preds = deque(maxlen=SMOOTH_WINDOW)
    pred_confs = deque(maxlen=SMOOTH_WINDOW)
    prev_display_label = ""

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
        # Draw overlay and show frame (use latest worker result)
        if DISPLAY:
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

    out = analyze_video(video_path)
    print("Frames analyzed:", out["frames_analyzed"])
    print("Per-frame counts:", out["per_frame_counts"])
    print("Overall video emotion (majority):", out["overall"])
