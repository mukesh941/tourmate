import re

with open('seed_hotels.py', 'r') as f:
    content = f.read()

# Lower prices significantly to be budget friendly
# Currently they range from $17 to $124. We can make them $5 to $35.
def lower_price(match):
    key = match.group(1)
    val = float(match.group(2))
    # Let's say we divide by 3 and round down, minimum 5
    new_val = max(5.0, round(val / 3.5))
    return f"{key}: {new_val:.1f}"

content = re.sub(r'(price_per_night(?:_start)?):\s*([\d.]+)', lower_price, content)

with open('seed_hotels.py', 'w') as f:
    f.write(content)

print("Prices reduced successfully.")
