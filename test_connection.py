#!/usr/bin/env python3

import requests
import socket
import sys

def test_connection(ip, port):
    """Test if the game server is accessible"""
    
    print(f"🧪 Testing connection to {ip}:{port}")
    print("-" * 40)
    
    # Test 1: Basic socket connection
    print("1️⃣  Testing socket connection...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            result = s.connect_ex((ip, port))
            if result == 0:
                print("   ✅ Socket connection successful")
            else:
                print("   ❌ Socket connection failed")
                return False
    except Exception as e:
        print(f"   ❌ Socket error: {e}")
        return False
    
    # Test 2: HTTP request
    print("2️⃣  Testing HTTP request...")
    try:
        response = requests.get(f"http://{ip}:{port}", timeout=10)
        if response.status_code == 200:
            print("   ✅ HTTP request successful")
        elif response.status_code == 302:
            print("   ✅ HTTP redirect (login required) - Server is working!")
        else:
            print(f"   ⚠️  HTTP response code: {response.status_code}")
    except requests.exceptions.ConnectTimeout:
        print("   ❌ HTTP request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ HTTP connection error")
        return False
    except Exception as e:
        print(f"   ❌ HTTP error: {e}")
        return False
    
    print("   🎉 Connection test PASSED!")
    print(f"   🌐 iPad should be able to access: http://{ip}:{port}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    else:
        ip = "172.20.10.4"
        port = 3000
    
    print("🔗 DNDG PVP Blackjack - Connection Test")
    print("=" * 50)
    print()
    
    success = test_connection(ip, port)
    
    print()
    if success:
        print("✅ ALL TESTS PASSED!")
        print("Your iPad should be able to connect to the game.")
        print()
        print("📱 Next steps for iPad:")
        print("1. Open Safari on iPad")
        print(f"2. Go to: http://{ip}:{port}")
        print("3. Enter a different player name than on laptop")
        print("4. Join the same game room")
        print("5. Start playing!")
    else:
        print("❌ CONNECTION FAILED!")
        print()
        print("🔧 Try these solutions:")
        print("• Turn off firewall on laptop temporarily")
        print("• Make sure iPad hotspot is still active")
        print("• Try a different port (4000, 5000, 9000)")
        print("• Restart the hotspot connection")
    
    print()
