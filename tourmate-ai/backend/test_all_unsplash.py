import httpx

urls = {
    "Red Fort": "https://images.unsplash.com/photo-1587595431973-160d0d94add1?auto=format&fit=crop&w=1200&q=80",
    "Humayun's Tomb": "https://images.unsplash.com/photo-1574169208507-84376144848b?auto=format&fit=crop&w=1200&q=80",
    "Lotus Temple": "https://images.unsplash.com/photo-1590050752112-92144ddf3301?auto=format&fit=crop&w=1200&q=80",
    "Akshardham": "https://images.unsplash.com/photo-1603522198007-8e6f1f44a30f?auto=format&fit=crop&w=1200&q=80",
    "Jama Masjid": "https://images.unsplash.com/photo-1555310931-15b50df4779a?auto=format&fit=crop&w=1200&q=80",
    "India Gate": "https://images.unsplash.com/photo-1585135445207-8898160840b2?auto=format&fit=crop&w=1200&q=80",
    "Chandni Chowk": "https://images.unsplash.com/photo-1585828068970-1b752ebc6604?auto=format&fit=crop&w=1200&q=80",
    "Qutub Minar": "https://images.unsplash.com/photo-1574768399557-4fb8e95fa6f1?auto=format&fit=crop&w=1200&q=80"
}

with httpx.Client(follow_redirects=True) as client:
    for name, url in urls.items():
        r = client.head(url)
        print(f"{name}: {r.status_code}")
