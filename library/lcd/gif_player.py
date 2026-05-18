# SPDX-License-Identifier: GPL-3.0-or-later
import os
import time
import threading
from typing import List, Tuple
from PIL import Image, ImageSequence

from library.log import logger
import library.config as config

class LcdGifPlayer:
    def __init__(self, lcd_comm, gif_path: str, x: int = 0, y: int = 0, width: int = 0, height: int = 0, max_queue_size: int = 4):
        """
        An optimized GIF player for Turing Smart Screen displays.
        
        Args:
            lcd_comm: The active LcdComm driver instance.
            gif_path: Path to the animated GIF.
            x: Target X position on the screen.
            y: Target Y position on the screen.
            width: Target width (0 to use native GIF width).
            height: Target height (0 to use native GIF height).
            max_queue_size: If the queue size exceeds this limit, we drop frames to avoid lag.
        """
        self.lcd = lcd_comm
        self.gif_path = gif_path
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_queue_size = max_queue_size
        
        self.frames: List[Tuple[Image.Image, float]] = []
        self._stop_event = threading.Event()
        self._thread = None
        self.is_playing = False

    def load(self):
        """Pre-loads, converts, and resizes all frames of the GIF in memory for fluid playback."""
        logger.info(f"Loading animated GIF: {self.gif_path}")
        if not os.path.exists(self.gif_path):
            raise FileNotFoundError(f"GIF file not found: {self.gif_path}")
        
        try:
            gif = Image.open(self.gif_path)
        except Exception as e:
            logger.error(f"Failed to open GIF {self.gif_path}: {e}")
            raise e

        # Target dimensions
        target_w = self.width if self.width > 0 else gif.width
        target_h = self.height if self.height > 0 else gif.height
        self.width = target_w
        self.height = target_h

        self.frames = []
        try:
            for frame in ImageSequence.Iterator(gif):
                # Copy frame and convert to RGB (GIF is usually palette)
                frame_image = frame.copy().convert("RGB")
                
                # Resize if needed
                if frame_image.width != target_w or frame_image.height != target_h:
                    frame_image = frame_image.resize((target_w, target_h), Image.Resampling.BILINEAR)
                
                # Get frame duration in seconds (default to 100ms)
                duration = frame.info.get("duration", 100)
                if duration <= 0:
                    duration = 100
                duration_sec = duration / 1000.0
                
                self.frames.append((frame_image, duration_sec))
        except Exception as e:
            logger.error(f"Error during GIF frame extraction: {e}")
            raise e

        logger.info(f"Successfully loaded {len(self.frames)} frames from {self.gif_path} (Target size: {target_w}x{target_h})")

    def start(self):
        """Starts the playback loop in a background thread."""
        if self.is_playing:
            return
        if not self.frames:
            logger.warning("Cannot start playback: No frames loaded.")
            return

        self._stop_event.clear()
        self.is_playing = True
        self._thread = threading.Thread(target=self._play_loop, name="LcdGifPlayerThread")
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"Started GIF playback thread for {self.gif_path}")

    def stop(self):
        """Stops the playback loop."""
        if not self.is_playing:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.is_playing = False
        logger.info(f"Stopped GIF playback thread for {self.gif_path}")

    def _play_loop(self):
        frame_idx = 0
        num_frames = len(self.frames)

        while not self._stop_event.is_set():
            frame_image, duration = self.frames[frame_idx]
            start_time = time.perf_counter()

            # Dynamic Queue Control to prevent lagging the system monitor
            current_qsize = 0
            if self.lcd.update_queue is not None:
                current_qsize = self.lcd.update_queue.qsize()

            if current_qsize <= self.max_queue_size:
                try:
                    # Send to the display. DisplayPILImage is thread-safe thanks to self.lcd.update_queue_mutex
                    self.lcd.DisplayPILImage(frame_image, self.x, self.y, self.width, self.height)
                except Exception as e:
                    logger.error(f"Error rendering GIF frame to display: {e}")
            else:
                # Drop frame if display queue is congested to keep system stats responsive
                logger.debug(f"Display queue congested (size: {current_qsize}). Dropping GIF frame.")

            # Calculate precise sleep time
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0.001, duration - elapsed)

            if self._stop_event.wait(sleep_time):
                break

            frame_idx = (frame_idx + 1) % num_frames
