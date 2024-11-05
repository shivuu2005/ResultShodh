from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
import pytesseract

#aapke pytesseract ki location 
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
def Solve(image_content):
    try:
        # Open the image from byte data and convert to grayscale for better OCR accuracy
        image = Image.open(BytesIO(image_content)).convert("L")
        
        # Apply a threshold filter to enhance text visibility (binarization)
        # Pixels above the threshold become white (255), below become black (0)
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)
        
        # Optional: Apply a median filter to smooth out noise (helps in noisy images)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Use pytesseract to extract text, specifying alphanumeric characters only (captcha specific)
        captcha_text = pytesseract.image_to_string(
            image, 
            config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ).strip().replace(" ", "")  # Remove any unwanted spaces in the result
        
        # Print the recognized captcha text
        print(f"Captcha solved: {captcha_text}")
        return captcha_text
    
    except IOError as e:
        print(f"Error opening image: {e}")
        return None
    except pytesseract.TesseractError as e:
        print(f"Tesseract OCR error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error solving captcha: {e}")
        return None

# Example usage:
# Assuming `image_bytes` contains the binary data of the image
# captcha_result = Solve(image_bytes)
