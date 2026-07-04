import os
from PIL import Image, ImageSequence

def reverse_gif(input_path: str, output_path: str) -> bool:
    """Extracts all sequential frames from a GIF, reverses them, and saves the result."""
    try:
        with Image.open(input_path) as img:
            frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
            frames.reverse()
            frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0)
            return True
    except Exception:
        return False

def compress_gif(input_path: str, output_path: str) -> bool:
    """Compresses a GIF by lowering the palette depth profile color bounds."""
    try:
        with Image.open(input_path) as img:
            frames = [frame.copy().convert('P', palette=Image.Palette.ADAPTIVE, colors=128) for frame in ImageSequence.Iterator(img)]
            frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0)
            return True
    except Exception:
        return False

