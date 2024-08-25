

# NO ERRORSSSSSSSSSSSSSSSSSSSSSSSSSSSS 

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyperclip
import yt_dlp as ytdlp
import re
import threading
import time
import requests

class ClipboardFileDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JAYDEV ")
        
        self.text = tk.Text(root, height=15, width=50)
        self.text.pack(padx=10, pady=10)
        
        self.clipboard_button = tk.Button(root, text="Check Clipboard", command=self.check_clipboard)
        self.clipboard_button.pack(pady=5)

        self.file_button = tk.Button(root, text="Open Text File", command=self.open_text_file)
        self.file_button.pack(pady=5)
        
        self.manual_button = tk.Button(root, text="Download from Text Box", command=self.download_from_text_box)
        self.manual_button.pack(pady=5)

        self.change_path_button = tk.Button(root, text="Change Download Path", command=self.change_download_path)
        self.change_path_button.pack(pady=5)

        # Set default download path to user's Downloads directory
        self.download_path = os.path.expanduser('~/Downloads')
        self.downloads = []
        self.total_size = 0
        self.start_time = None
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None

    def change_download_path(self):
        initial_dir = self.download_path  # Start from current download path or default Downloads folder
        new_path = filedialog.askdirectory(title="Select Download Directory", initialdir=initial_dir)
        
        if not new_path:  # If no path is selected, revert to default Downloads directory
            self.download_path = os.path.expanduser('~/Downloads')
            self.show_alert("Default Path", f"No directory selected. Download path set to default:\n{self.download_path}")
        else:
            self.download_path = new_path
            self.show_alert("Success", f"Download path changed to:\n{self.download_path}")

    def check_clipboard(self):
        content = pyperclip.paste()
        if content:
            urls = self.extract_urls(content)
            if urls:
                self.start_download(urls)
            else:
                self.show_alert("Clipboard Content", "No valid links found in clipboard.")

    def open_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                except Exception as e:
                    self.show_alert("Error", f"An error occurred: {e}")
                    return

            urls = self.extract_urls(content)
            if urls:
                self.show_alert("File Content", "\n".join([url[0] for url in urls]))
                self.start_download(urls)
            else:
                self.show_alert("File Content", "No valid links found in the file.")

    def download_from_text_box(self):
        content = self.text.get("1.0", tk.END).strip()
        if content:
            urls = self.extract_urls(content)
            if urls:
                self.start_download(urls)
            else:
                self.show_alert("Text Box Content", "No valid links found in the text box.")

    def start_download(self, urls):
        if not self.download_path:
            self.show_alert("Error", "Download directory not set.")
            return
        
        self.downloads.clear()
        self.total_size = 0

        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Downloading")

        self.progress_label = tk.Label(self.progress_window, text="Initializing...")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_window, orient='horizontal', length=400, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        self.start_time = time.time()

        threading.Thread(target=self.perform_downloads, args=(urls,), daemon=True).start()

    def perform_downloads(self, urls):
        ytdlp_opts = {
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,  # Avoid downloading playlists
        }
        
        with ytdlp.YoutubeDL(ytdlp_opts) as ydl:
            total_files = len(urls)
            for i, (url, filename_prefix) in enumerate(urls):
                try:
                    # Download the file
                    info_dict = ydl.extract_info(url, download=True)
                    original_filename = ydl.prepare_filename(info_dict)
                    
                    # Rename file to use the prefix
                    new_filename = os.path.join(self.download_path, f'{filename_prefix}.pdf')
                    os.rename(original_filename, new_filename)
                    
                    # Update the total size
                    filesize = os.path.getsize(new_filename)
                    self.total_size += filesize
                    self.downloads.append(url)
                    
                    elapsed_time = time.time() - self.start_time
                    estimated_total_time = (elapsed_time / (i + 1)) * total_files
                    remaining_time = estimated_total_time - elapsed_time
                    
                    self.update_progress(i + 1, total_files, remaining_time)
                except Exception as e:
                    print(f"Failed to download {url}: {e}")

        self.progress_window.destroy()
        self.show_summary()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # Update progress bar based on the downloaded data
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.progress_bar['value'] = percent
                self.progress_label.config(text=f"Downloading: {percent:.2f}%")
                self.progress_window.update_idletasks()
        elif d['status'] == 'finished':
            filename = d['filename']
            filesize = d['total_bytes']
            print(f"Finished downloading {filename} ({filesize} bytes)")
            
    def update_progress(self, completed, total, remaining_time):
        if self.progress_label and self.progress_bar:
            elapsed = time.time() - self.start_time
            progress_percent = (completed / total) * 100
            self.progress_bar['value'] = progress_percent
            progress_text = (f"Completed {completed}/{total} downloads.\n"
                             f"Elapsed Time: {self.format_time(elapsed)}\n"
                             f"Estimated Time Remaining: {self.format_time(remaining_time)}")
            self.progress_label.config(text=progress_text)
            self.progress_window.update_idletasks()

    def format_time(self, seconds):
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def extract_urls(self, text):
        # Regex pattern for extracting URLs
        url_pattern = r'(.*?)(https?://[^\s]+)'
        matches = re.findall(url_pattern, text)

        def clean_url(url):
            match = re.search(r'file=(https?://[^\s]+)', url)
            if match:
                return match.group(1)
            return url

        def get_filename_prefix(prefix_text):
            return prefix_text.strip().replace(';', '').replace(':', '').replace('/', '_').replace('\\', '_')  # Sanitizing the filename

        cleaned_urls = []
        for prefix_text, url in matches:
            clean_url_text = clean_url(url)
            filename_prefix = get_filename_prefix(prefix_text)
            cleaned_urls.append((clean_url_text, filename_prefix))

        return cleaned_urls

    def show_alert(self, title, message):
        alert = tk.Toplevel(self.root)
        alert.title(title)
        tk.Label(alert, text=message).pack(padx=10, pady=10)
        tk.Button(alert, text="OK", command=alert.destroy).pack(pady=5)

    def show_summary(self):
        total_size_mb = self.total_size / (1024 * 1024)
        self.show_alert("Download Complete", f"Total Size of Downloaded Files: {total_size_mb:.2f} MB")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardFileDownloaderApp(root)
    root.mainloop()




