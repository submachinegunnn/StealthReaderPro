import platform
import mss
from PIL import Image
import io

SYSTEM = platform.system()

# Global placeholders for Mac-only libraries
Vision = None
Quartz = None
Cocoa = None

class OCREngine:
    @staticmethod
    def _import_mac_libs():
        """Dynamically imports Mac libs only when running on macOS."""
        global Vision, Quartz, Cocoa
        if Vision is None:
            import Vision as V
            import Quartz as Q
            import Cocoa as C
            Vision, Quartz, Cocoa = V, Q, C

    @staticmethod
    def grab_text(coords):
        try:
            with mss.mss() as sct:
                monitor = {
                    "top": int(coords[1]), 
                    "left": int(coords[0]), 
                    "width": int(coords[2] - coords[0]), 
                    "height": int(coords[3] - coords[1])
                }
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            if SYSTEM == "Darwin":
                OCREngine._import_mac_libs()
                return OCREngine._mac_vision(img)
            else:
                return OCREngine._win_tesseract(img)
        except Exception as e:
            return f"OCR Error: {str(e)}"

    @staticmethod
    def _mac_vision(pil_img):
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        data = Cocoa.NSData.dataWithBytes_length_(img_byte_arr.getvalue(), len(img_byte_arr.getvalue()))
        
        image_source = Quartz.CGImageSourceCreateWithData(data, None)
        cg_image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        
        success, _ = handler.performRequests_error_([request], None)
        if not success: return "[Vision Failed]"
        
        results = request.results()
        return "\n".join([obs.topCandidates_(1)[0].string() for obs in results])

    @staticmethod
    def _win_tesseract(pil_img):
        import pytesseract
        # Ensure Tesseract is installed on Windows!
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        text = pytesseract.image_to_string(pil_img)
        return text.strip() if text.strip() else "[No text detected]"