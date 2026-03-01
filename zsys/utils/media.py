# -*- coding: utf-8 -*-
"""
Media utilities - image processing and FFmpeg integration.

Combined utilities for:
- Image resizing and manipulation (PIL/Pillow)
- FFmpeg/FFprobe executable location
"""

import os
import shutil
import platform
from io import BytesIO
from pathlib import Path
from typing import Union, Optional, BinaryIO, Dict

# Import PIL with fallback
try:
    from PIL import Image, UnidentifiedImageError, features
    from PIL.Image import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PILImage = None


# ============================================================================
# FFMPEG UTILITIES
# ============================================================================

def get_ffmpeg_paths() -> Dict[str, Optional[str]]:
    """
    Get paths to ffmpeg and ffprobe executables.
    
    Checks in order:
    1. Bundled executables in bin/ffmpeg/{os}/
    2. System PATH
    
    Returns:
        dict: Dict with 'ffmpeg' and 'ffprobe' paths (or None if not found)
    
    Example:
        paths = get_ffmpeg_paths()
        if paths["ffmpeg"]:
            subprocess.run([paths["ffmpeg"], "-i", "input.mp4"])
    """
    # Import here to avoid circular dependency
    from .filesystem import resource_path, is_android, is_frozen
    
    os_type = platform.system().lower()
    exe_suffix = ".exe" if os_type == "windows" else ""
    executables = ["ffmpeg", "ffprobe"]
    paths: Dict[str, Optional[str]] = {}
    
    # On Android, only use system PATH
    if is_android():
        return {exe: shutil.which(f"{exe}{exe_suffix}") for exe in executables}
    
    # Determine bin directory based on OS
    bin_dir_map = {
        "windows": "win64",
        "linux": "linux64",
        "darwin": "macos",
    }
    bin_dir = bin_dir_map.get(os_type)
    
    if bin_dir is None:
        # Fallback to system PATH for unsupported OS
        return {exe: shutil.which(f"{exe}{exe_suffix}") for exe in executables}
    
    # Check custom bundled location
    custom_dir = Path(resource_path("bin")) / "ffmpeg" / bin_dir
    
    for exe in executables:
        custom_path = custom_dir / f"{exe}{exe_suffix}"
        if custom_path.exists():
            paths[exe] = str(custom_path)
        else:
            # Fallback to system PATH
            paths[exe] = shutil.which(f"{exe}{exe_suffix}")
    
    return paths


def get_ffmpeg() -> Optional[str]:
    """Get path to ffmpeg executable."""
    return get_ffmpeg_paths().get("ffmpeg")


def get_ffprobe() -> Optional[str]:
    """Get path to ffprobe executable."""
    return get_ffmpeg_paths().get("ffprobe")


# ============================================================================
# IMAGE UTILITIES
# ============================================================================

def resize_image(
    input_img: Union[str, Path, BinaryIO, "PILImage"],
    output: Optional[Union[str, Path, BinaryIO]] = None,
    img_type: str = "PNG",
    size: int = 512,
    size2: Optional[int] = None,
    quality: int = 95,
    keep_aspect_ratio: bool = True
) -> Union[BytesIO, None]:
    """
    Resize image with aspect ratio preservation.
    
    Args:
        input_img: Input image (path, file object, or PIL.Image)
        output: Output file/stream (None to create BytesIO)
        img_type: Output image format (PNG, JPEG, WEBP)
        size: Main size (width for landscape, height for portrait)
        size2: Second size (if exact ratio needed)
        quality: Compression quality (1-100)
        keep_aspect_ratio: Keep image proportions
    
    Returns:
        BytesIO: If output=None, returns stream with image
        None: If output specified, saves to file/stream
    
    Raises:
        ImportError: If PIL/Pillow not installed
        ValueError: Invalid parameters
        IOError: Image processing error
    
    Example:
        # Resize to memory
        result = resize_image("photo.jpg", size=256)
        
        # Save to file
        resize_image("photo.jpg", "thumb.png", size=128)
        
        # From PIL.Image
        from PIL import Image
        img = Image.open("photo.jpg")
        result = resize_image(img, size=512, img_type="WEBP", quality=85)
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow not installed. Install: pip install Pillow")
    
    # Validate parameters
    if size <= 0 or (size2 is not None and size2 <= 0):
        raise ValueError("Sizes must be positive numbers")
    if quality < 1 or quality > 100:
        raise ValueError("Quality must be in range 1-100")
    
    # Determine format (with fallback for WEBP)
    format_to_use = img_type.upper()
    if format_to_use == 'WEBP' and not features.check('webp'):
        format_to_use = 'PNG'
    
    # Create BytesIO if output not specified
    return_bytes = output is None
    if return_bytes:
        output = BytesIO()
        output.name = f"resized.{format_to_use.lower()}"
    
    try:
        # Open image
        if isinstance(input_img, PILImage):
            img = input_img
        else:
            img = Image.open(input_img)
        
        # Calculate sizes
        if size2 is not None:
            new_size = (size, size2)
        elif not keep_aspect_ratio or img.width == img.height:
            new_size = (size, size)
        else:
            ratio = img.height / img.width
            if img.width > img.height:  # Landscape
                new_size = (size, max(1, int(size * ratio)))
            else:  # Portrait
                new_size = (max(1, int(size / ratio)), size)
        
        # Save parameters
        save_kwargs = {'format': format_to_use}
        if format_to_use in ('JPEG', 'JPG'):
            save_kwargs['quality'] = quality
            save_kwargs['subsampling'] = 0
        elif format_to_use == 'WEBP':
            save_kwargs['quality'] = quality
        
        # Resize and save
        resized = img.resize(new_size, Image.LANCZOS)
        resized.save(output, **save_kwargs)
        
        if return_bytes:
            output.seek(0)
        
        return output if return_bytes else None
    
    except UnidentifiedImageError as e:
        raise ValueError("Cannot read image") from e
    except Exception as e:
        raise IOError(f"Image processing error: {e}") from e


def get_image_info(
    input_img: Union[str, Path, BinaryIO]
) -> dict:
    """
    Get image information.
    
    Args:
        input_img: Path to image or file object
    
    Returns:
        dict: Dict with keys: width, height, format, mode
    
    Example:
        info = get_image_info("photo.jpg")
        print(f"Size: {info['width']}x{info['height']}")
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow not installed. Install: pip install Pillow")
    
    img = Image.open(input_img)
    return {
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
    }


__all__ = [
    # FFmpeg
    "get_ffmpeg_paths",
    "get_ffmpeg",
    "get_ffprobe",
    # Image
    "resize_image",
    "get_image_info",
    "PIL_AVAILABLE",
]
