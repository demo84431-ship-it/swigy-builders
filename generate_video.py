#!/usr/bin/env python3
"""
FoodDNA Demo Video Generator

Renders the demo output as a terminal-style video with voiceover.
Uses PIL for rendering and ffmpeg for video assembly.
"""

import re
import os
from PIL import Image, ImageDraw, ImageFont

# ── Config ──────────────────────────────────────────────────────────────────

WIDTH, HEIGHT = 1280, 720
FPS = 30
BG_COLOR = (30, 30, 30)  # Dark terminal background
TEXT_COLOR = (220, 220, 220)
FONT_SIZE = 16
LINE_HEIGHT = 22
PADDING = 40
CHAR_WIDTH = 9.6  # Approximate for monospace at FONT_SIZE

# ANSI color map
ANSI_COLORS = {
    '0': None,   # reset
    '1': None,   # bold (handled separately)
    '2': (128, 128, 128),  # dim
    '30': (0, 0, 0),
    '31': (205, 49, 49),
    '32': (46, 204, 64),
    '33': (241, 196, 15),
    '34': (52, 152, 219),
    '35': (187, 107, 217),  # magenta
    '36': (44, 209, 209),   # cyan
    '37': (255, 255, 255),
    '90': (80, 80, 80),
    '97': (255, 255, 255),
    '42': (46, 204, 64),    # bg green
    '43': (241, 196, 15),   # bg yellow
    '44': (52, 152, 219),   # bg blue
}

# Voiceover timing (seconds) — when each section starts
VOICEOVER_TIMING = {
    'intro':     0.0,
    'profile':   16.3,
    'scenario1': 16.3 + 1,      # +1s pause
    'scenario2': 16.3 + 43 + 2,
    'scenario3': 16.3 + 43 + 42 + 3,
    'scenario4': 16.3 + 43 + 42 + 61 + 4,
    'scenario5': 16.3 + 43 + 42 + 61 + 27 + 5,
    'outro':     16.3 + 43 + 42 + 61 + 27 + 40 + 6,
}


def parse_ansi(text):
    """Parse ANSI escape codes and return list of (char, color, bold) tuples."""
    result = []
    i = 0
    current_color = TEXT_COLOR
    current_bold = False
    
    while i < len(text):
        if text[i] == '\033' and i + 1 < len(text) and text[i + 1] == '[':
            # Parse ANSI code
            j = i + 2
            while j < len(text) and text[j] != 'm':
                j += 1
            if j < len(text):
                codes = text[i + 2:j].split(';')
                for code in codes:
                    if code == '0':
                        current_color = TEXT_COLOR
                        current_bold = False
                    elif code == '1':
                        current_bold = True
                    elif code in ANSI_COLORS:
                        c = ANSI_COLORS[code]
                        if c is not None:
                            current_color = c
                i = j + 1
                continue
        
        result.append((text[i], current_color, current_bold))
        i += 1
    
    return result


def get_font(bold=False):
    """Get monospace font."""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf',
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, FONT_SIZE)
    return ImageFont.load_default()


def render_frame(lines, scroll_offset=0):
    """Render a single frame with the given lines visible."""
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    font_regular = get_font(bold=False)
    font_bold = get_font(bold=True)
    
    # Calculate visible lines
    max_visible = (HEIGHT - 2 * PADDING) // LINE_HEIGHT
    visible_lines = lines[scroll_offset:scroll_offset + max_visible]
    
    y = PADDING
    for line in visible_lines:
        parsed = parse_ansi(line)
        x = PADDING
        for char, color, bold in parsed:
            font = font_bold if bold else font_regular
            draw.text((x, y), char, fill=color, font=font)
            x += CHAR_WIDTH
        y += LINE_HEIGHT
    
    return img


def generate_video():
    """Generate the demo video."""
    # Read demo output
    with open('demo_output.txt', 'r') as f:
        full_text = f.read()
    
    lines = full_text.split('\n')
    total_lines = len(lines)
    
    # Voiceover audio duration
    voiceover_duration = 258  # seconds (4:18)
    total_frames = voiceover_duration * FPS
    
    # Calculate timing: which lines are visible at each frame
    # Lines appear gradually, synced to voiceover
    # Each section has a time window and line range
    
    sections = [
        ('intro',     0,   20,  0.0,   16.3),   # lines 0-20, time 0-16.3s
        ('profile',   20,  50,  16.3,  17.3),    # lines 20-50, time 16.3-17.3s
        ('scenario1', 50,  75,  17.3,  59.3),    # lines 50-75, time 17.3-59.3s
        ('scenario2', 75,  100, 60.3,  102),      # lines 75-100
        ('scenario3', 100, 120, 103,   164),      # lines 100-120
        ('scenario4', 120, 138, 165,   192),      # lines 120-138
        ('scenario5', 138, 155, 193,   233),      # lines 138-155
        ('outro',     155, 162, 234,   258),      # lines 155-162
    ]
    
    # Build frame schedule: for each frame, determine which lines to show
    print(f"Generating {total_frames} frames at {FPS} fps ({voiceover_duration}s)...")
    
    output_dir = 'frames'
    os.makedirs(output_dir, exist_ok=True)
    
    for frame_num in range(total_frames):
        t = frame_num / FPS
        
        # Determine which lines should be visible
        visible_lines = []
        for name, line_start, line_end, t_start, t_end in sections:
            if t >= t_start:
                # Calculate how many lines from this section to show
                if t >= t_end:
                    progress = 1.0
                else:
                    progress = (t - t_start) / (t_end - t_start)
                progress = min(1.0, progress)
                
                section_lines = lines[line_start:line_end]
                num_visible = int(len(section_lines) * progress)
                visible_lines.extend(section_lines[:num_visible])
        
        # Scroll: show last N lines that fit on screen
        max_visible = (HEIGHT - 2 * PADDING) // LINE_HEIGHT
        scroll_offset = max(0, len(visible_lines) - max_visible)
        
        # Render frame
        img = render_frame(visible_lines, 0)
        
        # Add title bar
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, WIDTH, 30], fill=(20, 20, 20))
        draw.text((10, 6), "🍕 FoodDNA Agent — Demo", fill=(100, 200, 100), font=get_font(bold=True))
        draw.text((WIDTH - 200, 6), f"Swiggy Builders Club", fill=(120, 120, 120), font=get_font(bold=False))
        
        # Save frame
        img.save(f'{output_dir}/frame_{frame_num:05d}.png')
        
        if frame_num % (FPS * 10) == 0:
            print(f"  Frame {frame_num}/{total_frames} ({t:.0f}s / {voiceover_duration}s)")
    
    print(f"Generated {total_frames} frames. Assembling video...")
    
    # Combine frames + voiceover into video
    voiceover_path = 'voiceover-full.wav'
    output_path = 'fooddna-demo.mp4'
    
    os.system(
        f'ffmpeg -y -framerate {FPS} -i {output_dir}/frame_%05d.png '
        f'-i {voiceover_path} '
        f'-c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k '
        f'-shortest {output_path} 2>/dev/null'
    )
    
    # Cleanup frames
    os.system(f'rm -rf {output_dir}')
    
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Video saved: {output_path} ({size_mb:.1f} MB)")
    else:
        print("❌ Video generation failed")


if __name__ == '__main__':
    generate_video()
