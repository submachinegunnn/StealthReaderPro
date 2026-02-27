import customtkinter as ctk
from ocr_engine import OCREngine 
from ai_handler import AIHandler
from win_utils import protect_window
import json
import os
import platform
import webbrowser
from datetime import datetime

# Platform Check
SYSTEM = platform.system()

# Platform-specific logic for Hotkeys
if SYSTEM == "Windows":
    import keyboard

class AreaSelector(ctk.CTkToplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.attributes("-alpha", 0.3)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        
        self.canvas = ctk.CTkCanvas(self, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = self.start_y = self.rect = None
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='#A020F0', width=3)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        coords = (min(self.start_x, event.x), min(self.start_y, event.y), 
                  max(self.start_x, event.x), max(self.start_y, event.y))
        self.destroy()
        self.callback(coords)

class StealthReader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- APP STATE ---
        self.api_key = "" 
        self.history = []
        self.hotkey = "ctrl+alt+s"
        self.show_manual_box = True
        self.load_settings()
        self.ai = AIHandler(self.api_key)

        # --- WINDOW CONFIG ---
        self.title(f"STEALTH READER PRO")
        self.geometry("1100x880")
        self.configure(fg_color="#0B0B0B")

        # Layout Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        
        # Main Content Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=30, pady=(30, 0), sticky="nsew")
        
        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self, height=35, fg_color="#121212", corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="SYSTEM INITIALIZING...", font=("Arial", 11, "bold"), text_color="#A020F0")
        self.status_label.pack(side="left", padx=20)

        self.copy_status_btn = ctk.CTkButton(self.status_bar, text="📋 COPY OUTPUT", width=100, height=22, font=("Arial", 10), fg_color="transparent", border_width=1, border_color="#333", command=self.copy_to_clipboard)
        self.copy_status_btn.pack(side="right", padx=10)

        # Initialize Tabs
        self.init_home_tab()
        self.init_history_tab()
        self.init_settings_tab()
        
        self.show_home()

        # Initial Protection Launch
        self.after(500, self.perform_security_check)

    # --- UI INITIALIZATION ---
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#121212", border_color="#A020F0", border_width=1)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="S T E A L T H", font=("Impact", 32), text_color="#A020F0").pack(pady=40)
        
        self.nav_home = self.create_nav_btn("🏠  HOME", self.show_home)
        self.nav_history = self.create_nav_btn("📜  HISTORY", self.show_history)
        self.nav_settings = self.create_nav_btn("⚙️  SETTINGS", self.show_settings)

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, fg_color="transparent", border_width=1, border_color="#A020F0", anchor="w", command=command)
        btn.pack(pady=10, padx=20, fill="x")
        return btn

    def init_home_tab(self):
        self.home_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        
        # Manual Input Box
        self.manual_input_frame = ctk.CTkFrame(self.home_frame, fg_color="#121212", border_color="#333", border_width=1)
        self.manual_entry = ctk.CTkEntry(self.manual_input_frame, placeholder_text="Enter custom prompt or code...", fg_color="transparent", border_width=0)
        self.manual_entry.pack(side="left", fill="x", expand=True, padx=10, pady=5)
        self.manual_entry.bind("<Return>", lambda e: self.process_manual())
        ctk.CTkButton(self.manual_input_frame, text="⚡ SEND", width=80, fg_color="#A020F0", command=self.process_manual).pack(side="right", padx=5)
        
        if self.show_manual_box: self.manual_input_frame.pack(fill="x", pady=(0, 10))

        # Main Code Box
        font_family = "Menlo" if SYSTEM == "Darwin" else "Consolas"
        self.output_text = ctk.CTkTextbox(self.home_frame, fg_color="#0D0D0D", text_color="#D1D1D1", border_color="#A020F0", border_width=2, font=(font_family, 14), padx=20, pady=20)
        self.output_text.pack(fill="both", expand=True, pady=10)

        self.scan_btn = ctk.CTkButton(self.home_frame, text="INITIATE VISION SCAN", height=55, font=("Arial", 16, "bold"), fg_color="#A020F0", command=self.start_capture)
        self.scan_btn.pack(fill="x", pady=20)

    def init_history_tab(self):
        self.history_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(self.history_frame, text="DECODED HISTORY", font=("Arial", 18, "bold"), text_color="#A020F0").pack(pady=(0, 20))
        
        font_family = "Menlo" if SYSTEM == "Darwin" else "Consolas"
        self.history_box = ctk.CTkTextbox(self.history_frame, fg_color="#121212", border_color="#333", border_width=1, font=(font_family, 12))
        self.history_box.pack(fill="both", expand=True)
        ctk.CTkButton(self.history_frame, text="CLEAR CHRONICLES", fg_color="transparent", border_width=1, border_color="#FF4B4B", text_color="#FF4B4B", command=self.clear_history).pack(pady=10)

    def init_settings_tab(self):
        self.settings_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="SYSTEM CONFIGURATION", font=("Arial", 18, "bold"), text_color="#A020F0").pack(pady=(0, 30))
        
        self.api_entry = self.create_setting_row("API KEY (OPENROUTER):", self.api_key, True)
        self.hk_entry = self.create_setting_row("HOTKEY (WIN ONLY):", self.hotkey)

        self.manual_switch = ctk.CTkSwitch(self.settings_frame, text="Enable Quick Input Box", progress_color="#A020F0")
        if self.show_manual_box: self.manual_switch.select()
        self.manual_switch.pack(pady=20)

        ctk.CTkButton(self.settings_frame, text="SAVE & APPLY", height=45, fg_color="#A020F0", command=self.save_settings).pack(pady=20)

    def create_setting_row(self, label, value, is_pw=False):
        row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        row.pack(fill="x", padx=100, pady=10)
        ctk.CTkLabel(row, text=label, font=("Arial", 11, "bold")).pack(anchor="w")
        entry = ctk.CTkEntry(row, border_color="#A020F0", show="*" if is_pw else "")
        entry.insert(0, value)
        entry.pack(fill="x", pady=5)
        return entry

    # --- CORE LOGIC ---
    def perform_security_check(self):
        if SYSTEM == "Windows":
            success = protect_window(self)
            if success: self.update_status("STEALTH PROTECTION ACTIVE", "#00FF7F")
            else: self.update_status("PROTECTION FAILED", "#FF4B4B")
            self.bind_hotkey()
        else:
            self.update_status("OSX MODE: APPLE VISION OCR READY", "#00BFFF")

    def update_status(self, msg, color="#A020F0"):
        self.status_label.configure(text=f"● {msg}", text_color=color)

    def process_manual(self):
        text = self.manual_entry.get().strip()
        if text:
            self.manual_entry.delete(0, 'end')
            self.execute_ai(text)

    def start_capture(self):
        self.update_status("SELECTING AREA...", "#A020F0")
        AreaSelector(lambda coords: self.execute_ai(OCREngine.grab_text(coords)))

    def execute_ai(self, text):
        if not text or "[No text detected]" in text:
            self.update_status("SCAN FAILED: NO TEXT FOUND", "#FF4B4B")
            return
            
        self.update_status("AI ANALYZING...", "#FFFF00")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", ">> CONNECTION ESTABLISHED...\n>> DECRYPTING DATASTREAM...")
        self.update()
        
        response = self.ai.process_text(text, "openrouter/free")
        
        self.history.append({"time": datetime.now().strftime("%H:%M:%S"), "text": response})
        self.output_text.delete("1.0", "end")
        self.output_text.insert("end", response)
        self.update_status("READY", "#00FF7F")
        self.save_settings()

    def bind_hotkey(self):
        if SYSTEM == "Windows":
            try:
                keyboard.unhook_all_hotkeys()
                keyboard.add_hotkey(self.hotkey, self.start_capture)
            except: pass

    # --- DATA PERSISTENCE ---
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
                "show_manual_box": self.show_manual_box
            }, f)
        
        if self.show_manual_box: self.manual_input_frame.pack(fill="x", pady=(0, 10), before=self.output_text)
        else: self.manual_input_frame.pack_forget()
        
        self.perform_security_check()

    def load_settings(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key", "")
                    self.history = data.get("history", [])
                    self.hotkey = data.get("hotkey", "ctrl+alt+s")
                    self.show_manual_box = data.get("show_manual_box", True)
            except: pass

    # --- HELPERS ---
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
        # Use .get() to provide a fallback if 'text' or 'content' is missing
            content = item.get('text') or item.get('content') or "[Empty Entry]"
            timestamp = item.get('time', "00:00:00")
        
            self.history_box.insert("end", f"📅 {timestamp}\n{content}\n\n" + ("-"*45) + "\n\n")

    def show_home(self): self.hide_all(); self.home_frame.pack(fill="both", expand=True); self.nav_home.configure(fg_color="#A020F0")
    def show_history(self): self.hide_all(); self.update_history_view(); self.history_frame.pack(fill="both", expand=True); self.nav_history.configure(fg_color="#A020F0")
    def show_settings(self): self.hide_all(); self.settings_frame.pack(fill="both", expand=True); self.nav_settings.configure(fg_color="#A020F0")
    
    def hide_all(self):
        for f in [self.home_frame, self.history_frame, self.settings_frame]: f.pack_forget()
        for b in [self.nav_home, self.nav_history, self.nav_settings]: b.configure(fg_color="transparent")

if __name__ == "__main__":
    app = StealthReader()
    app.mainloop()