from textual.app import App, ComposeResult
from textual.widgets import Footer, Markdown, Static
from textual.containers import Container, ScrollableContainer
from textual.binding import Binding
from typing import List
import os
from .parser import Slide

class SlideWidget(ScrollableContainer):
    """Widget to display a single slide."""
    
    def __init__(self, slide: Slide, **kwargs):
        super().__init__(**kwargs)
        self.slide = slide
        # Add layout class if present
        layout = slide.metadata.get("layout", "default")
        self.add_class(f"layout-{layout}")
    
    def compose(self) -> ComposeResult:
        yield Markdown(self.slide.content)

class PresenterApp(App):
    """A terminal-based presentation tool."""
    
    CSS = """
    SlideWidget {
        width: 100%;
        height: 100%;
        padding: 2 4;
    }
    
    Markdown {
        width: 100%;
        margin: 0 0;
    }
    
    /* Layouts */
    .layout-title {
        align: center middle;
        text-align: center;
    }
    
    .layout-title Markdown {
        text-align: center;
    }

    .layout-center {
        align: center middle;
    }
    
    /* Global style tweaks */
    Screen {
        layers: base overlay;
    }
    """
    
    BINDINGS = [
        Binding("right,space,l", "next_slide", "Next"),
        Binding("left,h", "prev_slide", "Previous"),
        Binding("q,escape", "quit", "Quit"),
        Binding("f", "toggle_fullscreen", "Fullscreen"),
    ]

    def __init__(self, slides: List[Slide], **kwargs):
        super().__init__(**kwargs)
        self.slides = slides
        self.current_slide_index = 0

    def compose(self) -> ComposeResult:
        yield Footer()
        if self.slides:
            yield SlideWidget(self.slides[0], id="current-slide")
        else:
            yield Static("No slides found.")

    def on_mount(self):
        self.title = "CLI Presenter"
        self._update_slide_title()
        
        # Load external theme if present
        if os.path.exists("theme.tcss"):
            self.stylesheet.read("theme.tcss")

    def _update_slide_title(self):
         self.sub_title = f"Slide {self.current_slide_index + 1} / {len(self.slides)}"

    async def update_slide(self):
        slide_widget = self.query_one("#current-slide", SlideWidget)
        await slide_widget.remove()
        
        new_slide = SlideWidget(self.slides[self.current_slide_index], id="current-slide")
        self.mount(new_slide)
        self._update_slide_title()

    async def action_next_slide(self):
        if self.current_slide_index < len(self.slides) - 1:
            self.current_slide_index += 1
            await self.update_slide()

    async def action_prev_slide(self):
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            await self.update_slide()

