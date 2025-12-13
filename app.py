from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import os
from openai import OpenAI
from transformers import BlipProcessor, BlipForConditionalGeneration

app = Flask(__name__)

# Load BLIP model once at startup
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Initialize OpenAI client using API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Route for the form page
@app.route("/")
def home():
    return render_template("index.html")

# Caption the image using BLIP
def caption_image(image):
    image = image.convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    out = blip_model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

# Generate meme text
def generate_meme_text(caption):
    prompt = (
        f"Write a funny meme caption based on this image description:\n{caption}\n"
        "Provide exactly two lines separated by |. DO NOT include any labels."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    text = response.choices[0].message.content.strip()
    if "|" in text:
        top_text, bottom_text = text.split("|", 1)
    else:
        top_text, bottom_text = text, ""
    return top_text.strip(), bottom_text.strip()

# Draw text on image
def draw_text(draw, text, x, y=None, max_width=None, initial_font_size=50,
              from_bottom=False, max_height_ratio=0.25, margin=10):
    font_path = "C:\\Windows\\Fonts\\impact.ttf"
    width, height = draw.im.size
    max_width = max_width or width - 2 * margin
    max_height = int(height * max_height_ratio)

    font_size = initial_font_size
    while font_size > 10:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        # Wrap text into lines
        words = text.split()
        lines = []
        temp_words = words.copy()
        while temp_words:
            line_words = []
            while temp_words:
                line_words.append(temp_words.pop(0))
                line_text = " ".join(line_words)
                bbox = draw.textbbox((0, 0), line_text, font=font)
                if bbox[2] - bbox[0] > max_width:
                    if len(line_words) == 1:
                        break
                    temp_words.insert(0, line_words.pop())
                    break
            lines.append(" ".join(line_words))

        total_height = len(lines) * font_size
        if total_height <= max_height:
            break
        font_size -= 2

    # Determine y-position
    if y is None:
        y = height - total_height - margin if from_bottom else margin
    elif from_bottom:
        y = y - total_height - margin

    # Draw lines with outline
    for i, line in enumerate(lines):
        line_y = y + i * font_size
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                draw.text((x + dx, line_y + dy), line, font=font, anchor="mm", fill="black")
        draw.text((x, line_y), line, font=font, anchor="mm", fill="white")

# Generate meme route
@app.route("/generate", methods=["POST"])
def generate_meme():
    image_file = request.files["image"]
    image = Image.open(image_file).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    caption = caption_image(image)
    top_text, bottom_text = generate_meme_text(caption)

    draw_text(draw, top_text.upper(), x=width // 2, from_bottom=False)
    draw_text(draw, bottom_text.upper(), x=width // 2, from_bottom=True)

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
