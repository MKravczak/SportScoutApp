from PIL import Image, ImageDraw, ImageFont
import os

# Create directories if they don't exist
os.makedirs('app/static/img/players', exist_ok=True)
os.makedirs('app/static/img/profiles', exist_ok=True)

# Create a blank image with a gray background
img = Image.new('RGB', (200, 200), color=(240, 240, 240))
d = ImageDraw.Draw(img)

# Draw a silhouette
d.ellipse((75, 50, 125, 100), fill=(180, 180, 180))  # Head
d.rectangle((60, 100, 140, 180), fill=(180, 180, 180))  # Body

# Add text
try:
    # Try to load a font (if available)
    font = ImageFont.truetype("arial.ttf", 20)
    d.text((70, 20), "No Photo", fill=(100, 100, 100), font=font)
except:
    # Fallback to default font
    d.text((70, 20), "No Photo", fill=(100, 100, 100))

# Save the image
img.save('app/static/img/default_player.png')
print("Default player image created successfully.") 