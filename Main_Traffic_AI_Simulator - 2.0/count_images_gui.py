# License: MIT
# requirements:
#   opencv-python
#   ultralytics
#   pyyaml
#   numpy
#   tkinter
#   Pillow

"""
A self-contained application that first prompts the user to select a webcam,
then processes a set of four images (from file or capture) and generates a
JSON output with vehicle counts categorized by direction, using a simple GUI.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any
import yaml
import cv2
import json
from collections import defaultdict

# Pillow is required for displaying video frames in Tkinter
try:
    from PIL import Image, ImageTk
except ImportError:
    print("Error: The 'Pillow' library is required. Please install it using: pip install Pillow")
    sys.exit(1)

# This assumes your detector file is in a 'src' subfolder.
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from detector_ultralytics import VehicleDetectorUltralytics as VehicleDetector
except ImportError:
    logging.error("Failed to import 'detector_ultralytics'. Make sure it's in a 'src' folder or in the same directory.")
    # We don't exit here, as the user might only use the camera selection part
    VehicleDetector = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Core Image Processing Logic ---
class ImageProcessor:
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

    def __init__(self, config_file: str):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")
            
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        detector_config = config.get('detector', {})
        self.model_path = detector_config.get('model_name', 'yolov8n.pt')
        self.conf_threshold = detector_config.get('conf_threshold', 0.3)
        self.class_mapping = config.get('class_mapping', {})
        self.model = self._load_model()
        
    def _load_model(self):
        try:
            from ultralytics import YOLO
            return YOLO(self.model_path)
        except ImportError:
            raise RuntimeError("Ultralytics not installed. Cannot load model.")
        except Exception as e:
            raise RuntimeError(f"Error loading YOLO model: {e}")

    def process_image(self, image_path: str) -> Dict[str, int]:
        """Processes a single image and returns vehicle counts."""
        if not self.model:
            raise RuntimeError("YOLO model failed to load. Cannot process image.")
            
        logging.info(f"Processing image: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        results = self.model(image, conf=self.conf_threshold, verbose=False)
        
        vehicle_counts = defaultdict(int)
        if hasattr(self.model, 'names'):
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        original_class = self.model.names.get(cls_id, 'unknown')
                        mapped_class = self.class_mapping.get(original_class)
                        if mapped_class:
                            vehicle_counts[mapped_class] += 1
        
        return dict(vehicle_counts)


# --- Main GUI Application Class ---
class App:
    def __init__(self, master, webcam_index: int):
        self.master = master
        self.webcam_index = webcam_index # Use the index selected at startup
        self.webcam_available = (self.webcam_index is not None)

        master.title("Directional Vehicle Counter")
        master.geometry("800x550")

        self.directions = ["right", "down", "left", "up"]
        self.image_paths = {d: "" for d in self.directions}

        # Use paths relative to this script's directory (robust to IDE/shortcut launch CWD).
        self.base_dir = Path(__file__).resolve().parent
        self.config_file = str(self.base_dir / "configs" / "config.yaml")

        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        self.processor: ImageProcessor = None
        self.process_button = None
        self.output_label = None

        self._create_widgets()

    def _create_widgets(self):
        control_frame = tk.Frame(self.master, padx=10, pady=10)
        control_frame.pack(fill=tk.X)

        tk.Label(control_frame, text="Select or Capture Images for Each Direction:").pack(pady=(0, 10))
        if not self.webcam_available:
            tk.Label(control_frame, text="No webcam detected. Capture feature is disabled.", fg="red").pack()

        self.path_entries = {}
        for i, direction in enumerate(self.directions):
            frame = tk.Frame(control_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{direction.capitalize()}:", width=10, anchor='e').pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=50, state='readonly')
            entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
            
            tk.Button(frame, text="Browse", command=lambda d=direction: self._select_image(d)).pack(side=tk.LEFT, padx=(0, 5))
            
            capture_btn = tk.Button(frame, text="Capture", command=lambda d=direction: self._capture_image(d))
            if not self.webcam_available:
                capture_btn.config(state=tk.DISABLED)
            capture_btn.pack(side=tk.LEFT)
            
            self.path_entries[direction] = entry

        self.process_button = tk.Button(control_frame, text="Process Images", command=self._run_in_thread, font=("Helvetica", 12, "bold"), bg="green", fg="white")
        self.process_button.pack(pady=20)

        self.output_label = tk.Label(self.master, text="Final JSON Output", font=("Helvetica", 10, "bold"))
        self.output_label.pack(pady=(10, 0))
        self.output_text = tk.Text(self.master, height=10, wrap=tk.WORD, bg="#f0f0f0")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.output_text.config(state=tk.DISABLED)

    def _select_image(self, direction: str):
        file_path = filedialog.askopenfilename(title=f"Select image for '{direction}'", filetypes=[("Image files", list(ImageProcessor.IMAGE_EXTENSIONS))])
        if file_path:
            self._update_path_entry(direction, file_path)

    def _update_path_entry(self, direction: str, file_path: str):
        self.image_paths[direction] = file_path
        entry = self.path_entries[direction]
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        entry.config(state='readonly')

    def _capture_image(self, direction: str):
        capture_window = tk.Toplevel(self.master)
        capture_window.title(f"Capture for {direction.capitalize()}")
        
        video_label = tk.Label(capture_window)
        video_label.pack()

        cap = cv2.VideoCapture(self.webcam_index, cv2.CAP_DSHOW)
        
        last_frame_ref = {'frame': None}

        def update_feed():
            ret, frame = cap.read()
            if ret:
                last_frame_ref['frame'] = frame.copy()
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)
            if capture_window.winfo_exists():
                video_label.after(15, update_feed)
            else:
                cap.release()

        def snap_and_save():
            if last_frame_ref['frame'] is not None:
                filename = f"capture_{direction}_{int(time.time())}.png"
                save_path = self.output_dir / filename
                cv2.imwrite(str(save_path), last_frame_ref['frame'])
                logging.info(f"Image saved to {save_path}")
                self._update_path_entry(direction, str(save_path))
                on_close()

        def on_close():
            if 'after_id' in locals() or 'after_id' in globals():
                 video_label.after_cancel(after_id)
            cap.release()
            capture_window.destroy()
        
        snap_button = tk.Button(capture_window, text="Snap & Save", command=snap_and_save, font=("Helvetica", 10, "bold"))
        snap_button.pack(pady=10)

        capture_window.protocol("WM_DELETE_WINDOW", on_close)
        after_id = video_label.after(15, update_feed)

    def _run_in_thread(self):
        for direction in self.directions:
            if not self.image_paths[direction]:
                messagebox.showerror("Missing Input", f"Please select or capture an image for the '{direction}' direction.")
                return

        self.process_button.config(state=tk.DISABLED, text="Processing...")
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
        self.master.update_idletasks()

        thread = threading.Thread(target=self._process_images)
        thread.daemon = True
        thread.start()

    def _process_images(self):
        try:
            if VehicleDetector is None:
                raise ImportError("VehicleDetector could not be imported. Cannot process images.")
            if not self.processor:
                self.processor = ImageProcessor(self.config_file)
            
            final_counts = {}
            for direction in self.directions:
                image_path = self.image_paths[direction]
                counts = self.processor.process_image(image_path)
                final_counts[direction] = counts
            
            self._display_output(final_counts)

            output_file = self.output_dir / "directional_counts.json"
            with open(output_file, 'w') as f:
                json.dump(final_counts, f, indent=2)

            messagebox.showinfo("Success", f"Processing complete. Counts saved to:\n{output_file}")

        except Exception as e:
            logging.error(f"An error occurred during processing: {e}")
            messagebox.showerror("Processing Error", f"An error occurred: {e}")
        finally:
            self.master.after(100, lambda: self.process_button.config(state=tk.NORMAL, text="Process Images"))

    def _display_output(self, data: Dict[str, Any]):
        json_str = json.dumps(data, indent=2)
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, json_str)
        self.output_text.config(state='disabled')

# --- Camera Selection Dialog ---
def select_camera_dialog(root):
    dialog = tk.Toplevel(root)
    dialog.title("Select Camera")
    dialog.geometry("680x560")
    dialog.grab_set() # Modal window

    video_label = tk.Label(dialog)
    video_label.pack(pady=10)

    status_label = tk.Label(dialog, text="Searching for cameras...", font=("Helvetica", 10))
    status_label.pack()

    # Store state in a mutable object (dictionary)
    state = {'cap': None, 'current_index': -1, 'selected_index': None, 'after_id': None}

    def update_feed():
        if state['cap'] and state['cap'].isOpened():
            ret, frame = state['cap'].read()
            if ret:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)
        state['after_id'] = video_label.after(15, update_feed)

    def try_next_camera():
        if state['cap']:
            state['cap'].release()
        
        state['current_index'] += 1
        cap = cv2.VideoCapture(state['current_index'], cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            status_label.config(text=f"No more cameras found. Please select one or close.")
            next_button.config(state=tk.DISABLED)
        else:
            state['cap'] = cap
            status_label.config(text=f"Showing Camera Index: {state['current_index']}")
            select_button.config(state=tk.NORMAL)

    def on_select():
        state['selected_index'] = state['current_index']
        on_close()

    def on_close():
        if state['after_id']:
            video_label.after_cancel(state['after_id'])
        if state['cap']:
            state['cap'].release()
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)
    next_button = tk.Button(button_frame, text="Next Camera", command=try_next_camera)
    next_button.pack(side=tk.LEFT, padx=10)
    select_button = tk.Button(button_frame, text="Select this Camera", command=on_select, state=tk.DISABLED)
    select_button.pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    try_next_camera() # Try the first camera
    update_feed()

    root.wait_window(dialog)
    return state['selected_index']


def main():
    root = tk.Tk()
    root.withdraw() # Hide the main window until camera is selected

    selected_index = select_camera_dialog(root)

    if selected_index is not None:
        logging.info(f"Starting application with selected camera index: {selected_index}")
        root.deiconify() # Show the main window
        app = App(root, webcam_index=selected_index)
        root.mainloop()
    else:
        logging.warning("No camera was selected. Exiting application.")
        root.destroy()


if __name__ == '__main__':
    main()