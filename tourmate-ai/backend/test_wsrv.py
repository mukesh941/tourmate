import httpx
import urllib.parse
url = urllib.parse.quote('https://upload.wikimedia.org/wikipedia/commons/d/d4/Qutub_Minar%2C_Delhi.jpg')
r = httpx.get(f'https://wsrv.nl/?url={url}')
print(r.status_code)
