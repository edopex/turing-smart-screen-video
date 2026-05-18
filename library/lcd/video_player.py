# SPDX-License-Identifier: GPL-3.0-or-later
import os
import time
import threading
from typing import List, Tuple
from PIL import Image, ImageSequence, ImageChops

from library.log import logger
import library.config as config

try:
    import cv2
except ImportError:
    cv2 = None

class LcdVideoPlayer:
    def __init__(self, lcd_comm, file_path: str, x: int = 0, y: int = 0, 
                 width: int = 0, height: int = 0, max_queue_size: int = 4, pre_cache: bool = True):
        """
        A highly optimized, unified GIF and MP4 Video player for Turing Smart Screen displays.
        
        Args:
            lcd_comm: The active LcdComm driver instance.
            file_path: Path to the animated GIF or video file (.mp4, .avi, .webm, etc.).
            x: Target X position on the screen.
            y: Target Y position on the screen.
            width: Target width (0 to use native dimensions).
            height: Target height (0 to use native dimensions).
            max_queue_size: If the queue size exceeds this limit, we drop frames to avoid lag.
            pre_cache: If True, pre-decode and cache all frames in RAM for zero-CPU looping.
                       If False, read frames dynamically from disk (best for long videos).
        """
        self.lcd = lcd_comm
        self.file_path = file_path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_queue_size = max_queue_size
        self.pre_cache = pre_cache
        
        self.is_gif = file_path.lower().endswith(('.gif', '.apng'))
        self.frames: List[Tuple[Image.Image, float]] = []
        self._stop_event = threading.Event()
        self._thread = None
        self.is_playing = False
        
        # Native dimensions & video properties
        self.native_width = 0
        self.native_height = 0
        self.fps = 25.0
        self.frame_delay = 0.04

    def load(self):
        """Loads video or GIF properties, and pre-caches frames if enabled."""
        logger.info(f"Loading media asset: {self.file_path} (Format: {'GIF' if self.is_gif else 'VIDEO'})")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Media file not found: {self.file_path}")

        if self.is_gif:
            self._load_gif()
        else:
            self._load_video()

        # Resolve target size
        self.width = self.width if self.width > 0 else self.native_width
        self.height = self.height if self.height > 0 else self.native_height
        
        # Cap to screen boundaries
        self.width = min(self.width, self.lcd.get_width())
        self.height = min(self.height, self.lcd.get_height())

        logger.info(f"Media loaded: {self.native_width}x{self.native_height} at {self.fps:.1f} FPS. "
                    f"Target playback: {self.width}x{self.height} at ({self.x}, {self.y})")

    def _load_gif(self):
        try:
            gif = Image.open(self.file_path)
            self.native_width, self.native_height = gif.size
            duration = gif.info.get("duration", 100)
            if duration <= 0:
                duration = 100
            self.fps = 1000.0 / duration
            self.frame_delay = duration / 1000.0
            
            if self.pre_cache:
                logger.info("Pre-caching GIF frames in RAM...")
                raw_frames = []
                for frame in ImageSequence.Iterator(gif):
                    frame_image = frame.copy().convert("RGB")
                    # Pre-resize if dimensions differ
                    if self.width > 0 and (frame_image.width != self.width or frame_image.height != self.height):
                        frame_image = frame_image.resize((self.width, self.height), Image.Resampling.BILINEAR)
                    
                    frame_dur = frame.info.get("duration", 100)
                    if frame_dur <= 0:
                        frame_dur = 100
                    raw_frames.append((frame_image, frame_dur / 1000.0))
                
                # Now compute delta-cropped frames to optimize USB serial transfer bandwidth
                logger.info("Computing delta frame compression...")
                self.frames = []
                prev_frame = None
                for i, (frame_image, duration) in enumerate(raw_frames):
                    # Force first frame (and once every 60 frames) to render in full as a keyframe / recovery sync point
                    if i == 0 or prev_frame is None or (i % 60 == 0):
                        self.frames.append((frame_image, self.x, self.y, duration))
                    else:
                        diff = ImageChops.difference(frame_image, prev_frame)
                        bbox = diff.getbbox()
                        if bbox is None:
                            # Frame is identical to previous, send None to skip transmission
                            self.frames.append((None, self.x, self.y, duration))
                        else:
                            left, upper, right, lower = bbox
                            cropped = frame_image.crop(bbox)
                            self.frames.append((cropped, self.x + left, self.y + upper, duration))
                    prev_frame = frame_image
                logger.info(f"Successfully cached and delta-compressed {len(raw_frames)} GIF frames.")
        except Exception as e:
            logger.error(f"Failed to load GIF {self.file_path}: {e}")
            raise e

    def _load_video(self):
        if cv2 is None:
            raise ImportError("OpenCV ('opencv-python-headless') is required to play video files.")
            
        cap = cv2.VideoCapture(self.file_path)
        if not cap.isOpened():
            raise IOError(f"OpenCV could not open video file: {self.file_path}")
            
        self.native_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.native_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 25.0
        self.frame_delay = 1.0 / self.fps
        
        if self.pre_cache:
            logger.info("Pre-caching video frames in RAM...")
            raw_frames = []
            
            # Temporary target size for resizing during load
            t_w = self.width if self.width > 0 else self.native_width
            t_h = self.height if self.height > 0 else self.native_height
            t_w = min(t_w, self.lcd.get_width())
            t_h = min(t_h, self.lcd.get_height())
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR (OpenCV format) to RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(rgb)
                
                # Resize on the fly
                if pil_frame.width != t_w or pil_frame.height != t_h:
                    pil_frame = pil_frame.resize((t_w, t_h), Image.Resampling.BILINEAR)
                    
                raw_frames.append(pil_frame)
                
            cap.release()
            
            # Now compute delta-cropped frames to optimize USB serial transfer bandwidth
            logger.info(f"Loaded {len(raw_frames)} raw frames. Computing delta compression...")
            self.frames = []
            prev_frame = None
            for i, frame_image in enumerate(raw_frames):
                # Force first frame (and once every 60 frames) to render in full as a keyframe / recovery sync point
                if i == 0 or prev_frame is None or (i % 60 == 0):
                    self.frames.append((frame_image, self.x, self.y, self.frame_delay))
                else:
                    diff = ImageChops.difference(frame_image, prev_frame)
                    bbox = diff.getbbox()
                    if bbox is None:
                        # Frame is identical to previous, send None to skip transmission
                        self.frames.append((None, self.x, self.y, self.frame_delay))
                    else:
                        left, upper, right, lower = bbox
                        cropped = frame_image.crop(bbox)
                        self.frames.append((cropped, self.x + left, self.y + upper, self.frame_delay))
                prev_frame = frame_image
                
            logger.info(f"Successfully cached and delta-compressed {len(raw_frames)} video frames in RAM.")
        else:
            cap.release()

    def start(self):
        """Starts playback in a background thread."""
        if self.is_playing:
            return
        if self.pre_cache and not self.frames:
            logger.warning("Cannot start playback: No frames loaded.")
            return

        self._stop_event.clear()
        self.is_playing = True
        self._thread = threading.Thread(target=self._play_loop, name="LcdVideoPlayerThread")
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"Started playback loop for {self.file_path}")

    def stop(self):
        """Stops the playback loop."""
        if not self.is_playing:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.is_playing = False
        logger.info(f"Stopped playback loop for {self.file_path}")

    def _play_loop(self):
        if self.pre_cache:
            self._play_cached_loop()
        else:
            self._play_streamed_loop()

    def _play_cached_loop(self):
        frame_idx = 0
        num_frames = len(self.frames)

        while not self._stop_event.is_set():
            frame_item = self.frames[frame_idx]
            cropped_image, target_x, target_y, duration = frame_item
            start_time = time.perf_counter()

            if cropped_image is not None:
                # Queue control to protect against lag
                current_qsize = 0
                if self.lcd.update_queue is not None:
                    current_qsize = self.lcd.update_queue.qsize()

                if current_qsize <= self.max_queue_size:
                    try:
                        self.lcd.DisplayPILImage(
                            cropped_image,
                            target_x,
                            target_y,
                            cropped_image.width,
                            cropped_image.height
                        )
                    except Exception as e:
                        logger.error(f"Error rendering frame: {e}")
                else:
                    logger.debug(f"Queue congested (size: {current_qsize}). Dropping frame.")

            elapsed = time.perf_counter() - start_time
            sleep_time = max(0.001, duration - elapsed)

            if self._stop_event.wait(sleep_time):
                break

            frame_idx = (frame_idx + 1) % num_frames

    def _play_streamed_loop(self):
        """Streams video directly from disk frame-by-frame (used when pre_cache=False)."""
        if self.is_gif:
            # Fallback to loading GIF frames if streaming requested for GIF
            self.pre_cache = True
            self._load_gif()
            self._play_cached_loop()
            return

        cap = cv2.VideoCapture(self.file_path)
        
        while not self._stop_event.is_set():
            start_time = time.perf_counter()
            ret, frame = cap.read()
            
            if not ret:
                # Loop video: reset capture position to the beginning
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    logger.error("Could not loop video: Stream failed.")
                    break

            # Convert to PIL Image
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(rgb)
            
            # Resize
            if pil_frame.width != self.width or pil_frame.height != self.height:
                pil_frame = pil_frame.resize((self.width, self.height), Image.Resampling.BILINEAR)

            # Queue control
            current_qsize = 0
            if self.lcd.update_queue is not None:
                current_qsize = self.lcd.update_queue.qsize()

            if current_qsize <= self.max_queue_size:
                try:
                    self.lcd.DisplayPILImage(pil_frame, self.x, self.y, self.width, self.height)
                except Exception as e:
                    logger.error(f"Error rendering streamed frame: {e}")
            else:
                logger.debug(f"Queue congested (size: {current_qsize}). Dropping streamed frame.")

            elapsed = time.perf_counter() - start_time
            sleep_time = max(0.001, self.frame_delay - elapsed)

            if self._stop_event.wait(sleep_time):
                break

        cap.release()
