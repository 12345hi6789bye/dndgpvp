#!/usr/bin/env python3

import qrcode
import sys
import os

def generate_qr_code(url, save_path="game_qr.png"):
    """Generate QR code for easy mobile access"""
    
    print(f"📱 Generating QR code for: {url}")
    print("-" * 50)
    
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(save_path)
        
        print(f"✅ QR code saved to: {save_path}")
        print()
        print("📲 To use on iPad:")
        print("1. Open the saved QR code image on your laptop screen")
        print("2. Open Camera app on iPad")
        print("3. Point camera at the QR code")
        print("4. Tap the notification to open Safari")
        print("5. Enter your player name and start playing!")
        
        # Also create ASCII version for terminal
        qr_ascii = qrcode.QRCode()
        qr_ascii.add_data(url)
        qr_ascii.make()
        
        print()
        print("📺 QR Code (scan with iPad camera):")
        print("=" * 40)
        qr_ascii.print_ascii(invert=True)
        print("=" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating QR code: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "http://172.20.10.4:3000"
    
    print("🎮 DNDG PVP Blackjack - QR Code Generator")
    print("=" * 50)
    print()
    
    success = generate_qr_code(url)
    
    if success:
        print()
        print("🎯 Alternative connection methods:")
        print(f"   • Direct URL: {url}")
        print("   • QR code image: game_qr.png")
        print("   • ASCII QR code: shown above")
    else:
        print()
        print("🔗 Manual connection:")
        print(f"   Open Safari on iPad and go to: {url}")
