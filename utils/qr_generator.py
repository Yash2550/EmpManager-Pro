import qrcode
import os
from io import BytesIO
import base64


def generate_qr_code(data, filename, save_dir):
    """
    Generate a QR code image and save it.
    Returns the filename of the saved QR code.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#0ea5e9", back_color="white")
    filepath = os.path.join(save_dir, filename)
    img.save(filepath)
    return filename


def generate_qr_base64(data):
    """
    Generate a QR code and return it as a base64-encoded string
    for embedding directly in HTML.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#0ea5e9", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
