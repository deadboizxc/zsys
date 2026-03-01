# ZSYS Resources

Static resources and assets for ZSYS applications.

## Structure

```
resources/
├── fonts/         # Font files for UI rendering
├── images/        # Images, icons, logos
├── locales/       # Internationalization (i18n) translations
├── static/        # Static files for web interfaces
└── templates/     # Template files (HTML, config templates)
```

## Fonts

Font files used for text rendering, image generation, and UI components.

**Usage:**
```python
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent / "resources"
FONTS_DIR = RESOURCES_DIR / "fonts"

# Load a font
font_path = FONTS_DIR / "Roboto-Regular.ttf"
```

**Common Use Cases:**
- Text overlay on images
- Generating memes/banners
- PDF generation
- Custom UI rendering

## Images

Images, icons, logos, and visual assets.

**Usage:**
```python
from pathlib import Path
from PIL import Image

IMAGES_DIR = Path(__file__).parent / "resources" / "images"

# Load an image
logo = Image.open(IMAGES_DIR / "logo.png")

# Use in bot
@command("logo")
async def send_logo(ctx):
    await ctx.send_photo(IMAGES_DIR / "logo.png")
```

**Common Use Cases:**
- Bot avatars and logos
- Default images for missing media
- Icons for UI elements
- Templates for image manipulation

## Locales

Internationalization (i18n) translation files.

**Typical Structure:**
```
locales/
├── en/
│   └── LC_MESSAGES/
│       └── messages.po
├── ru/
│   └── LC_MESSAGES/
│       └── messages.po
└── es/
    └── LC_MESSAGES/
        └── messages.po
```

**Usage with gettext:**
```python
import gettext

# Setup translation
lang = gettext.translation(
    'messages',
    localedir='resources/locales',
    languages=['ru']
)
_ = lang.gettext

# Use translations
print(_("Hello, world!"))  # -> "Привет, мир!"
```

**Usage with Babel:**
```python
from babel.support import Translations

translations = Translations.load(
    dirname='resources/locales',
    locales=['ru']
)

_ = translations.gettext
print(_("Welcome"))  # -> "Добро пожаловать"
```

**Common Use Cases:**
- Multi-language bot responses
- Localized UI text
- Region-specific content
- Help messages in different languages

## Static

Static files for web interfaces (CSS, JavaScript, images for web).

**Typical Structure:**
```
static/
├── css/
│   └── style.css
├── js/
│   └── app.js
├── img/
│   └── favicon.ico
└── lib/
    └── jquery.min.js
```

**Usage with FastAPI:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="resources/static"),
    name="static"
)
```

**Usage in HTML:**
```html
<link rel="stylesheet" href="/static/css/style.css">
<script src="/static/js/app.js"></script>
<img src="/static/img/logo.png" alt="Logo">
```

**Common Use Cases:**
- Web dashboard assets
- Admin panel resources
- API documentation static files
- Client-side JavaScript/CSS

## Templates

Template files for generating dynamic content.

**Typical Structure:**
```
templates/
├── html/
│   ├── dashboard.html
│   └── email.html
├── config/
│   ├── nginx.conf.j2
│   └── systemd.service.j2
└── markdown/
    └── readme.md.j2
```

**Usage with Jinja2:**
```python
from jinja2 import Environment, FileSystemLoader

# Setup Jinja2
env = Environment(
    loader=FileSystemLoader('resources/templates')
)

# Render template
template = env.get_template('html/dashboard.html')
html = template.render(
    title="ZSYS Dashboard",
    user=user_obj,
    stats=stats_dict
)
```

**Usage with FastAPI:**
```python
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="resources/templates")

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "html/dashboard.html",
        {"request": request, "user": user}
    )
```

**Common Use Cases:**
- HTML emails
- Dynamic web pages
- Configuration file generation
- Report generation
- Documentation templates

## Accessing Resources

### Using Pathlib
```python
from pathlib import Path

# Get resources directory
RESOURCES_DIR = Path(__file__).parent / "resources"

# Access specific resources
fonts_dir = RESOURCES_DIR / "fonts"
images_dir = RESOURCES_DIR / "images"
locales_dir = RESOURCES_DIR / "locales"
static_dir = RESOURCES_DIR / "static"
templates_dir = RESOURCES_DIR / "templates"
```

### Using Package Resources
```python
from importlib.resources import files

# Get resource path (Python 3.9+)
resources = files("zsys.resources")
font_path = resources / "fonts" / "Roboto-Regular.ttf"
```

### Environment Variables
```python
import os
from pathlib import Path

# Allow overriding resources directory
RESOURCES_DIR = Path(
    os.getenv("ZSYS_RESOURCES_DIR", "resources")
)
```

## Best Practices

1. **Use Relative Paths**: Always use relative paths within resources
2. **Version Assets**: Keep track of asset versions (e.g., `logo_v2.png`)
3. **Compress Images**: Optimize images before adding them
4. **Organize by Type**: Keep similar resources together
5. **Document Usage**: Add README in subdirectories for complex structures
6. **License Files**: Include LICENSE files for third-party resources
7. **Resource Loading**: Cache loaded resources in memory for performance

## Integration Example

```python
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

class ResourceManager:
    """Centralized resource management."""
    
    def __init__(self, resources_dir: Path):
        self.resources_dir = resources_dir
        self.fonts_dir = resources_dir / "fonts"
        self.images_dir = resources_dir / "images"
        self._font_cache = {}
        self._image_cache = {}
    
    def get_font(self, name: str, size: int = 12):
        """Get font with caching."""
        key = f"{name}:{size}"
        if key not in self._font_cache:
            path = self.fonts_dir / name
            self._font_cache[key] = ImageFont.truetype(str(path), size)
        return self._font_cache[key]
    
    def get_image(self, name: str):
        """Get image with caching."""
        if name not in self._image_cache:
            path = self.images_dir / name
            self._image_cache[name] = Image.open(path)
        return self._image_cache[name].copy()
    
    def generate_banner(self, text: str) -> Image.Image:
        """Generate a banner with text."""
        bg = self.get_image("banner_bg.png")
        font = self.get_font("Roboto-Bold.ttf", size=48)
        
        draw = ImageDraw.Draw(bg)
        draw.text((50, 50), text, font=font, fill=(255, 255, 255))
        
        return bg

# Usage
resources = ResourceManager(Path("resources"))
banner = resources.generate_banner("Welcome to ZSYS!")
banner.save("output.png")
```

## Contributing

When adding new resources:

1. **Optimize**: Compress images, minify CSS/JS
2. **License**: Ensure proper licensing for third-party assets
3. **Document**: Update this README with new resource types
4. **Organize**: Place files in appropriate subdirectories
5. **Test**: Verify resources load correctly across platforms
