# AI Meme Generator (Flask + OpenAI Vision)

This project is a small, end-to-end Flask application that demonstrates how to integrate **OpenAI vision models**, **image processing**, and **web uploads** to generate captioned memes from user-provided images.

It is designed as a **teaching example** showing how to wire together:
- A web server and UI (Flask)
- Public image hosting for AI consumption
- Prompted text generation using OpenAI
- Dynamic text rendering on images using PIL
- Practical deployment constraints

---

## What the App Does

1. A user uploads an image through a web form.
2. The image is saved to a publicly accessible `/static` directory.
3. A public URL for the image is sent to OpenAI with a structured prompt.
4. OpenAI returns a **two-line meme caption**.
5. The caption is split into **top text** and **bottom text**.
6. Text is dynamically sized and rendered onto the image.
7. The final meme is displayed in the browser and available for download.

---

## Project Structure

- app.py # Main Flask application
- templates/
    - index.html # Upload form and preview UI
- static/
    - <uploads> # User-uploaded images
    - meme.png # Generated meme output

---

## Requirements

### Python
- Python 3.9+

### Dependencies

```
bash
pip install flask pillow openai

``` 

### Environment Variables

An OpenAI API key is required:

```
export OPENAI_API_KEY="your_api_key_here"
```

### Running the App Locally
python app.py

Then visit:

http://localhost:5000

## Key Design Decisions
### Public Image URLs for OpenAI

The /static directory saves the images for the public url access. This mirrors how images would typically be served from object storage (e.g. S3) in production and allows OpenAI to “see” the image.

``` 
url_for("static", filename=image_filename, _external=True)
```

### Structured Prompting

The OpenAI prompt enforces a strict output format:

- Exactly two lines

- Lines separated by |

- No labels or extra text

- This makes the model output deterministic and easy to parse into top and bottom captions.

### Dynamic Text Rendering

The draw_text() function:

- Automatically scales font size based on image dimensions

- Wraps text to fit width constraints

- Supports top or bottom placement

- Draws outlined white text for readability on varied backgrounds

This avoids hard-coded font sizes and makes the output resilient to different image shapes and resolutions.

### Image Processing

- Images are auto-rotated using EXIF data

- Converted to RGB for consistency

- Resized to a max of 1024×1024 to control memory usage and processing time

### Output

- The final meme is saved as static/meme.png

- The image is also returned as base64 for immediate browser preview

- A dedicated /download route allows users to download the image

## Limitations

- The output file is overwritten on each request

- No authentication or rate limiting

- Single-user oriented

- Caption quality depends on image clarity and content

These tradeoffs are intentional to keep the example focused and easy to reason about.

## Possible Improvements

- Generate unique filenames per request

- Store images in cloud object storage

- Add file size and type validation

- Background or async OpenAI calls

- Multi-user support and persistence

- Content moderation or safety filtering

## Purpose

This project is intentionally simple but realistic. It demonstrates how to:

1. Integrate OpenAI into a web backend

2. Handle real deployment constraints

3. Process user-generated media

4. Build a complete AI-powered feature from request to output

It is meant as a learning and interview discussion artifact, not a hardened production system.