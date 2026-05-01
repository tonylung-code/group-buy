import socket
import requests

# 強制映射 IP (這是 Google Global Cache 的穩定 IP)
DNS_CACHE = {
    'oauth2.google.com': '142.251.42.234',
    'www.googleapis.com': '142.251.43.10',
    'sheets.googleapis.com': '142.251.43.10'
}

orig_getaddrinfo = socket.getaddrinfo

def patched_getaddrinfo(host, *args, **kwargs):
    if host in DNS_CACHE:
        return orig_getaddrinfo(DNS_CACHE[host], *args, **kwargs)
    return orig_getaddrinfo(host, *args, **kwargs)

socket.getaddrinfo = patched_getaddrinfo

print("--- 正在嘗試繞過系統 DNS 連線 Google ---")
try:
    r = requests.get("https://oauth2.google.com/token", timeout=5)
    print(f"連線成功！狀態碼: {r.status_code} (預期為 405 或 400，只要不是 NXDOMAIN 即可)")
except Exception as e:
    print(f"連線依舊失敗: {e}")