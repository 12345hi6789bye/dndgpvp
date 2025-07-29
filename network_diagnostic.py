#!/usr/bin/env python3

import socket
import subprocess
import platform
import sys

def check_network_connectivity():
    """Diagnostic tool for network connectivity issues"""
    
    print("🔍 DNDG PVP Blackjack - Network Diagnostic Tool")
    print("=" * 60)
    print()
    
    # 1. Check local IP addresses
    print("1️⃣  Checking Local IP Addresses:")
    print("-" * 35)
    
    try:
        # Get hostname
        hostname = socket.gethostname()
        print(f"   Hostname: {hostname}")
        
        # Get all IP addresses
        if platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=10)
                interfaces = {}
                current_interface = None
                
                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t') and not line.startswith(' '):
                        current_interface = line.split(':')[0]
                        interfaces[current_interface] = []
                    elif current_interface and 'inet ' in line and '127.0.0.1' not in line:
                        ip = line.strip().split()[1]
                        if not ip.startswith('169.254.'):  # Skip link-local
                            interfaces[current_interface].append(ip)
                
                for interface, ips in interfaces.items():
                    if ips:
                        print(f"   {interface}: {', '.join(ips)}")
                        
            except Exception as e:
                print(f"   Error getting interfaces: {e}")
    
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 2. Check if server port is available
    print("2️⃣  Checking Port Availability:")
    print("-" * 35)
    
    def check_port(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return True
        except:
            return False
    
    ports_to_check = [8080, 5000, 3000, 9000]
    available_ports = []
    
    for port in ports_to_check:
        if check_port(port):
            print(f"   ✅ Port {port}: Available")
            available_ports.append(port)
        else:
            print(f"   ❌ Port {port}: In use")
    
    print()
    
    # 3. Network type detection
    print("3️⃣  Network Connection Type:")
    print("-" * 35)
    
    try:
        if platform.system() == "Darwin":
            # Check for WiFi/hotspot
            wifi_result = subprocess.run(['networksetup', '-getinfo', 'Wi-Fi'], 
                                       capture_output=True, text=True, timeout=5)
            if 'IP address:' in wifi_result.stdout:
                for line in wifi_result.stdout.split('\n'):
                    if 'IP address:' in line:
                        wifi_ip = line.split(':')[1].strip()
                        print(f"   WiFi IP: {wifi_ip}")
                        
                        # Detect if it's likely a hotspot
                        if wifi_ip.startswith('172.20.10.') or wifi_ip.startswith('192.168.43.'):
                            print("   📱 Hotspot connection detected!")
                            print("   💡 For iPad hotspot: iPad should connect to this laptop's IP")
                            print("   💡 For laptop hotspot: Other devices connect to laptop's IP")
            
            # Check ethernet
            eth_result = subprocess.run(['networksetup', '-getinfo', 'Ethernet'], 
                                      capture_output=True, text=True, timeout=5)
            if 'IP address:' in eth_result.stdout:
                print("   🔌 Ethernet connection detected")
                        
    except Exception as e:
        print(f"   Could not detect network type: {e}")
    
    print()
    
    # 4. Recommendations
    print("4️⃣  Recommendations:")
    print("-" * 20)
    
    if available_ports:
        recommended_port = available_ports[0]
        print(f"   🎯 Use port {recommended_port} (currently available)")
    else:
        print("   ⚠️  All common ports are in use. Try killing other services or use a different port.")
    
    print("   🌐 For other devices to connect:")
    print("      • Use the IP addresses shown in section 1")
    print("      • Make sure both devices are on the same network")
    print("      • For hotspots: Use the hotspot provider's IP on other devices")
    print("      • Turn off firewall temporarily if connection fails")
    
    print()
    print("5️⃣  Quick Test Commands:")
    print("-" * 25)
    print("   Test from other device (replace IP):")
    print("   curl http://172.20.10.4:8080")
    print("   or ping 172.20.10.4")
    print()

if __name__ == "__main__":
    check_network_connectivity()
