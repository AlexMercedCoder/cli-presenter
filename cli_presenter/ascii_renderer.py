import io
import re
from functools import lru_cache

# Simple block char set for better density
ASCII_CHARS = ["@", "%", "#", "*", "+", "=", "-", ":", ".", " "]

def pixels_to_ascii(image, width=80):
    # Resize
    w, h = image.size
    aspect = h / w / 0.55 # 0.55 correction for char height
    new_h = int(width * aspect)
    image = image.resize((width, new_h))
    
    # Grayscale
    image = image.convert("L")
    pixels = image.getdata()
    
    # Map to chars (0=Black=@, 255=White=Space)
    # We want Black lines to be @, White background to be Space.
    # So map 0->@ (index 0), 255->Space (index -1)
    
    chars = []
    for p in pixels:
        # p is 0..255
        # index = p / 255 * (len-1)
        idx = int((p / 255) * (len(ASCII_CHARS) - 1))
        # Invert index because our list starts with Darkest
        # plain mapping: 0 -> @, 255 -> ' ' (last)
        chars.append(ASCII_CHARS[idx])
        
    result = ""
    for i in range(0, len(chars), width):
        result += "".join(chars[i:i+width]) + "\n"
        
    return result

@lru_cache(maxsize=32)
def render_mermaid_to_ascii(mermaid_code: str) -> str:
    """
    Renders mermaid code to ASCII using Playwright.
    Cached to avoid re-spawning browser.
    """
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
    except ImportError:
        return "Install 'playwright' and 'Pillow' for ASCII diagrams."

    html = f"""
    <!DOCTYPE html>
    <body>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        <div class="mermaid">
        {mermaid_code}
        </div>
    </body>
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html)
            try:
                page.wait_for_selector('.mermaid svg', timeout=3000)
                element = page.locator('.mermaid')
                png_bytes = element.screenshot()
                
                image = Image.open(io.BytesIO(png_bytes))
                return pixels_to_ascii(image)
                
            except Exception as e:
                return f"Error rendering mermaid: {e}"
            finally:
                browser.close()
    except Exception as e:
        return f"Playwright Error: {e}"
