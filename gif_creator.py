import os
from PIL import Image
import imageio

def create_animated_gif(image_paths: list, output_path: str, settings: dict) -> bool:
    """Resizes frames uniformly and builds an animated GIF based on user preferences."""
    try:
        if len(image_paths) < 2:
            return False
            
        # Parse speed constraints down to dynamic duration markers
        speed_map = {"Slow": 0.5, "Normal": 0.2, "Fast": 0.1}
        duration = speed_map.get(settings.get("speed"), 0.2)
        
        # Determine loop metadata
        loop_count = 0 if settings.get("loop_opt") == "Infinite" else 1
        
        frames = []
        # Sample uniform canvas metrics based on the first element
        with Image.open(image_paths[0]) as first_img:
            target_size = first_img.size

        for path in image_paths:
            with Image.open(path) as img:
                # Standardize frame sizing to prevent visual tearing
                img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                # Ensure conversion to RGB format for imageio compatibility
                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')
                
                temp_frame_path = f"{path}_processed.png"
                img_resized.save(temp_frame_path)
                frames.append(imageio.v2.imread(temp_frame_path))
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)

        # Write frames to the animated GIF output path
        imageio.mimsave(output_path, frames, duration=duration, loop=loop_count)
        return True
    except Exception:
        return False

