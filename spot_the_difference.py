"""
Sydney Group 16
1. Mejbah Md Fahim - S400658 
2. Md Showkotul Islam - S399845
3. Sharika Alam - S401269
4. Jannatul Naima -S400577
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import random
import math


# ─────────────────────────────────────────────
#  Class 1 – Difference (data model)
# ─────────────────────────────────────────────
class Difference:
    """Represents a single hidden difference region on the modified image."""

    def __init__(self, x, y, w, h, diff_type):
        self.x = x          # top-left column
        self.y = y          # top-left row
        self.w = w          # width  of the region
        self.h = h          # height of the region
        self.diff_type = diff_type
        self.found = False

    def centre(self):
        """Return the (cx, cy) pixel centre of this region."""
        return (self.x + self.w // 2, self.y + self.h // 2)

    def contains_point(self, px, py, tolerance=30):
        """
        Return True if (px, py) falls inside the region (with a small
        tolerance border so clicks near the edge still register).
        """
        return (
            self.x - tolerance <= px <= self.x + self.w + tolerance
            and self.y - tolerance <= py <= self.y + self.h + tolerance
        )

    def overlaps(self, other, margin=10):
        """Check whether this region overlaps with another (plus a safety margin)."""
        return not (
            self.x + self.w + margin < other.x
            or other.x + other.w + margin < self.x
            or self.y + self.h + margin < other.y
            or other.y + other.h + margin < self.y
        )


# ─────────────────────────────────────────────
#  Class 2 – ImageProcessor (OpenCV logic)
# ─────────────────────────────────────────────
class ImageProcessor:
    """
    Loads an image and creates a modified copy with exactly 5 hidden
    differences injected at random, non-overlapping locations.

    Supported alteration types
    --------------------------
    colour_shift   – shifts hue/saturation in a rectangular patch
    blur           – applies a Gaussian blur to a patch
    brightness     – increases or decreases brightness of a patch
    noise          – overlays random salt-and-pepper noise on a patch
    swap_channels  – swaps the R and B colour channels in a patch
    """

    NUM_DIFFERENCES = 5
    REGION_W = 60   # width  of every difference patch
    REGION_H = 60   # height of every difference patch

    ALTERATION_TYPES = [
        "colour_shift",
        "blur",
        "brightness",
        "noise",
        "swap_channels",
    ]

    def __init__(self):
        self.original_bgr = None   # original image in BGR (OpenCV native)
        self.modified_bgr = None   # altered clone
        self.differences = []      # list[Difference]

    # ── public interface ──────────────────────

    def load_image(self, filepath):
        """Load image from disk and generate the modified version."""
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError(f"Cannot read image: {filepath}")
        self.original_bgr = img.copy()
        self.modified_bgr, self.differences = self._make_modified(img)

    def get_original_rgb(self):
        return cv2.cvtColor(self.original_bgr, cv2.COLOR_BGR2RGB)

    def get_modified_rgb(self):
        return cv2.cvtColor(self.modified_bgr, cv2.COLOR_BGR2RGB)

    # ── private helpers ───────────────────────

    def _make_modified(self, source):
        """Return (modified_bgr, list[Difference])."""
        clone = source.copy()
        h, w = clone.shape[:2]
        placed = []

        # We need exactly 5 non-overlapping patches
        attempts = 0
        while len(placed) < self.NUM_DIFFERENCES and attempts < 1000:
            attempts += 1

            # Pick a random top-left that keeps the patch fully inside the image
            rx = random.randint(0, max(0, w - self.REGION_W - 1))
            ry = random.randint(0, max(0, h - self.REGION_H - 1))

            diff_type = random.choice(self.ALTERATION_TYPES)
            candidate = Difference(rx, ry, self.REGION_W, self.REGION_H, diff_type)

            # Reject if it overlaps with any already-placed patch
            if any(candidate.overlaps(p) for p in placed):
                continue

            self._apply_alteration(clone, candidate)
            placed.append(candidate)

        return clone, placed

    def _apply_alteration(self, img, diff):
        """Mutate a rectangular patch of `img` according to diff.diff_type."""
        x, y, w, h = diff.x, diff.y, diff.w, diff.h
        patch = img[y:y + h, x:x + w]

        if diff.diff_type == "colour_shift":
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).astype(np.int32)
            hsv[:, :, 0] = (hsv[:, :, 0] + random.randint(20, 60)) % 180
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] + random.randint(30, 80), 0, 255)
            img[y:y + h, x:x + w] = cv2.cvtColor(
                hsv.astype(np.uint8), cv2.COLOR_HSV2BGR
            )

        elif diff.diff_type == "blur":
            ksize = random.choice([11, 15, 19])
            img[y:y + h, x:x + w] = cv2.GaussianBlur(patch, (ksize, ksize), 0)

        elif diff.diff_type == "brightness":
            delta = random.choice([-60, -50, 50, 60])
            bright = np.clip(patch.astype(np.int32) + delta, 0, 255).astype(np.uint8)
            img[y:y + h, x:x + w] = bright

        elif diff.diff_type == "noise":
            noisy = patch.copy()
            num_pixels = int(0.15 * w * h)
            for _ in range(num_pixels):
                ny = random.randint(0, h - 1)
                nx = random.randint(0, w - 1)
                noisy[ny, nx] = [0, 0, 0] if random.random() < 0.5 else [255, 255, 255]
            img[y:y + h, x:x + w] = noisy

        elif diff.diff_type == "swap_channels":
            swapped = patch.copy()
            swapped[:, :, 0], swapped[:, :, 2] = patch[:, :, 2].copy(), patch[:, :, 0].copy()
            img[y:y + h, x:x + w] = swapped


# ─────────────────────────────────────────────
#  Class 3 – GameState (score / mistake logic)
# ─────────────────────────────────────────────
class GameState:
    """Tracks mistakes, found differences, and cumulative score."""

    MAX_MISTAKES = 3

    def __init__(self):
        self.mistakes = 0
        self.total_found = 0   # cumulative across all images
        self.game_over = False # True once mistakes == MAX_MISTAKES or all found

    def reset_for_new_image(self):
        self.mistakes = 0
        self.game_over = False

    def register_mistake(self):
        self.mistakes += 1
        if self.mistakes >= self.MAX_MISTAKES:
            self.game_over = True

    def register_find(self):
        self.total_found += 1

    def is_locked_out(self):
        return self.mistakes >= self.MAX_MISTAKES

    @property
    def remaining(self):
        """How many differences are yet to be found in the current image."""
        return None  # caller must compute from the difference list


# ─────────────────────────────────────────────
#  Class 4 – SpotTheDifferenceApp (Tkinter GUI)
# ─────────────────────────────────────────────
class SpotTheDifferenceApp(tk.Tk):
    """
    Main application window.

    Layout
    ------
    Top bar   : Load Image | Reveal | status labels
    Image area: original (left, read-only) | modified (right, clickable)
    Bottom bar: mistake counter + score
    """

    DISPLAY_SIZE = 500   # images are scaled to fit inside a square of this size

    def __init__(self):
        super().__init__()
        self.title("Spot the Difference")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        self.processor = ImageProcessor()
        self.state = GameState()

        # Tkinter PhotoImage references (must be kept alive)
        self._orig_photo = None
        self._mod_photo  = None

        # Scale factors used when converting click coords → image coords
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0

        self._build_ui()

    # ── UI construction ───────────────────────

    def _build_ui(self):
        BG   = "#1e1e2e"
        CARD = "#2a2a3e"
        ACC  = "#89b4fa"
        TXT  = "#cdd6f4"

        # ── top toolbar ──
        toolbar = tk.Frame(self, bg=BG, pady=8)
        toolbar.pack(fill=tk.X, padx=12)

        btn_style = dict(
            bg=ACC, fg="#1e1e2e", font=("Consolas", 11, "bold"),
            relief=tk.FLAT, padx=14, pady=6, cursor="hand2"
        )
        tk.Button(toolbar, text="📂  Load Image", command=self._load_image, **btn_style).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="👁  Reveal All",  command=self._reveal_all, **btn_style).pack(side=tk.LEFT, padx=4)

        self._status_var = tk.StringVar(value="Load an image to start playing.")
        tk.Label(toolbar, textvariable=self._status_var, bg=BG, fg=TXT,
                 font=("Consolas", 10)).pack(side=tk.LEFT, padx=16)

        # ── image canvases ──
        canvas_frame = tk.Frame(self, bg=BG)
        canvas_frame.pack(padx=12, pady=4)

        lbl_orig = tk.Label(canvas_frame, text="Original", bg=BG, fg=ACC,
                            font=("Consolas", 10, "bold"))
        lbl_orig.grid(row=0, column=0, pady=(0, 4))

        lbl_mod = tk.Label(canvas_frame, text="Modified  ← click here", bg=BG, fg=ACC,
                           font=("Consolas", 10, "bold"))
        lbl_mod.grid(row=0, column=1, pady=(0, 4))

        self.canvas_orig = tk.Canvas(
            canvas_frame, width=self.DISPLAY_SIZE, height=self.DISPLAY_SIZE,
            bg=CARD, highlightthickness=2, highlightbackground=CARD
        )
        self.canvas_orig.grid(row=1, column=0, padx=(0, 8))

        self.canvas_mod = tk.Canvas(
            canvas_frame, width=self.DISPLAY_SIZE, height=self.DISPLAY_SIZE,
            bg=CARD, highlightthickness=2, highlightbackground="#f38ba8"
        )
        self.canvas_mod.grid(row=1, column=1)
        self.canvas_mod.bind("<Button-1>", self._on_canvas_click)

        # ── bottom status bar ──
        bottom = tk.Frame(self, bg=BG, pady=8)
        bottom.pack(fill=tk.X, padx=12)

        self._mistake_var = tk.StringVar(value="Mistakes: 0 / 3")
        self._score_var   = tk.StringVar(value="Total Found: 0")
        self._remain_var  = tk.StringVar(value="Remaining: –")

        lbl_kw = dict(bg=BG, fg=TXT, font=("Consolas", 11))
        tk.Label(bottom, textvariable=self._mistake_var, **lbl_kw).pack(side=tk.LEFT, padx=12)
        tk.Label(bottom, textvariable=self._remain_var,  **lbl_kw).pack(side=tk.LEFT, padx=12)
        tk.Label(bottom, textvariable=self._score_var,   **lbl_kw).pack(side=tk.RIGHT, padx=12)

    # ── event handlers ────────────────────────

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            self.processor.load_image(path)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.state.reset_for_new_image()
        self._refresh_canvases()
        self._refresh_labels()
        self._status_var.set("Image loaded – click on the Modified image to find differences!")

    def _on_canvas_click(self, event):
        if not self.processor.differences:
            return
        if self.state.is_locked_out():
            return

        # Convert canvas click → original image coordinates
        img_x = int((event.x - self._offset_x) / self._scale)
        img_y = int((event.y - self._offset_y) / self._scale)

        hit = None
        for diff in self.processor.differences:
            if not diff.found and diff.contains_point(img_x, img_y):
                hit = diff
                break

        if hit:
            hit.found = True
            self.state.register_find()
            self._draw_circle_on_both(hit, color="red")
            self._refresh_labels()

            remaining = sum(1 for d in self.processor.differences if not d.found)
            if remaining == 0:
                self._status_var.set("🎉 All differences found!")
                messagebox.showinfo(
                    "Well done!",
                    f"You found all 5 differences!\n"
                    f"Mistakes this round: {self.state.mistakes}\n"
                    f"Total found overall: {self.state.total_found}\n\n"
                    "Load another image to keep playing."
                )
        else:
            self.state.register_mistake()
            self._refresh_labels()
            if self.state.is_locked_out():
                self._status_var.set("❌ Too many mistakes – round over.")
                found_count = sum(1 for d in self.processor.differences if d.found)
                messagebox.showwarning(
                    "Too many mistakes",
                    f"You reached 3 mistakes.\n"
                    f"Differences found this round: {found_count} / 5\n\n"
                    "Load a new image to restart."
                )
            else:
                self._status_var.set(f"Wrong click! Mistakes: {self.state.mistakes} / 3")

    def _reveal_all(self):
        if not self.processor.differences:
            return
        for diff in self.processor.differences:
            if not diff.found:
                diff.found = True   # mark as "found" so circles appear
                self._draw_circle_on_both(diff, color="blue")
        self._refresh_labels()
        self._status_var.set("All differences revealed. Load a new image to play again.")

    # ── drawing helpers ───────────────────────

    def _refresh_canvases(self):
        """Render both images onto their canvases and compute scale / offset."""
        orig_rgb = self.processor.get_original_rgb()
        mod_rgb  = self.processor.get_modified_rgb()

        ih, iw = orig_rgb.shape[:2]
        self._scale, self._offset_x, self._offset_y = self._fit_scale(iw, ih)

        new_w = int(iw * self._scale)
        new_h = int(ih * self._scale)

        orig_resized = cv2.resize(orig_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        mod_resized  = cv2.resize(mod_rgb,  (new_w, new_h), interpolation=cv2.INTER_AREA)

        self._orig_photo = ImageTk.PhotoImage(Image.fromarray(orig_resized))
        self._mod_photo  = ImageTk.PhotoImage(Image.fromarray(mod_resized))

        self.canvas_orig.delete("all")
        self.canvas_mod.delete("all")

        self.canvas_orig.create_image(self._offset_x, self._offset_y,
                                      anchor=tk.NW, image=self._orig_photo)
        self.canvas_mod.create_image(self._offset_x, self._offset_y,
                                     anchor=tk.NW, image=self._mod_photo)

        # Re-draw any circles for already-found differences
        for diff in self.processor.differences:
            if diff.found:
                self._draw_circle_on_both(diff, color="red")

    def _fit_scale(self, iw, ih):
        """Compute scale and (offset_x, offset_y) to fit image into DISPLAY_SIZE×DISPLAY_SIZE."""
        scale = min(self.DISPLAY_SIZE / iw, self.DISPLAY_SIZE / ih, 1.0)
        new_w = int(iw * scale)
        new_h = int(ih * scale)
        ox = (self.DISPLAY_SIZE - new_w) // 2
        oy = (self.DISPLAY_SIZE - new_h) // 2
        return scale, ox, oy

    def _draw_circle_on_both(self, diff, color):
        """Draw a circle around `diff` on both canvases in display-space coordinates."""
        cx_img, cy_img = diff.centre()
        # Map image coords → canvas coords
        cx = int(cx_img * self._scale) + self._offset_x
        cy = int(cy_img * self._scale) + self._offset_y
        r  = int(max(diff.w, diff.h) * self._scale / 2) + 8

        circle_kw = dict(outline=color, width=3)
        self.canvas_orig.create_oval(cx - r, cy - r, cx + r, cy + r, **circle_kw)
        self.canvas_mod.create_oval( cx - r, cy - r, cx + r, cy + r, **circle_kw)

    def _refresh_labels(self):
        remaining = sum(1 for d in self.processor.differences if not d.found)
        self._mistake_var.set(f"Mistakes: {self.state.mistakes} / {GameState.MAX_MISTAKES}")
        self._remain_var.set(f"Remaining: {remaining}")
        self._score_var.set(f"Total Found: {self.state.total_found}")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = SpotTheDifferenceApp()
    app.mainloop()
