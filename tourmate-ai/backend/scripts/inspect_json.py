import json

try:
    with open('indian_cities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            print(f"List of {len(data)} items.")
            print("First item keys:", list(data[0].keys()))
            print("First item:", data[0])
        else:
            print(f"Type: {type(data)}")
            
    with open('world_cities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        indian = [c for c in data if c.get('country') == 'IN']
        print(f"\nWorld Cities IN items: {len(indian)}")
        print("First item keys:", list(indian[0].keys()))
        print("First item:", indian[0])
except Exception as e:
    print("Error:", e)
