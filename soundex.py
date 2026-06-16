#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import webbrowser
import re
import threading
import subprocess
import shutil
import time
import tkinter as tk
import os

HISTORY_DIR = os.path.expanduser("~/.local/share/soundex")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
WATCHLIST_FILE = os.path.join(HISTORY_DIR, "watchlist.json")
os.makedirs(HISTORY_DIR, exist_ok=True)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=150, height=45, radius=22, bg_color="#4a90e2", hover_color="#357abd", text_color="#121212", font=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.radius = radius
        self.bg_color_hex = bg_color
        self.hover_color_hex = hover_color
        
        self.bg_color = self.hex_to_rgb(bg_color)
        self.hover_color = self.hex_to_rgb(hover_color)
        self.current_color = self.bg_color
        self.target_color = self.bg_color
        self.is_animating = False
        
        self.text_color = text_color
        self.font = font or ("Courier New", 14, "bold")
        self.text_str = text
        self.bind("<Configure>", self.draw)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = self.radius
        points = [r, 0, w-r, 0, w, 0, w, r, w, h-r, w, h, w-r, h, r, h, 0, h, 0, h-r, 0, r, 0, 0]
        hex_c = self.rgb_to_hex(self.current_color)
        self.create_polygon(points, fill=hex_c, smooth=True, tags="bg")
        self.create_text(w/2, h/2, text=self.text_str, font=self.font, fill=self.text_color, tags="text")

    def animate_color(self):
        curr = self.current_color
        targ = self.target_color
        if curr != targ:
            step = 0.2
            new_curr = (
                curr[0] + (targ[0] - curr[0]) * step,
                curr[1] + (targ[1] - curr[1]) * step,
                curr[2] + (targ[2] - curr[2]) * step
            )
            if abs(targ[0] - new_curr[0]) < 1 and abs(targ[1] - new_curr[1]) < 1 and abs(targ[2] - new_curr[2]) < 1:
                self.current_color = targ
            else:
                self.current_color = new_curr
            
            hex_c = self.rgb_to_hex(self.current_color)
            self.itemconfig("bg", fill=hex_c)
            self.after(16, self.animate_color)
        else:
            self.is_animating = False

    def on_enter(self, e):
        self.target_color = self.hover_color
        self.config(cursor="hand2")
        if not self.is_animating:
            self.is_animating = True
            self.animate_color()

    def on_leave(self, e):
        self.target_color = self.bg_color
        self.config(cursor="")
        if not self.is_animating:
            self.is_animating = True
            self.animate_color()

    def on_click(self, e):
        flash = self.hex_to_rgb("#ffffff")
        self.current_color = flash
        self.animate_color()
        if self.command:
            self.command()

class SoundexApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Soundex")
        self.geometry("650x450")
        self.configure(bg="#121212")
        self.resizable(False, False)
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.accent_color = "#4a90e2"
        self.history_data = []
        self.watchlist_data = []
        self.current_selection = None
        self._after_id = None
        self.suggestions = []
        self.poster_image = None
        
        self.is_loading = False
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0

        self.load_data()
        self.setup_ui()

    def load_data(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r') as f:
                    self.history_data = json.load(f)
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, 'r') as f:
                    self.watchlist_data = json.load(f)
        except Exception:
            pass

    def save_data(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history_data, f)
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump(self.watchlist_data, f)
        except Exception:
            pass

    def setup_ui(self):
        # Bottom Navigation Bar
        self.bottom_bar = tk.Frame(self, bg="#1a1a1a", height=50)
        self.bottom_bar.pack(side="bottom", fill="x")
        self.bottom_bar.pack_propagate(False)

        wl_btn = tk.Label(self.bottom_bar, text="★ WATCH LIST", font=("Courier New", 12, "bold"), bg="#1a1a1a", fg="#aaaaaa", cursor="hand2")
        wl_btn.pack(side="left", padx=20, pady=15)
        wl_btn.bind("<Button-1>", lambda e: self.show_watchlist())
        wl_btn.bind("<Enter>", lambda e, b=wl_btn: b.config(fg="#ffffff"))
        wl_btn.bind("<Leave>", lambda e, b=wl_btn: b.config(fg="#aaaaaa"))

        hist_btn = tk.Label(self.bottom_bar, text="🕒 HISTORY", font=("Courier New", 12, "bold"), bg="#1a1a1a", fg="#aaaaaa", cursor="hand2")
        hist_btn.pack(side="right", padx=20, pady=15)
        hist_btn.bind("<Button-1>", lambda e: self.show_history())
        hist_btn.bind("<Enter>", lambda e, b=hist_btn: b.config(fg="#ffffff"))
        hist_btn.bind("<Leave>", lambda e, b=hist_btn: b.config(fg="#aaaaaa"))

        # Main Content
        self.main_content = tk.Frame(self, bg="#121212")
        self.main_content.pack(fill="both", expand=True)

        tk.Label(self.main_content, text="S O U N D E X", font=("Courier New", 32, "bold"), bg="#121212", fg=self.accent_color).pack(pady=(25, 15))

        # Search Bar
        self.entry_frame = tk.Frame(self.main_content, bg="#333333", padx=2, pady=2)
        self.entry_frame.pack(pady=(0, 5))
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.entry_frame, textvariable=self.entry_var, font=("Courier New", 15), width=35, bg="#1e1e1e", fg="#ffffff", insertbackground="white", relief="flat", highlightthickness=0)
        self.entry.pack(ipadx=10, ipady=12)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Return>", lambda e: self.on_enter_pressed())
        self.entry.bind("<Down>", lambda e: self.suggestion_box.focus_set())
        
        # Suggestions Dropdown
        self.suggestion_box = tk.Listbox(self.main_content, bg="#1e1e1e", fg="#ffffff", font=("Courier New", 12), height=5, relief="flat", highlightthickness=1, highlightbackground="#333333", selectbackground=self.accent_color, activestyle="none")
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestion_box.bind("<Return>", self.on_suggestion_select)

        # Preview Area
        self.preview_frame = tk.Frame(self.main_content, bg="#121212")
        
        self.poster_lbl = tk.Label(self.preview_frame, bg="#121212")
        self.poster_lbl.pack(side="left", padx=(0, 15))
        
        self.info_frame = tk.Frame(self.preview_frame, bg="#121212")
        self.info_frame.pack(side="left", fill="both", expand=True)
        
        self.title_lbl = tk.Label(self.info_frame, text="", font=("Courier New", 14, "bold"), bg="#121212", fg="#ffffff", wraplength=300, justify="left")
        self.title_lbl.pack(anchor="w")
        self.desc_lbl = tk.Label(self.info_frame, text="", font=("Courier New", 10), bg="#121212", fg="#aaaaaa", wraplength=300, justify="left")
        self.desc_lbl.pack(anchor="w", pady=(5,0))

        # TV Show Controls
        self.tv_frame = tk.Frame(self.info_frame, bg="#121212")
        tk.Label(self.tv_frame, text="Season:", font=("Courier New", 10), bg="#121212", fg="#ffffff").pack(side="left")
        self.season_var = tk.StringVar(value="1")
        tk.Entry(self.tv_frame, textvariable=self.season_var, width=3, bg="#1e1e1e", fg="white", font=("Courier New", 10), relief="flat", highlightthickness=1, highlightbackground="#333333").pack(side="left", padx=(5,15), ipady=2)
        
        tk.Label(self.tv_frame, text="Episode:", font=("Courier New", 10), bg="#121212", fg="#ffffff").pack(side="left")
        self.episode_var = tk.StringVar(value="1")
        tk.Entry(self.tv_frame, textvariable=self.episode_var, width=3, bg="#1e1e1e", fg="white", font=("Courier New", 10), relief="flat", highlightthickness=1, highlightbackground="#333333").pack(side="left", padx=5, ipady=2)

        # Buttons
        self.btn_frame = tk.Frame(self.info_frame, bg="#121212")
        
        self.play_btn = RoundedButton(self.btn_frame, text="PLAY", command=self.play_movie, width=100, height=35, radius=17, bg_color=self.accent_color, hover_color="#357abd", font=("Courier New", 11, "bold"))
        self.play_btn.pack(side="left", padx=(0, 10))
        
        self.trailer_btn = RoundedButton(self.btn_frame, text="TRAILER", command=self.play_trailer, width=100, height=35, radius=17, bg_color="#444444", hover_color="#666666", text_color="#ffffff", font=("Courier New", 11, "bold"))
        self.trailer_btn.pack(side="left", padx=(0, 10))
        
        self.watch_later_btn = RoundedButton(self.btn_frame, text="[+] LATER", command=self.add_to_watchlist, width=100, height=35, radius=17, bg_color="#e67e22", hover_color="#d35400", text_color="#ffffff", font=("Courier New", 11, "bold"))
        self.watch_later_btn.pack(side="left")

        # Status
        self.status_lbl = tk.Label(self.main_content, text="Ready.", font=("Courier New", 10), bg="#121212", fg="#666666")
        self.status_lbl.pack(side="bottom", pady=10)
        
        self.entry.focus_set()

    def set_status(self, text, color="#888888"):
        self.status_lbl.config(text=text, fg=color)
        self.update_idletasks()

    def start_loading_animation(self):
        self.is_loading = True
        self.animate_loading()

    def stop_loading_animation(self):
        self.is_loading = False

    def animate_loading(self):
        if self.is_loading:
            self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            char = self.spinner_chars[self.spinner_idx]
            self.set_status(f"Searching {char}", self.accent_color)
            self.after(100, self.animate_loading)

    def on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Return', 'Escape', 'Left', 'Right']:
            return
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self.fetch_suggestions)

    def on_enter_pressed(self):
        if self.suggestion_box.winfo_ismapped():
            self.suggestion_box.focus_set()
            self.suggestion_box.selection_set(0)
            self.on_suggestion_select(None)
        else:
            self.play_movie()

    def fetch_suggestions(self):
        query = self.entry_var.get().strip()
        if not query or len(query) < 2:
            self.suggestion_box.pack_forget()
            self.preview_frame.pack_forget()
            self.stop_loading_animation()
            self.set_status("Ready.", "#666666")
            return

        self.start_loading_animation()
        threading.Thread(target=self._fetch_suggestions_thread, args=(query,), daemon=True).start()

    def _fetch_suggestions_thread(self, query):
        query_clean = re.sub(r'[^a-zA-Z0-9]', '_', query).lower()
        query_clean = re.sub(r'_+', '_', query_clean).strip('_')
        if not query_clean: 
            self.stop_loading_animation()
            return
        
        first_char = query_clean[0]
        url = f"https://v2.sg.media-imdb.com/suggestion/{first_char}/{urllib.parse.quote(query_clean)}.json"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode('utf-8'))
            
            results = []
            if 'd' in data:
                for item in data['d']:
                    if 'id' in item and item['id'].startswith('tt'):
                        img = item['i']['imageUrl'] if 'i' in item and 'imageUrl' in item['i'] else ""
                        results.append({
                            'id': item['id'],
                            't': item.get('l', 'Unknown'),
                            'y': str(item.get('y', '')),
                            's': item.get('s', ''),
                            'type': item.get('qid', 'movie'),
                            'img': img
                        })
            self.after(0, self.show_suggestions, results)
        except Exception:
            self.stop_loading_animation()

    def show_suggestions(self, results):
        self.stop_loading_animation()
        self.suggestions = results
        self.suggestion_box.delete(0, tk.END)
        self.preview_frame.pack_forget()
        
        if results:
            for r in results:
                display_text = f"{r['t']} ({r['y']})" if r['y'] else r['t']
                self.suggestion_box.insert(tk.END, display_text)
            self.suggestion_box.pack(after=self.entry_frame, pady=5, fill="x", padx=40)
            self.set_status("Matches found.", "#666666")
        else:
            self.suggestion_box.pack_forget()
            self.set_status("No matches found.", "#e74c3c")

    def on_suggestion_select(self, event):
        selection = self.suggestion_box.curselection()
        if selection:
            idx = selection[0]
            self.current_selection = self.suggestions[idx]
            self.entry_var.set(self.current_selection['t'])
            self.suggestion_box.pack_forget()
            self.entry.focus_set()
            self.update_preview()

    def update_preview(self):
        if not self.current_selection: return
        item = self.current_selection
        
        y_text = f" ({item['y']})" if item['y'] else ""
        self.title_lbl.config(text=item['t'] + y_text)
        self.desc_lbl.config(text=item['s'])
        
        self.preview_frame.pack(pady=20, fill="x", padx=40)
        self.btn_frame.pack(anchor="w", pady=(10, 0))
        
        if item['type'] == 'tvSeries':
            self.tv_frame.pack(anchor="w", pady=(5,0))
        else:
            self.tv_frame.pack_forget()

        self.poster_lbl.config(image='')
        if item['img']:
            self.set_status("Loading poster...", "#888888")
            threading.Thread(target=self._fetch_poster, args=(item['img'],), daemon=True).start()

    def _fetch_poster(self, img_url):
        proxy_url = f"https://wsrv.nl/?url={urllib.parse.quote(img_url)}&output=png&w=100"
        try:
            req = urllib.request.Request(proxy_url, headers={'User-Agent': 'Mozilla/5.0'})
            raw_data = urllib.request.urlopen(req).read()
            self.poster_image = tk.PhotoImage(data=raw_data)
            self.after(0, lambda: self.poster_lbl.config(image=self.poster_image))
            self.after(0, lambda: self.set_status("Ready to stream.", "#2ecc71"))
        except Exception:
            self.after(0, lambda: self.set_status("Ready to stream.", "#2ecc71"))

    def open_fullscreen(self, url):
        if shutil.which("brave-browser"):
            subprocess.Popen(["brave-browser", "--new-window", "--start-maximized", "--kiosk", url])
        elif shutil.which("brave"):
            subprocess.Popen(["brave", "--new-window", "--start-maximized", "--kiosk", url])
        elif shutil.which("google-chrome"):
            subprocess.Popen(["google-chrome", "--new-window", "--start-maximized", "--kiosk", url])
        elif shutil.which("chromium"):
            subprocess.Popen(["chromium", "--new-window", "--start-maximized", "--kiosk", url])
        elif shutil.which("firefox"):
            subprocess.Popen(["firefox", "--new-window", "--kiosk", url])
        else:
            webbrowser.open(url)
            if shutil.which("xdotool"):
                def wait_and_fullscreen():
                    time.sleep(3)
                    subprocess.Popen(["xdotool", "key", "F11"])
                threading.Thread(target=wait_and_fullscreen, daemon=True).start()

    def play_movie(self):
        if not self.current_selection:
            return

        imdb_id = self.current_selection['id']
        url = f"https://www.playimdb.com/title/{imdb_id}/"
        
        if self.current_selection['type'] == 'tvSeries':
            s = self.season_var.get().strip() or "1"
            e = self.episode_var.get().strip() or "1"
            url += f"{s}/{e}/"

        # Update History
        self.history_data = [x for x in self.history_data if x['id'] != self.current_selection['id']]
        self.history_data.insert(0, self.current_selection)
        self.history_data = self.history_data[:20]
        self.save_data()

        self.set_status("Opening in fullscreen...", "#2ecc71")
        self.open_fullscreen(url)

    def play_trailer(self):
        if not self.current_selection:
            return
        query = f"{self.current_selection['t']} {self.current_selection['y']} official trailer"
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        self.open_fullscreen(url)

    def add_to_watchlist(self):
        if not self.current_selection:
            return
        # Prevent duplicates
        for item in self.watchlist_data:
            if item['id'] == self.current_selection['id']:
                self.set_status("Already in Watch List!", "#e67e22")
                return
        
        self.watchlist_data.insert(0, self.current_selection)
        self.save_data()
        self.set_status(f"Added '{self.current_selection['t']}' to Watch List.", "#e67e22")

    def create_list_popup(self, title, data_list, is_history=False):
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry("400x300")
        top.resizable(False, False)
        top.configure(bg="#121212")
        
        # Focus the window explicitly instead of grab_set to avoid freezing
        top.focus_set()

        tk.Label(top, text=title.upper(), font=("Courier New", 18, "bold"), bg="#121212", fg=self.accent_color).pack(pady=15)
        
        container = tk.Frame(top, bg="#121212")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if not data_list:
            tk.Label(container, text="This list is empty.", font=("Courier New", 12), bg="#121212", fg="#888888").pack(pady=40)
            return top

        # Create canvas for scrollable list
        canvas = tk.Canvas(container, bg="#121212", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#121212")

        # Fixed width prevents infinite Configure loops on Linux WMs
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=340)
        
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for item in data_list:
            row = tk.Frame(scrollable_frame, bg="#1a1a1a")
            row.pack(fill="x", pady=2)
            
            lbl = tk.Label(row, text=f"{item['t']} ({item['y']})", font=("Courier New", 10), bg="#1a1a1a", fg="#ffffff", anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            
            # Click title to load it
            lbl.bind("<Button-1>", lambda e, i=item, t=top: self.load_and_close(i, t))
            lbl.bind("<Enter>", lambda e, l=lbl: l.config(fg=self.accent_color))
            lbl.bind("<Leave>", lambda e, l=lbl: l.config(fg="#ffffff"))

            # Remove button
            rm_btn = tk.Label(row, text="[X]", font=("Courier New", 10, "bold"), bg="#1a1a1a", fg="#e74c3c", cursor="hand2")
            rm_btn.pack(side="right", padx=10)
            rm_btn.bind("<Button-1>", lambda e, i=item, t=top, hist=is_history: self.remove_item(i, t, hist))
        
        if is_history:
            clr_btn = tk.Button(top, text="CLEAR ALL", font=("Courier New", 10), bg="#e74c3c", fg="#ffffff", relief="flat", command=lambda: self.clear_all_history(top))
            clr_btn.pack(pady=(0,10))

        return top

    def load_and_close(self, item, top):
        top.destroy()
        self.current_selection = item
        self.entry_var.set(item['t'])
        self.suggestion_box.pack_forget()
        self.update_preview()

    def remove_item(self, item, top, is_history):
        if is_history:
            self.history_data = [x for x in self.history_data if x['id'] != item['id']]
        else:
            self.watchlist_data = [x for x in self.watchlist_data if x['id'] != item['id']]
        self.save_data()
        top.destroy()
        if is_history:
            self.show_history()
        else:
            self.show_watchlist()

    def clear_all_history(self, top):
        self.history_data = []
        self.save_data()
        top.destroy()

    def show_history(self):
        self.create_list_popup("History", self.history_data, is_history=True)

    def show_watchlist(self):
        self.create_list_popup("Watch List", self.watchlist_data, is_history=False)

if __name__ == "__main__":
    app = SoundexApp()
    app.mainloop()
