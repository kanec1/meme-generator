from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import os
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Route for the home page
@app.route("/")
def home():
    return render_template("index.html")

# Generate meme (caption + text) in one call
def generate_meme_text_from_image(image):
    # Resize image to speed up processing
    max_size = (1024, 1024)
    image.thumbnail(max_size)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode()

    prompt = (
        "Look at this image and do the following:\n"
        "1. Describe it in one clear sentence.\n"
        "2. Write a funny meme caption in exactly two lines separated by |.\n"
        "Return only the two caption lines."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }],
        temperature=0.9,
        max_tokens=150
    )

    text = response.choices[0].message.content.strip()
    if "|" in text:
        top_text, bottom_text = text.split("|", 1)
    else:
        top_text, bottom_text = text, ""
    return top_text.strip(), bottom_text.strip()

# Draw text on image (simplified)
def draw_text(draw, text, x, y, max_width, from_bottom=False, font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    font_size = 50
    font = ImageFont.truetype(font_path, font_size)
    width, height = draw.im.size
    max_width = max_width or width - 20

    # Simple wrapping
    words = text.split()
    lines, line = [], ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0,0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    total_height = len(lines) * font_size
    y = height - total_height - 10 if from_bottom else 10

    # Draw outline + text
    for i, line in enumerate(lines):
        line_y = y + i * font_size
        for dx in [-2,0,2]:
            for dy in [-2,0,2]:
                draw.text((x+dx, line_y+dy), line, font=font, anchor="mm", fill="black")
        draw.text((x, line_y), line, font=font, anchor="mm", fill="white")

# Meme generation route
@app.route("/generate", methods=["POST"])
def generate_meme():
    image_file = request.files["image"]
    image = Image.open(image_file).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    top_text, bottom_text = generate_meme_text_from_image(image)

    draw_text(draw, top_text.upper(), x=width//2, y=None, max_width=width-20, from_bottom=False)
    draw_text(draw, bottom_text.upper(), x=width//2, y=None, max_width=width-20, from_bottom=True)

    os.makedirs("static", exist_ok=True)
    meme_path = "static/meme.png"
    image.save(meme_path, format="PNG")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    meme_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

    return render_template("index.html", meme_url=meme_url, download_url=meme_path)

# Download route
@app.route("/download")
def download_meme():
    meme_path = "static/meme.png"
    return send_file(meme_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
