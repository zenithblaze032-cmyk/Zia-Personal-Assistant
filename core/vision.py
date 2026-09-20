import io
from PIL import ImageGrab

def capture_screen_bytes() -> bytes:
    """
    Captures the primary screen and returns the image as bytes (JPEG).
    """
    screenshot = ImageGrab.grab()
    
    # Compress it slightly for speed and to fit within context limits
    # Max size for basic moondream is typically 1024x1024 or similar, but it handles dynamic sizing well
    screenshot.thumbnail((1280, 1280))
    
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='JPEG', quality=85)
    
    return img_byte_arr.getvalue()
