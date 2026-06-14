import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os


class FFmpegGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Converter")
        self.root.geometry("700x500")

        self.files = []

        self.build_ui()

    def build_ui(self):

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            top_frame,
            text="Add Files",
            command=self.add_files
        ).pack(side="left")

        ttk.Button(
            top_frame,
            text="Remove Selected"
        ).pack(side="left", padx=5)

        ttk.Label(
            top_frame,
            text="Output Format:"
        ).pack(side="left", padx=(20, 5))

        self.format_var = tk.StringVar(value="mp4")

        formats = [
            "mp4",
            "mkv",
            "mov",
            "avi",
            "webm",
            "mp3",
            "wav",
            "flac",
            "ogg"
        ]

        ttk.Combobox(
            top_frame,
            textvariable=self.format_var,
            values=formats,
            state="readonly",
            width=10
        ).pack(side="left")

        self.file_list = tk.Listbox(self.root)
        self.file_list.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        ttk.Button(
            self.root,
            text="Convert",
            command=self.start_conversion
        ).pack(pady=10)

        self.log = tk.Text(
            self.root,
            height=10
        )
        self.log.pack(
            fill="both",
            padx=10,
            pady=5
        )

    def add_files(self):

        files = filedialog.askopenfilenames()

        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_list.insert(tk.END, file)

    def write_log(self, text):

        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def start_conversion(self):

        if not self.files:
            messagebox.showwarning(
                "Warning",
                "No files selected"
            )
            return

        threading.Thread(
            target=self.convert_files,
            daemon=True
        ).start()

    def convert_files(self):

        fmt = self.format_var.get()

        output_dir = os.path.join(
            os.getcwd(),
            "converted"
        )

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        for file in self.files:

            name = os.path.splitext(
                os.path.basename(file)
            )[0]

            output = os.path.join(
                output_dir,
                f"{name}.{fmt}"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                file,
                output
            ]

            self.write_log(
                f"Converting: {os.path.basename(file)}"
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
                self.write_log(
                    f"Finished: {output}"
                )
            else:
                self.write_log(
                    f"Failed: {file}"
                )

        self.write_log("")
        self.write_log("ALL CONVERSIONS COMPLETE")

        if os.name == "nt":
            os.startfile(output_dir)


if __name__ == "__main__":

    root = tk.Tk()

    app = FFmpegGUI(root)

    root.mainloop()