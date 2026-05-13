import os
import sys
import socket

# Force IPv4 to resolve "Network is unreachable" errors in IPv6-hostile environments
old_getaddrinfo = socket.getaddrinfo
def force_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = force_ipv4

# Force the current directory into the python path for Docker/HuggingFace
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
