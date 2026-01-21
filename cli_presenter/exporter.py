import os
import markdown
from jinja2 import Template
from typing import List
from .parser import Slide

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Presentation</title>
    <style>
        {{ css }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: true });
    </script>
    <script>
        // Simple navigation script for the HTML export
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function showSlide(n) {
            slides[currentSlide].style.display = 'none';
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].style.display = 'flex';
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                showSlide(currentSlide + 1);
            } else if (e.key === 'ArrowLeft') {
                showSlide(currentSlide - 1);
            }
        });
        
        // Show all slides for printing
        window.onbeforeprint = () => {
             slides.forEach(s => s.style.display = 'flex');
        };
        window.onafterprint = () => {
             slides.forEach(s => s.style.display = 'none');
             slides[currentSlide].style.display = 'flex';
        };
    </script>
</head>
<body>
    {% for slide in slides %}
    <div class="slide layout-{{ slide.metadata.get('layout', 'default') }}">
        {% if slide.metadata.get('logo') %}
        <img src="{{ slide.metadata.get('logo') }}" class="logo" alt="Logo">
        {% endif %}
        <div class="content">
            {{ slide.html_content }}
        </div>
    </div>
    {% endfor %}
    <script>
        // Initialize
        slides.forEach(s => s.style.display = 'none');
        if(slides.length > 0) slides[0].style.display = 'flex';
    </script>
</body>
</html>
"""

def export_to_html(slides: List[Slide], output_path: str, css_path: str = None):
    # Convert markdown to HTML
    for slide in slides:
        slide.html_content = markdown.markdown(slide.content, extensions=['fenced_code', 'codehilite'])
        # Handle mermaid code blocks -> convert to <pre class="mermaid">
        # This is a simple replacement. For robust parsing we might use a markdown extension,
        # but swapping ````mermaid` for `<pre class="mermaid">` often works for simple cases.
        slide.html_content = slide.html_content.replace('<pre><code class="language-mermaid">', '<pre class="mermaid">').replace('</code></pre>', '</pre>')

    # Load CSS
    css_content = ""
    if css_path and os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    else:
        # Default CSS
        css_content = """
        @page { size: 1920px 1080px; margin: 0; }
        body { margin: 0; font-family: sans-serif; background: #eee; }
        .slide { 
            width: 1920px; 
            height: 1080px; 
            background: white; 
            position: relative; 
            display: flex; 
            flex-direction: column; 
            box-sizing: border-box; 
            padding: 50px; 
            margin: 20px auto;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .logo {
            position: absolute;
            top: 40px;
            right: 40px;
            height: 80px;
            width: auto;
        }
        @media print {
            body { background: white; }
            .slide { margin: 0; box-shadow: none; page-break-after: always; }
        }
        .layout-title { justify-content: center; align_items: center; text-align: center; }
        .layout-center { justify-content: center; align_items: center; }
        .content { font-size: 32px; width: 100%; }
        h1 { font-size: 80px; }
        pre.mermaid { background: transparent; display: flex; justify-content: center; }
        """

    # Render HTML
    template = Template(HTML_TEMPLATE)
    html_string = template.render(slides=slides, css=css_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_string)

def export_to_pdf_playwright(html_path: str, pdf_path: str):
    """
    Converts a local HTML file to PDF using Playwright.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
         raise ImportError("Playwright is missing. Run 'pip install playwright' and 'playwright install'.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # file:// protocol requires absolute path
        abs_html_path = os.path.abspath(html_path)
        page.goto(f"file://{abs_html_path}")
        # Wait for mermaid or other content if needed?
        page.wait_for_load_state("networkidle") 
        # Generate PDF
        page.pdf(path=pdf_path, width="1920px", height="1080px", print_background=True)
        browser.close()
