import customtkinter as ctk
from ocr_engine import OCREngine 
from ai_handler import AIHandler
from win_utils import protect_window
from overlay import ScreenSelector as AreaSelector
from discord_handler import DiscordHandler
from PIL import ImageTk
from tkinter import messagebox
import json
import os
import platform
import webbrowser
import requests
from datetime import datetime

VERSION = "1.0.0"
REPO_URL = "https://api.github.com/repos/submachinegunnn/StealthReaderPro/releases/latest"

SYSTEM = platform.system()
if SYSTEM == "Windows":
    import keyboard

class StealthReader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.themes = {
            "Stealth Purple": {"accent": "#A020F0", "bg": "#0B0B0B", "card": "#121212"},
            "Cyber Blue": {"accent": "#00BFFF", "bg": "#050505", "card": "#0A0F14"},
            "Monochrome": {"accent": "#FFFFFF", "bg": "#111111", "card": "#1A1A1A"}
        }
        
        self.api_key = "" 
        self.history = []
        self.hotkey = "ctrl+alt+s"
        self.show_manual_box = True
        self.current_theme_name = "Stealth Purple"
        
        self.load_settings()
        
        theme = self.themes.get(self.current_theme_name, self.themes["Stealth Purple"])
        self.accent = theme["accent"]
        self.ai = AIHandler(self.api_key)
        self.discord = DiscordHandler()
        self.discord.update_presence("INITIALIZING", "Loading Stealth Modules")

        self.title("STEALTH READER PRO")
        self.geometry("1100x880")
        self.configure(fg_color=theme["bg"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar(theme)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=30, pady=(30, 0), sticky="nsew")
        self.setup_status_bar(theme)

        self.init_home_tab()
        self.init_history_tab()
        self.init_settings_tab()
        
        self.show_home()

        self.after(500, self.perform_security_check)
        self.after(2000, self.check_for_updates)

    # --- UI SETUP ---
    # --- UI SETUP ---
    def setup_sidebar(self, theme):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, 
                                   fg_color=theme["card"], border_color=self.accent, border_width=1)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="S T E A L T H", 
                    font=("Impact", 32), text_color=self.accent).pack(pady=40)
        
        self.nav_home = self.create_nav_btn("🏠  HOME", self.show_home)
        self.nav_history = self.create_nav_btn("📜  HISTORY", self.show_history)
        self.nav_settings = self.create_nav_btn("⚙️  SETTINGS", self.show_settings)

    def setup_status_bar(self, theme):
        self.status_bar = ctk.CTkFrame(self, height=35, fg_color=theme["card"], corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Zone 1: Activity Status (Bottom Left)
        self.status_label = ctk.CTkLabel(self.status_bar, text="● SYSTEM READY", 
                                        font=("Arial", 11, "bold"), text_color=self.accent)
        self.status_label.pack(side="left", padx=20)

        # Zone 2: Security Indicator (Middle)
        self.security_label = ctk.CTkLabel(self.status_bar, text="SEC: PENDING", 
                                          font=("Arial", 10, "bold"), text_color="#888")
        self.security_label.pack(side="left", padx=20)

        # Zone 3: Version Info (Bottom Right)
        self.version_label = ctk.CTkLabel(self.status_bar, text=f"v{VERSION}", 
                                         font=("Arial", 10), text_color="#555")
        self.version_label.pack(side="right", padx=20)

        ctk.CTkButton(self.status_bar, text="📋 COPY", width=60, height=22, 
                     fg_color="transparent", border_width=1, border_color="#333", 
                     command=self.copy_to_clipboard).pack(side="right", padx=10)

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, fg_color="transparent", 
                           border_width=1, border_color=self.accent, anchor="w", command=command)
        btn.pack(pady=10, padx=20, fill="x")
        return btn

    # --- UPDATER LOGIC (Fixed Position & Indentation) ---
    def check_for_updates(self):
        """Checks GitHub for a newer release version."""
        try:
            response = requests.get(REPO_URL, timeout=5)
            if response.status_code == 200:
                latest_json = response.json()
                remote_version = latest_json.get("tag_name", "1.0.0").replace("v", "")
                if remote_version != VERSION:
                    self.update_status(f"UPDATE AVAILABLE: v{remote_version}", "#FFD700")
                    if messagebox.askyesno("Update Found", f"Version {remote_version} is available! View on GitHub?"):
                        webbrowser.open("https://github.com/submachinegunnn/StealthReaderPro/releases")
        except Exception as e:
            print(f"Update check failed: {e}")

    # --- TABS & CORE LOGIC ---
    def init_home_tab(self):
        self.home_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.manual_input_frame = ctk.CTkFrame(self.home_frame, fg_color="#121212", border_color="#333", border_width=1)
        self.manual_entry = ctk.CTkEntry(self.manual_input_frame, placeholder_text="Enter custom prompt...", fg_color="transparent", border_width=0)
        self.manual_entry.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.manual_entry.bind("<Return>", lambda e: self.process_manual())
        self.send_btn = ctk.CTkButton(self.manual_input_frame, text="⚡ SEND", width=80, fg_color=self.accent, command=self.process_manual)
        self.send_btn.pack(side="right", padx=5)
        if self.show_manual_box: self.manual_input_frame.pack(fill="x", pady=(0, 10))
        font_family = "Menlo" if SYSTEM == "Darwin" else "Consolas"
        self.output_text = ctk.CTkTextbox(self.home_frame, fg_color="#0D0D0D", text_color="#D1D1D1", border_color=self.accent, border_width=2, font=(font_family, 14), padx=20, pady=20)
        self.output_text.pack(fill="both", expand=True, pady=10)
        self.scan_btn = ctk.CTkButton(self.home_frame, text="INITIATE VISION SCAN", height=55, font=("Arial", 16, "bold"), fg_color=self.accent, command=self.start_capture)
        self.scan_btn.pack(fill="x", pady=20)

    def init_history_tab(self):
        self.history_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(self.history_frame, text="DECODED HISTORY", font=("Arial", 18, "bold"), text_color=self.accent).pack(pady=(0, 20))
        font_family = "Menlo" if SYSTEM == "Darwin" else "Consolas"
        self.history_box = ctk.CTkTextbox(self.history_frame, fg_color="#121212", border_color="#333", border_width=1, font=(font_family, 12))
        self.history_box.pack(fill="both", expand=True)
        ctk.CTkButton(self.history_frame, text="CLEAR CHRONICLES", fg_color="transparent", border_width=1, border_color="#FF4B4B", text_color="#FF4B4B", command=self.clear_history).pack(pady=10)

    def init_settings_tab(self):
        self.settings_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="SYSTEM CONFIGURATION", font=("Arial", 18, "bold"), text_color=self.accent).pack(pady=(0, 30))
        self.api_entry = self.create_setting_row("API KEY (OPENROUTER):", self.api_key, True)
        self.hk_entry = self.create_setting_row("HOTKEY (WIN ONLY):", self.hotkey)
        row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        row.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(row, text="UI COLOR SCHEME:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.theme_dropdown = ctk.CTkOptionMenu(row, values=list(self.themes.keys()), command=self.change_theme, fg_color=self.accent, button_color=self.accent)
        self.theme_dropdown.set(self.current_theme_name)
        self.theme_dropdown.pack(fill="x", pady=5)
        self.manual_switch = ctk.CTkSwitch(self.settings_frame, text="Enable Quick Input Box", progress_color=self.accent)
        if self.show_manual_box: self.manual_switch.select()
        self.manual_switch.pack(pady=20)
        # Manual Update Check
        ctk.CTkButton(self.settings_frame, text="CHECK FOR UPDATES", height=32, 
                     fg_color="transparent", border_width=1, border_color="#444", 
                     command=self.check_for_updates).pack(pady=10)
        ctk.CTkButton(self.settings_frame, text="SAVE & APPLY", height=45, fg_color=self.accent, command=self.save_settings).pack(pady=20)

    def create_setting_row(self, label, value, is_pw=False):
        row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        row.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(row, text=label, font=("Arial", 11, "bold")).pack(anchor="w")
        entry = ctk.CTkEntry(row, border_color=self.accent, show="*" if is_pw else "")
        entry.insert(0, value)
        entry.pack(fill="x", pady=5)
        return entry

    def change_theme(self, new_theme_name):
        self.current_theme_name = new_theme_name
        theme = self.themes[new_theme_name]
        self.accent = theme["accent"]
        
        # 1. Update the main window background
        self.configure(fg_color=theme["bg"])
        
        # 2. Update the sidebar and container
        self.sidebar.configure(fg_color=theme["card"], border_color=self.accent)
        self.container.configure(fg_color="transparent") # Keep container clear
        
        # 3. Update the Status Bar
        self.status_bar.configure(fg_color=theme["card"])
        self.status_label.configure(text_color=self.accent)
        
        # 4. Update the Buttons
        self.scan_btn.configure(fg_color=self.accent)
        self.send_btn.configure(fg_color=self.accent)
        self.theme_dropdown.configure(fg_color=self.accent, button_color=self.accent)
        
        # 5. Update the Textbox border
        self.output_text.configure(border_color=self.accent)
        
        # 6. Update Navigation Buttons
        for btn in [self.nav_home, self.nav_history, self.nav_settings]:
            btn.configure(border_color=self.accent)
            # If the button is currently active (selected), update its highlight color
            if btn.cget("fg_color") != "transparent":
                btn.configure(fg_color=self.accent)
        
        # 7. Update any active frames
        self.manual_input_frame.configure(fg_color=theme["card"])
        
        self.save_settings()
        self.update_status(f"THEME UPDATED: {new_theme_name.upper()}", self.accent)

    def perform_security_check(self):
        if SYSTEM == "Windows":
            success = protect_window(self)
            if success:
                self.security_label.configure(text="SEC: STEALTH ACTIVE", text_color="#00FF7F")
            else:
                self.security_label.configure(text="SEC: FAILED", text_color="#FF4B4B")
            self.bind_hotkey()
        else:
            self.security_label.configure(text="SEC: OSX MODE", text_color="#00BFFF")
        self.discord.update_presence("IDLE", "Monitoring System")

    def start_capture(self):
        self.update_status("SELECTING AREA...", self.accent)
        self.discord.update_presence("SCANNING", "Selecting Screen Area")
        AreaSelector(lambda coords: self.handle_ocr_result(OCREngine.grab_text(coords)))

    def handle_ocr_result(self, result):
        text, img = result
        self.show_preview(img)
        self.execute_ai(text)

    def show_preview(self, pil_img):
        preview = ctk.CTkToplevel(self)
        preview.title("Capture Preview")
        preview.attributes("-topmost", True)
        img_tk = ImageTk.PhotoImage(pil_img)
        label = ctk.CTkLabel(preview, image=img_tk, text="")
        label.image = img_tk 
        label.pack(padx=10, pady=10)
        self.after(1200, preview.destroy)

    def execute_ai(self, text):
        if not text or "[No text detected]" in text:
            self.update_status("SCAN FAILED: NO TEXT FOUND", "#FF4B4B")
            return
        self.update_status("AI ANALYZING...", "#FFFF00")
        self.discord.update_presence("THINKING", "Analyzing Decrypted Text")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", ">> CONNECTION ESTABLISHED...\n>> DECRYPTING DATASTREAM...")
        self.update()
        response = self.ai.process_text(text, "openrouter/free")
        self.history.append({"time": datetime.now().strftime("%H:%M:%S"), "text": response})
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", response)
        self.update_status("READY", "#00FF7F")
        self.discord.update_presence("IDLE", "Data Processed")
        self.save_settings()

    def bind_hotkey(self):
        if SYSTEM == "Windows":
            try:
                keyboard.unhook_all_hotkeys()
                keyboard.add_hotkey(self.hotkey, self.start_capture)
            except: pass

    def save_settings(self):
        self.api_key = self.api_entry.get()
        self.hotkey = self.hk_entry.get()
        self.show_manual_box = self.manual_switch.get()
        self.ai = AIHandler(self.api_key)
        with open("config.json", "w") as f:
            json.dump({
                "api_key": self.api_key, 
                "history": self.history, 
                "hotkey": self.hotkey, 
                "theme": self.current_theme_name,
                "show_manual_box": self.show_manual_box
            }, f)
        if self.show_manual_box: self.manual_input_frame.pack(fill="x", pady=(0, 10), before=self.output_text)
        else: self.manual_input_frame.pack_forget()

    def load_settings(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key", "")
                    self.history = data.get("history", [])
                    self.hotkey = data.get("hotkey", "ctrl+alt+s")
                    self.current_theme_name = data.get("theme", "Stealth Purple")
                    self.show_manual_box = data.get("show_manual_box", True)
            except: pass

    def process_manual(self):
        text = self.manual_entry.get().strip()
        if text:
            self.manual_entry.delete(0, 'end')
            self.execute_ai(text)

    def update_status(self, msg, color=None):
        self.status_label.configure(text=f"● {msg}", text_color=color or self.accent)

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.output_text.get("1.0", "end-1c"))
        self.update_status("COPIED TO CLIPBOARD", "#00FF7F")

    def clear_history(self):
        self.history = []
        self.save_settings()
        self.update_history_view()

    def update_history_view(self):
        self.history_box.delete("1.0", "end")
        for item in reversed(self.history):
            content = item.get('text') or item.get('content') or "[Empty]"
            timestamp = item.get('time', "00:00:00")
            self.history_box.insert("end", f"📅 {timestamp}\n{content}\n\n" + ("-"*45) + "\n\n")

    def show_home(self): self.hide_all(); self.home_frame.pack(fill="both", expand=True); self.nav_home.configure(fg_color=self.accent)
    def show_history(self): self.hide_all(); self.update_history_view(); self.history_frame.pack(fill="both", expand=True); self.nav_history.configure(fg_color=self.accent)
    def show_settings(self): self.hide_all(); self.settings_frame.pack(fill="both", expand=True); self.nav_settings.configure(fg_color=self.accent)
    
    def hide_all(self):
        for f in [self.home_frame, self.history_frame, self.settings_frame]: f.pack_forget()
        for b in [self.nav_home, self.nav_history, self.nav_settings]: b.configure(fg_color="transparent")

if __name__ == "__main__":
    app = StealthReader()
    app.mainloop()