"""
OCR Service using Tesseract (FREE - No API needed)
"""

try:
    import pytesseract
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing required packages. Run: pip install pytesseract Pillow")
    raise e

from datetime import datetime
import re
import io
from typing import Dict, Optional

class OCRService:
    """Service for extracting expense details from receipt images using Tesseract OCR"""
    
    def __init__(self):
        """Initialize Tesseract OCR"""
        # For Windows, set tesseract path
        # Uncomment and adjust the path if tesseract is not in PATH
        try:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        except:
            pass  # If tesseract is in PATH, this won't be needed
        
        # Test if tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract OCR initialized (version: {version})")
        except Exception as e:
            print(f"⚠️ Warning: Tesseract not found. Install from: https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"   Error: {e}")
    
    def extract_expense_details(self, image_content: bytes) -> Dict[str, Optional[str]]:
        """
        Extract expense details from receipt image
        
        Args:
            image_content: Binary content of the receipt image
            
        Returns:
            Dictionary containing extracted expense details
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            
            # Perform OCR
            full_text = pytesseract.image_to_string(image)
            
            if not full_text or len(full_text.strip()) < 10:
                return self._empty_response("No text detected in image. Please ensure the receipt is clear and well-lit.")
            
            print(f"\n📄 OCR Extracted Text:\n{full_text}\n")
            
            # Extract details
            extracted_data = {
                'employee': self._extract_employee(full_text),
                'description': self._extract_description(full_text),
                'date': self._extract_date(full_text),
                'category': self._extract_category(full_text),
                'paid_by': self._extract_payment_method(full_text),
                'remark': self._extract_remark(full_text),
                'amount': self._extract_amount(full_text)
            }
            
            print(f"✅ Extracted Data: {extracted_data}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ OCR Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._empty_response(f"OCR processing failed: {str(e)}")
    
    def _preprocess_image(self, image):
        """Improve image quality for better OCR"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Resize if image is too small
            width, height = image.size
            if width < 1000:
                scale_factor = 1500 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            return image
        except Exception as e:
            print(f"Warning: Image preprocessing failed: {e}")
            return image
    
    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract monetary amount from receipt"""
        # Look for total, amount, or price patterns
        patterns = [
            r'total[:\s]*[\$₹€£]?\s*(\d+[,.]?\d*\.?\d*)',
            r'amount[:\s]*[\$₹€£]?\s*(\d+[,.]?\d*\.?\d*)',
            r'grand\s*total[:\s]*[\$₹€£]?\s*(\d+[,.]?\d*\.?\d*)',
            r'balance[:\s]*[\$₹€£]?\s*(\d+[,.]?\d*\.?\d*)',
            r'[\$₹€£]\s*(\d+[,.]?\d*\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                amount = match.group(1).replace(',', '')
                try:
                    float_amount = float(amount)
                    if 0 < float_amount < 1000000:
                        return amount
                except ValueError:
                    continue
        
        # Try to find any decimal number that looks like money
        amounts = re.findall(r'\b(\d+\.\d{2})\b', text)
        if amounts:
            return max(amounts, key=lambda x: float(x))
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt"""
        patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                for fmt in ['%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
                           '%d %B %Y', '%d %b %Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_category(self, text: str) -> str:
        """Determine expense category from receipt content"""
        text_lower = text.lower()
        
        categories = {
            'Food': ['restaurant', 'cafe', 'coffee', 'food', 'dining', 'meal', 'breakfast', 
                    'lunch', 'dinner', 'pizza', 'burger', 'kitchen', 'grill', 'bistro'],
            'Transportation': ['taxi', 'uber', 'lyft', 'ola', 'fuel', 'gas', 'petrol', 
                             'parking', 'toll', 'metro', 'train', 'flight', 'bus'],
            'Accommodation': ['hotel', 'motel', 'accommodation', 'lodging', 'airbnb', 'resort'],
            'Office Supplies': ['office', 'supplies', 'stationery', 'printer', 'paper'],
            'Entertainment': ['movie', 'cinema', 'theater', 'entertainment', 'show'],
            'Medical': ['pharmacy', 'medical', 'hospital', 'clinic', 'doctor', 'medicine'],
            'Utilities': ['electric', 'water', 'internet', 'phone', 'utility'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def _extract_payment_method(self, text: str) -> str:
        """Extract payment method from receipt"""
        text_lower = text.lower()
        
        payment_methods = {
            'Credit Card': ['credit', 'visa', 'mastercard', 'amex'],
            'Debit Card': ['debit'],
            'UPI': ['upi', 'paytm', 'gpay', 'phonepe', 'bhim'],
            'Cash': ['cash'],
        }
        
        for method, keywords in payment_methods.items():
            if any(keyword in text_lower for keyword in keywords):
                return method
        
        return 'Cash'
    
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract business name or description from receipt"""
        lines = text.split('\n')
        if len(lines) > 0:
            for line in lines[:5]:
                line = line.strip()
                if (line and len(line) > 3 and 
                    not re.match(r'^[\d\s\-/:.]+$', line) and
                    not re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', line)):
                    clean_line = re.sub(r'[^a-zA-Z0-9\s&\'-]', '', line)
                    if len(clean_line.strip()) > 3:
                        return clean_line.strip()[:100]
        return None
    
    def _extract_employee(self, text: str) -> Optional[str]:
        """Extract employee name if present on receipt"""
        patterns = [
            r'(?:name|employee|customer)[:\s]+([a-z\s]+)',
            r'(?:mr|ms|mrs)[.\s]+([a-z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if 2 < len(name) < 50 and not re.search(r'\d', name):
                    return name.title()
        
        return None
    
    def _extract_remark(self, text: str) -> Optional[str]:
        """Extract additional remarks or notes"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'note|remark|comment|memo', line, re.IGNORECASE):
                if i + 1 < len(lines):
                    return lines[i + 1].strip()[:200]
        return None
    
    def _empty_response(self, error_message: str = "") -> Dict[str, Optional[str]]:
        """Return empty response structure"""
        return {
            'employee': None,
            'description': error_message if error_message else None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'category': 'Other',
            'paid_by': 'Cash',
            'remark': None,
            'amount': None
        }


# Singleton instance
ocr_service = OCRService()