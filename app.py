from flask import Flask, request, render_template, send_file, url_for
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

# Generate funny meme caption using a public URL
def generate_meme_text_from_image(image_filename):
    # Construct a public URL for Render to serve the image
    image_url = url_for('static', filename=image_filename, _external=True)

    prompt = (
        f"Look at this image and write a funny two-line meme caption.\n"
        f"Use humor, exaggeration, or sarcasm.\n"
        f"Return exactly two lines separated by |, with no labels.\n"
        f"Image URL: {image_url}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
        max_tokens=150
    )

    text = response.choices[0].message.content.strip()
    if "|" in text:
        top_text, bottom_text = text.split("|", 1)
    else:
        top_text, bottom_text = text, ""
    return top_text.strip(), bottom_text.strip()

# Draw text on the image
def draw_text(draw, text, x, y, max_width, from_bottom=False,
              font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    font_size = 50
    font = ImageFont.truetype(font_path, font_size)
    width, height = draw.im.size
    max_width = max_width or width - 20

    # Simple word wrap
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

    # Save uploaded image to static folder
    os.makedirs("static", exist_ok=True)
    image_filename = image_file.filename
    image_path = os.path.join("static", image_filename)
    image_file.save(image_path)

    # Open image for editing
    max_size = (1024, 1024)   # maximum width/height
    image.thumbnail(max_size)  # preserves aspect ratio
    width, height = image.size
    draw = ImageDraw.Draw(image)


    # Generate captions using public URL
    top_text, bottom_text = generate_meme_text_from_image(image_filename)

    draw_text(draw, top_text.upper(), x=width//2, y=None, max_width=width-20, from_bottom=False)
    draw_text(draw, bottom_text.upper(), x=width//2, y=None, max_width=width-20, from_bottom=True)

    # Save meme
    meme_path = os.path.join("static", "meme.png")
    image.save(meme_path, format="PNG")

    # Return as base64 for preview
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
