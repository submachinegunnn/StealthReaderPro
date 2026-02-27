import subprocess
import platform
import sys

def install(packages):
    for package in packages:
        try:
            print(f"--- Attempting to install: {package} ---")
            # Using --no-cache-dir ensures a fresh install if things were broken
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}. Error: {e}")

# Common libraries for both OS
common = [
    "customtkinter", 
    "mss", 
    "Pillow", 
    "openai", 
    "pypresence"
]

# Windows specific
windows_only = [
    "pytesseract",
    "keyboard"
]

# macOS specific
mac_only = [
    "pyobjc-framework-Vision", 
    "pyobjc-framework-Cocoa"
]

system = platform.system()

if __name__ == "__main__":
    print(f"🚀 System Detected: {system}")
    print("---------------------------------------")
    
    # 1. Install common libraries
    install(common)
    
    # 2. Install OS specific libraries
    if system == "Windows":
        print("🪟 Windows detected. Installing Tesseract wrapper and Keyboard hooks...")
        install(windows_only)
        print("\n💡 NOTE: Ensure you have Tesseract-OCR installed at C:\\Program Files\\Tesseract-OCR")
        
    elif system == "Darwin": # macOS
        print("🍎 macOS detected. Installing Apple Vision & Cocoa frameworks...")
        install(mac_only)
        print("\n💡 NOTE: Keyboard library is skipped on Mac to avoid Permission/Root errors.")
    
    print("---------------------------------------")
    print("✅ Setup process finished!")