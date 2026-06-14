import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import shutil


class FFmpegGUI:
    """Professional FFmpeg Converter with Advanced Options"""

    QUALITY_PRESETS = {
        "Fast": {"video_crf": 28, "audio_bitrate": "128k"},
        "Balanced": {"video_crf": 23, "audio_bitrate": "192k"},
        "High Quality": {"video_crf": 18, "audio_bitrate": "320k"},
    }

    VIDEO_CODECS = {
        "H.264": "libx264",
        "H.265": "libx265",
        "VP9": "libvpx-vp9",
        "AV1": "libaom-av1",
    }

    AUDIO_CODECS = {
        "AAC": "aac",
        "MP3": "libmp3lame",
        "Opus": "libopus",
        "Vorbis": "libvorbis",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Converter Pro")
        self.root.geometry("1000x750")
        self.root.minsize(900, 600)
        
        # Configure style
        self.setup_styles()

        self.files = []
        self.is_converting = False
        self.output_dir = os.path.join(os.getcwd(), "converted")

        self.build_ui()
        self.check_ffmpeg()

    def setup_styles(self):
        """Configure ttk styles for better appearance"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Header.TFrame', relief='sunken', borderwidth=2)
        style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'))

    def build_ui(self):
        """Build the main UI layout"""
        # Main container with notebook for organized tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Files tab
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="📁 Files", sticky="nsew")
        self.build_files_tab(files_frame)

        # Settings tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings", sticky="nsew")
        self.build_settings_tab(settings_frame)

        # Log tab
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="📋 Log", sticky="nsew")
        self.build_log_tab(log_frame)

    def build_files_tab(self, parent):
        """Build the files management tab"""
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            title_frame,
            text="File Management",
            style='Title.TLabel'
        ).pack(side="left")

        # Buttons frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="➕ Add Files",
            command=self.add_files,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="🗑️ Remove Selected",
            command=self.remove_file,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="🗑️ Clear All",
            command=self.clear_all,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="📂 Output Folder",
            command=self.select_output_dir,
            width=15
        ).pack(side="left", padx=5)

        # Output directory label
        self.output_label = ttk.Label(
            parent,
            text=f"Output: {self.output_dir}",
            foreground="blue"
        )
        self.output_label.pack(fill="x", padx=10, pady=5)

        # File list with scrollbar
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.file_list = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Helvetica', 10),
            height=10
        )
        self.file_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.file_list.yview)

        # File count
        self.file_count_label = ttk.Label(parent, text="Files: 0")
        self.file_count_label.pack(fill="x", padx=10, pady=5)

        # Convert button
        ttk.Button(
            parent,
            text="▶️ START CONVERSION",
            command=self.start_conversion,
            width=30
        ).pack(pady=15)

    def build_settings_tab(self, parent):
        """Build the settings configuration tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # Quality Preset
        self.create_labeled_frame(
            scrollable_frame, "Quality Preset", "preset"
        )
        self.preset_var = tk.StringVar(value="Balanced")
        for preset in self.QUALITY_PRESETS.keys():
            ttk.Radiobutton(
                self.preset_frame,
                text=preset,
                variable=self.preset_var,
                value=preset
            ).pack(anchor="w", padx=20)

        # Output Format
        self.create_labeled_frame(
            scrollable_frame, "Output Format", "format"
        )
        self.format_var = tk.StringVar(value="mp4")
        formats = ["mp4", "mkv", "mov", "avi", "webm", "mp3", "wav", "flac", "ogg"]
        
        format_combo = ttk.Combobox(
            self.format_frame,
            textvariable=self.format_var,
            values=formats,
            state="readonly",
            width=20
        )
        format_combo.pack(padx=20, pady=5)

        # Video Codec
        self.create_labeled_frame(
            scrollable_frame, "Video Codec", "vcodec"
        )
        self.video_codec_var = tk.StringVar(value="H.264")
        video_codec_combo = ttk.Combobox(
            self.vcodec_frame,
            textvariable=self.video_codec_var,
            values=list(self.VIDEO_CODECS.keys()),
            state="readonly",
            width=20
        )
        video_codec_combo.pack(padx=20, pady=5)

        # Audio Codec
        self.create_labeled_frame(
            scrollable_frame, "Audio Codec", "acodec"
        )
        self.audio_codec_var = tk.StringVar(value="AAC")
        audio_codec_combo = ttk.Combobox(
            self.acodec_frame,
            textvariable=self.audio_codec_var,
            values=list(self.AUDIO_CODECS.keys()),
            state="readonly",
            width=20
        )
        audio_codec_combo.pack(padx=20, pady=5)

        # Resolution
        self.create_labeled_frame(
            scrollable_frame, "Resolution (leave blank for original)", "resolution"
        )
        self.resolution_var = tk.StringVar(value="")
        resolutions = ["", "1920x1080", "1280x720", "854x480", "640x360"]
        resolution_combo = ttk.Combobox(
            self.resolution_frame,
            textvariable=self.resolution_var,
            values=resolutions,
            width=20
        )
        resolution_combo.pack(padx=20, pady=5)

        # Frame rate
        self.create_labeled_frame(
            scrollable_frame, "Frame Rate (leave blank for original)", "fps"
        )
        self.fps_var = tk.StringVar(value="")
        fps_combo = ttk.Combobox(
            self.fps_frame,
            textvariable=self.fps_var,
            values=["", "24", "25", "30", "60"],
            width=20
        )
        fps_combo.pack(padx=20, pady=5)

        # CRF Value (Quality)
        self.create_labeled_frame(
            scrollable_frame, "Quality (CRF: 0-51, lower=better)", "crf"
        )
        self.crf_var = tk.StringVar(value="23")
        crf_spin = ttk.Spinbox(
            self.crf_frame,
            from_=0,
            to=51,
            textvariable=self.crf_var,
            width=10
        )
        crf_spin.pack(padx=20, pady=5, anchor="w")

        # Audio bitrate
        self.create_labeled_frame(
            scrollable_frame, "Audio Bitrate", "abitrate"
        )
        self.audio_bitrate_var = tk.StringVar(value="192k")
        abitrate_combo = ttk.Combobox(
            self.abitrate_frame,
            textvariable=self.audio_bitrate_var,
            values=["128k", "192k", "256k", "320k"],
            width=20
        )
        abitrate_combo.pack(padx=20, pady=5)

        # Keep original audio
        self.keep_audio_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            scrollable_frame,
            text="Keep original audio quality (ignore audio bitrate setting)",
            variable=self.keep_audio_var
        ).pack(anchor="w", padx=20, pady=10)

    def create_labeled_frame(self, parent, label_text, frame_name):
        """Helper to create a labeled frame"""
        frame = ttk.LabelFrame(parent, text=label_text, padding=10)
        frame.pack(fill="x", padx=20, pady=10)
        setattr(self, f"{frame_name}_frame", frame)

    def build_log_tab(self, parent):
        """Build the logging/status tab"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            title_frame,
            text="Conversion Log",
            style='Title.TLabel'
        ).pack(side="left")

        ttk.Button(
            title_frame,
            text="🗑️ Clear Log",
            command=self.clear_log
        ).pack(side="right", padx=5)

        # Log text area
        self.log = scrolledtext.ScrolledText(
            parent,
            height=20,
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(
            parent,
            mode='indeterminate'
        )
        self.progress.pack(fill="x", padx=10, pady=5)

        # Status label
        self.status_label = ttk.Label(parent, text="Ready", foreground="green")
        self.status_label.pack(fill="x", padx=10, pady=5)

    def check_ffmpeg(self):
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
                check=True
            )
            self.write_log("✓ FFmpeg detected successfully")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"FFmpeg not found! Please install FFmpeg.\nError: {str(e)}"
            )
            self.write_log("✗ FFmpeg not found!")

    def add_files(self):
        """Add files to the conversion list"""
        files = filedialog.askopenfilenames()
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_list.insert(tk.END, os.path.basename(file))
        self.update_file_count()

    def remove_file(self):
        """Remove selected file from the list"""
        selection = self.file_list.curselection()
        if selection:
            index = selection[0]
            self.file_list.delete(index)
            del self.files[index]
            self.update_file_count()

    def clear_all(self):
        """Clear all files from the list"""
        if messagebox.askyesno("Confirm", "Clear all files?"):
            self.file_list.delete(0, tk.END)
            self.files = []
            self.update_file_count()

    def select_output_dir(self):
        """Select output directory"""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.output_label.config(text=f"Output: {self.output_dir}")

    def update_file_count(self):
        """Update file count label"""
        count = len(self.files)
        self.file_count_label.config(text=f"Files: {count}")

    def write_log(self, text):
        """Write text to the log"""
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        if not self.files:
            messagebox.showwarning("Warning", "No files selected!")
            return

        if self.is_converting:
            messagebox.showinfo("Info", "Conversion already in progress!")
            return

        self.is_converting = True
        self.progress.start()
        self.status_label.config(text="Converting...", foreground="orange")
        
        threading.Thread(target=self.convert_files, daemon=True).start()

    def convert_files(self):
        """Convert all selected files"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)

            fmt = self.format_var.get()
            preset = self.preset_var.get()
            video_codec = self.VIDEO_CODECS.get(self.video_codec_var.get(), "libx264")
            audio_codec = self.AUDIO_CODECS.get(self.audio_codec_var.get(), "aac")

            for i, file in enumerate(self.files):
                if not self.is_converting:
                    break

                filename = os.path.basename(file)
                name = os.path.splitext(filename)[0]
                output = os.path.join(self.output_dir, f"{name}.{fmt}")

                self.write_log(f"\n[{i+1}/{len(self.files)}] Converting: {filename}")

                cmd = self.build_ffmpeg_command(
                    file, output, fmt, preset, video_codec, audio_codec
                )

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )

                for line in process.stdout:
                    self.write_log(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.write_log(f"✓ Success: {filename}")
                else:
                    self.write_log(f"✗ Failed: {filename}")

            self.write_log("\n" + "="*50)
            self.write_log("ALL CONVERSIONS COMPLETE")
            self.write_log("="*50)
            self.status_label.config(text="Complete!", foreground="green")

            if os.name == "nt":
                os.startfile(self.output_dir)

        except Exception as e:
            self.write_log(f"Error: {str(e)}")
            self.status_label.config(text="Error!", foreground="red")
        finally:
            self.is_converting = False
            self.progress.stop()

    def build_ffmpeg_command(self, input_file, output_file, fmt, preset, video_codec, audio_codec):
        """Build FFmpeg command with selected options"""
        cmd = ["ffmpeg", "-y", "-i", input_file]

        # Video codec
        cmd.extend(["-c:v", video_codec])

        # Resolution
        if self.resolution_var.get():
            cmd.extend(["-vf", f"scale={self.resolution_var.get()}"])

        # Frame rate
        if self.fps_var.get():
            cmd.extend(["-r", self.fps_var.get()])

        # CRF (quality)
        cmd.extend(["-crf", self.crf_var.get()])

        # Audio codec
        cmd.extend(["-c:a", audio_codec])

        # Audio bitrate
        if not self.keep_audio_var.get():
            cmd.extend(["-b:a", self.audio_bitrate_var.get()])

        cmd.append(output_file)
        return cmd

    def clear_log(self):
        """Clear the log"""
        self.log.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegGUI(root)
    root.mainloop()