#!/usr/bin/python3

# Created by marwa BIFISSE (Heavy use of chatgpt)

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageColor, UnidentifiedImageError

import os
import re

# Instead of using os.cwd, i created this function to return full path of executed script, so i can load elements correctly

from files import get_dir 

# Get image resolution in pixels (x,y)

def get_image_resolution(image_path):
        # Check if file exists and is readable
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Baddaz '{image_path}' does not exist.")
    if not os.access(image_path, os.R_OK):
        raise PermissionError(f"Baddaz '{image_path}' cannot be read.")
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height

# Create a gradient shadow image bottom.

def create_gradient_shadow_bottom(width, shadow_height):
    
    # Create an empty RGBA shadow
    
    shadow = Image.new('RGBA', (width, shadow_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)

    # Draw vertical gradient (top transparent -> bottom semi-opaque)
    for y in range(shadow_height):
        alpha = int(255 * (y / shadow_height) * 0.5)  # combine 50% opacity reduction here
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

    return shadow

# Create a top gradient shadow

def create_gradient_shadow_top(width, shadow_height, color=(0, 0, 0)):

    shadow = Image.new('RGBA', (width, shadow_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)

    # Draw vertical gradient from top (opaque) to bottom (transparent)

    for y in range(shadow_height):
        alpha = int(255 * ((shadow_height - y) / shadow_height) * 0.5)
        draw.line([(0, y), (width, y)], fill=(color[0], color[1], color[2], alpha))

    return shadow


# Crop image to specific size and add logo and arrow (if image is rectangle)

def add_logo_to_image(
    image_source_path, logo_path, image_output_path, logo_position,
    image_width, image_height, crop_position, logo_margin, logo_decrease_percent,
    arrow_path=None, arrow_position='bottom-right', logo_opacity=None,
    square=None, city=None, imageone=None, title=None, lang=None
):
    # Checks

    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")
    if logo_path and not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file '{logo_path}' not found.")
    if arrow_path:
        if not os.path.isfile(arrow_path):
            raise FileNotFoundError(f"Arrow file '{arrow_path}' not found.")
        if not arrow_path.lower().endswith('.png'):
            raise ValueError("The arrow must be in PNG format.")
    if not os.access(os.path.dirname(image_output_path), os.W_OK):
        os.makedirs(os.path.dirname(image_output_path), exist_ok=True)
    if logo_path and not logo_path.lower().endswith('.png'):
        raise ValueError("The logo must be in PNG format.")

    # Open the image (convert highRes to HD if needed)

    image = convert_to_hd(image_source_path) if is_high_res(image_source_path) else Image.open(image_source_path)
    image = image.convert('RGBA')

    if logo_path:
        logo = Image.open(logo_path).convert('RGBA')

    # Resize image if smaller than the needed size

    if image.width < image_width or image.height < image_height:
        new_width = max(image_width, 1000)
        new_height = max(image_height, 1000)
        if image.width < new_width:
            aspect_ratio = image.height / image.width
            new_width = image_width
            new_height = int(new_width * aspect_ratio)
        elif image.height < new_height:
            aspect_ratio = image.width / image.height
            new_height = image_height
            new_width = int(new_height * aspect_ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop image

    if crop_position == 'right':
        left = image.width - image_width
        top = 0
    elif crop_position == 'left':
        left = 0
        top = 0
    elif crop_position == 'center':
        left = (image.width - image_width) // 2
        top = (image.height - image_height) // 2
    else:
        raise ValueError("Invalid crop position. Choose either 'right', 'left', or 'center'.")
    image = image.crop((left, top, left + image_width, top + image_height))
    image = image.resize((image_width, image_height), Image.Resampling.LANCZOS)

    # Add gradient shadow

    if image_height == 1080 and image_width == 1080:
        sh_path = os.path.join(get_dir(), 'shadows', 'ShadowSB.png')
    elif image_height == 1350 and image_width == 1080:
        sh_path = os.path.join(get_dir(), 'shadows', 'ShadowT.png')
    else:
        sh_path = None

    if sh_path:
        shadowsb = Image.open(sh_path).convert('RGBA')
        image.paste(shadowsb, (0,0), shadowsb)
    else:
        shadow_height = int(image_height * 0.1)
        shadow = create_gradient_shadow_bottom(image_width, shadow_height)
        image.paste(shadow, (0, image_height - shadow_height), shadow)

    # Optional top shadow for first square image

    if square == 'on' and imageone == 0 and image_width == 1080 and image_height == 1080:
        shadow_height = int(image_height * 0.6)
        shadow = create_gradient_shadow_top(image_width, shadow_height)
        image.paste(shadow, (0, 0), shadow)

    # Handle logo

    if logo_path:
        if logo_decrease_percent < 0 or logo_decrease_percent > 90:
            raise ValueError("The logo decrease percentage must be between 0 and 90.")
        decrease_factor = (100 - logo_decrease_percent) / 100
        new_logo_width = int(logo.width * decrease_factor)
        new_logo_height = int(logo.height * decrease_factor)
        logo = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)

        if logo_opacity is not None:
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: p * (logo_opacity / 255.0))
            logo.putalpha(alpha)

        # Determine logo position

        positions = {
            'top-left': (logo_margin, logo_margin),
            'top-right': (image.width - new_logo_width - logo_margin, logo_margin),
            'bottom-left': (logo_margin, image.height - new_logo_height - logo_margin),
            'bottom-right': (image.width - new_logo_width - logo_margin, image.height - new_logo_height - logo_margin),
            'center': ((image.width - new_logo_width) // 2, (image.height - new_logo_height) // 2),
            'top-center': ((image.width - new_logo_width) // 2, logo_margin),
            'bottom-center': ((image.width - new_logo_width) // 2, image.height - new_logo_height - logo_margin)
        }
        if logo_position not in positions:
            raise ValueError("Invalid logo position.")
        pos = positions[logo_position]
        image.paste(logo, pos, logo)

    # Optional title/logo overlays for first square image

    if square == 'on' and imageone == 0 and image_width == 1080 and image_height == 1080:
        for fname in ['shadows/ShadowST.png', 'logo360/LogoTitle.png']:
            path = os.path.join(get_dir(), fname)
            if os.path.isfile(path):
                overlay = Image.open(path).convert('RGBA')
                image.paste(overlay, (0, 0), overlay)

        if title:
            if lang == 'fr':
                font_path = os.path.join(get_dir(), 'fonts', 'DIN-Condensed-Bold.ttf')
                font_size = 100
                add_title_to_image(image, title, font_path, font_size, 'white', 'center', 50, 30, 120)
            elif lang == 'ar':
                font_path = os.path.join(get_dir(), 'fonts', 'ArbFONTS-Somar-Bold.otf')
                font_size = 100
                add_title_to_image(image, title, font_path, font_size, 'white', 'center', 50, -10, 80)

    # Optional arrow

    if arrow_path:
        arrow = Image.open(arrow_path).convert('RGBA')
        arrow_width = int(arrow.width * decrease_factor)
        arrow_height = int(arrow.height * decrease_factor)
        arrow = arrow.resize((arrow_width, arrow_height), Image.Resampling.LANCZOS)
        if logo_opacity is not None:
            alpha = arrow.split()[3]
            alpha = alpha.point(lambda p: p * (logo_opacity / 255.0))
            arrow.putalpha(alpha)

        arrow_positions = {
            'top-left': (logo_margin, logo_margin),
            'top-right': (image.width - arrow_width - logo_margin, logo_margin),
            'bottom-left': (logo_margin, image.height - arrow_height - logo_margin),
            'bottom-right': (image.width - arrow_width - logo_margin, image.height - arrow_height - logo_margin)
        }
        if arrow_position not in arrow_positions:
            raise ValueError("Invalid arrow position.")
        image.paste(arrow, arrow_positions[arrow_position], arrow)

    # Optional city text for 1080x1080

    if square == 'on' and image_width == 1080 and image_height == 1080 and city:
        sep_path = os.path.join(get_dir(), 'logo360', 'LogoSep.png')
        if os.path.isfile(sep_path):
            sep = Image.open(sep_path).convert('RGBA')
            image.paste(sep, (0, 0), sep)

        font_size = 53
        if lang == 'fr':
            font_path = os.path.join(get_dir(), 'fonts', 'DIN-Condensed-Bold.ttf')
            y_pos = 1010
        elif lang == 'ar':
            font_path = os.path.join(get_dir(), 'fonts', 'ArbFONTS-Somar-Bold.otf')
            y_pos = 995
        else:
            font_path = None

        if font_path:
            myfont = ImageFont.truetype(font_path, font_size)
            draw = ImageDraw.Draw(image)
            draw.text((160, y_pos), city, font=myfont, fill='white')

    # Flatten RGBA to RGB with black background

    background_color = (0, 0, 0)  # background
    rgb_image = Image.new("RGB", image.size, background_color)
    rgb_image.paste(image, mask=image.split()[3])  # merge alpha channel

    # Save as JPEG

    rgb_image.save(image_output_path, format='JPEG', quality=100)


# Batch process multiple images
def batch_process_images(image_paths, logo_path, image_output_dir, logo_position, image_width, image_height, crop_position, logo_margin, logo_decrease_percent, arrow_path=None, arrow_position='bottom-right', logo_opacity=None, square=None, city=None, title=None, lang=None):
    
    # Verify that the list of image paths is not empty

    if not image_paths:
        raise ValueError("The list of image paths must contain at least one element.")
    
    # Ensure the output directory exists

    if not os.path.exists(image_output_dir):
        os.makedirs(image_output_dir)
    
    # Process each image in the list

    for i, image_path in enumerate(image_paths):
        # Determine if the current image should have an arrow

        current_arrow_path = arrow_path if (i < len(image_paths) - 1) and (len(image_paths) > 1) else None
        
        # Construct the output path for the current image

        output_path = os.path.join(image_output_dir, f"processed_image_{i + 1}.jpg")
        
        # Call the add_logo_to_image function

        add_logo_to_image(
            image_source_path=image_path,
            logo_path=logo_path,
            image_output_path=output_path,
            logo_position=logo_position,
            image_width=image_width,
            image_height=image_height,
            crop_position=crop_position,
            logo_margin=logo_margin,
            logo_decrease_percent=logo_decrease_percent,
            arrow_path=current_arrow_path,
            arrow_position=arrow_position if current_arrow_path else 'bottom-right',
            logo_opacity=logo_opacity,
            square=square,
            city=city,
            imageone=i,
            title=title,
            lang=lang
        )

# For 1080x1080, function to align text to center

def add_title_to_image(image, text, font_path, font_size, text_color, align='left', margin=10, spacing=0, y_position=None):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    image_width, image_height = image.size
    max_text_width = image_width - 2 * margin

    # Wrap text based on available width

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        # Use font.getbbox() to measure text width
        line_text = ' '.join(current_line)
        bbox = font.getbbox(line_text)
        w = bbox[2] - bbox[0]
        if w > max_text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Calculate total text block height

    text_height = sum([(font.getbbox(line)[3] - font.getbbox(line)[1]) + spacing for line in lines]) - spacing

    # Vertical position

    y = y_position if y_position is not None else (image_height - text_height) // 2

    # Draw each line

    for line in lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]

        # Horizontal alignment

        if align == 'left':
            x = margin
        elif align == 'center':
            x = (image_width - line_width) // 2
        elif align == 'right':
            x = image_width - line_width - margin
        else:
            raise ValueError("Invalid alignment value. Use 'left', 'center', or 'right'.")

        draw.text((x, y), line, font=font, fill=text_color)
        y += line_height + spacing

    return image


# Function to verify if image is HighRes

def is_high_res(image_path, min_width=1920, min_height=1080):
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The file at {image_path} does not exist.")

        with Image.open(image_path) as img:
            width, height = img.size
            return width >= min_width and height >= min_height

    except FileNotFoundError as fnf_error:
        print(f"FileNotFoundError: {fnf_error}")
    except UnidentifiedImageError:
        print(f"UnidentifiedImageError: The file at {image_path} is not a valid image or cannot be opened.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return False

# Function to force respect the aspect ratio

def calculate_new_dimensions(width, height, max_width=1920, max_height=1080):
    aspect_ratio = width / height

    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
    else:
        new_width, new_height = width, height

    return new_width, new_height

# convert HighRes to HD

def convert_to_hd(image_path, max_width=1920, max_height=1080):
    if is_high_res(image_path):
        try:
            with Image.open(image_path) as img:
                # Calculate the new dimensions while maintaining the aspect ratio
                new_width, new_height = calculate_new_dimensions(img.width, img.height, max_width, max_height)
                
                # Resize the image using Pillow 10 compatible resampling
                img_hd = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                return img_hd

        except FileNotFoundError as fnf_error:
            print(f"FileNotFoundError: {fnf_error}")
        except UnidentifiedImageError:
            print(f"UnidentifiedImageError: The file at {image_path} is not a valid image or cannot be opened.")
        except Exception as e:
            print(f"An unexpected error occurred while processing the image: {e}")
    else:
        print("The image is not high resolution and will not be resized.")
    
    return None

# Add text with highlight word to Post360 (1080x1350) (old version)
def old_add_title_to_post(image, text, font_path, font_size, text_color,
                          align='left', margin=10, spacing=0, y_position=None,
                          highlight_word=None, highlight_color=None):
    # Convert hex color codes to RGB

    text_color = ImageColor.getrgb(text_color)
    if highlight_color:
        highlight_color = ImageColor.getrgb(highlight_color)

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    image_width, image_height = image.size
    max_text_width = image_width - 2 * margin

    # Wrap text based on available width

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        line_text = ' '.join(current_line)
        bbox = font.getbbox(line_text)
        line_width = bbox[2] - bbox[0]
        if line_width > max_text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Calculate total text block height

    text_height = sum([(font.getbbox(line)[3] - font.getbbox(line)[1]) + spacing for line in lines]) - spacing

    # Set vertical position

    y = y_position if y_position is not None else (image_height - text_height) // 2

    # Draw each line

    for line in lines:
        bbox_line = font.getbbox(line)
        line_width = bbox_line[2] - bbox_line[0]
        line_height = bbox_line[3] - bbox_line[1]

        # Horizontal alignment

        if align == 'left':
            x = margin
        elif align == 'center':
            x = (image_width - line_width) // 2
        elif align == 'right':
            x = image_width - line_width - margin
        else:
            raise ValueError("Invalid alignment value. Use 'left', 'center', or 'right'.")

        # Draw each word with optional highlight

        words_in_line = line.split()
        current_x = x
        for word in words_in_line:
            bbox_word = font.getbbox(word)
            word_width = bbox_word[2] - bbox_word[0]

            if highlight_word and word == highlight_word and highlight_color:
                draw.text((current_x, y), word, font=font, fill=highlight_color)
            else:
                draw.text((current_x, y), word, font=font, fill=text_color)

            # Add space width

            space_bbox = font.getbbox(' ')
            space_width = space_bbox[2] - space_bbox[0]
            current_x += word_width + space_width

        y += line_height + spacing

    return image

# Add text with highlight word to Post360 (1080x1350)

def add_title_to_post(
    image,
    text,
    font_path,
    font_size,
    text_color,
    align="left",
    margin=10,
    spacing=0,
    y_position=None,
    highlight_word=None,
    highlight_color=None,
    is_rtl=False,
):
    # Convert hex colors

    text_color = ImageColor.getrgb(text_color)
    if highlight_color:
        highlight_color = ImageColor.getrgb(highlight_color)

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    image_width, image_height = image.size
    max_text_width = image_width - 2 * margin

    # Wrap text

    words = text.split()
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        line_text = " ".join(current_line)
        line_width = font.getbbox(line_text)[2]

        if line_width > max_text_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    # RTL support

    if is_rtl:
        lines = [" ".join(line.split()[::-1]) for line in lines]

    # Use font metrics for consistent line height

    ascent, descent = font.getmetrics()
    line_height = ascent + descent

    # Total block height

    text_height = line_height * len(lines) + spacing * (len(lines) - 1)

    # Vertical positioning

    y = y_position if y_position is not None else (image_height - text_height) // 2

    # Draw lines

    for line in lines:
        line_width = font.getbbox(line)[2]

        # Horizontal alignment

        if align == "left":
            x = margin if not is_rtl else image_width - line_width - margin
        elif align == "center":
            x = (image_width - line_width) // 2
        elif align == "right":
            x = image_width - line_width - margin if not is_rtl else margin
        else:
            raise ValueError("Invalid alignment value")

        current_x = x

        for word in line.split():
            word_width = font.getbbox(word)[2]

            if (
                highlight_word
                and highlight_color
                and re.fullmatch(rf"{re.escape(word)}", highlight_word)
            ):
                draw.text((current_x, y), word, font=font, fill=highlight_color)
            else:
                draw.text((current_x, y), word, font=font, fill=text_color)

            space_width = font.getbbox(" ")[2]
            current_x += word_width + space_width

        # Consistent vertical advance

        y += line_height + spacing

    return image

# Create image file or generate preview

def create_post(image_source_path, image_output_path, image_width, image_height, crop_position,
                title, word, lang, title_size, title_spacing, title_color, word_color, mytag=None):
    # Checks

    logo_path = os.path.join(get_dir(), 'logo360/LogoP.png')
    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file '{logo_path}' not found.")

    if not os.access(os.path.dirname(image_output_path), os.W_OK) and image_output_path!="preview":
        raise PermissionError(f"Cannot write to the directory '{os.path.dirname(image_output_path)}'.")

    if not logo_path.lower().endswith('.png'):
        raise ValueError("The logo must be in PNG format.")
 
    # Open the image and logo

    if is_high_res(image_source_path):
        image = convert_to_hd(image_source_path)
    else:
        image = Image.open(image_source_path)

    logo = Image.open(logo_path)

    # Resize the image if smaller than desired dimensions

    if image.size[0] < image_width or image.size[1] < image_height:
        new_width = max(image_width, 1000)
        new_height = max(image_height, 1000)

        if image.size[0] < new_width:
            aspect_ratio = image.size[1] / image.size[0]
            new_width = image_width
            new_height = int(new_width * aspect_ratio)
        elif image.size[1] < new_height:
            aspect_ratio = image.size[0] / image.size[1]
            new_height = image_height
            new_width = int(new_height * aspect_ratio)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop the image

    if crop_position not in ['right', 'left', 'center']:
        raise ValueError("Invalid crop position. Choose either 'right', 'left', or 'center'.")
    if crop_position == 'right':
        image = image.crop((image.size[0] - image_width, 0, image.size[0], image_height))
    elif crop_position == 'left':
        image = image.crop((0, 0, image_width, image_height))
    elif crop_position == 'center':
        left = (image.size[0] - image_width) // 2
        top = (image.size[1] - image_height) // 2
        image = image.crop((left, top, left + image_width, top + image_height))

    # Resize to exact dimensions

    image = image.resize((image_width, image_height), Image.Resampling.LANCZOS)

    # Add gradient shadow

    sh_path = os.path.join(get_dir(), 'shadows/ShadowPS.png')
    if not os.path.isfile(sh_path):
        raise FileNotFoundError(f"The file '{sh_path}' does not exist.")
    if not os.access(sh_path, os.R_OK):
        raise PermissionError(f"The file '{sh_path}' cannot be read due to insufficient permissions.")
    shadowsb = Image.open(sh_path)
    image.paste(shadowsb, shadowsb if shadowsb.mode == 'RGBA' else None)

    # Paste the logo

    image.paste(logo, None, logo if logo.mode == 'RGBA' else None)

    # Add title text

    font_path = ''
    if lang == 'fr':
        font_path = os.path.join(get_dir(), 'fonts/DIN-Condensed-Bold.ttf')
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font file '{font_path}' not found.")
        add_title_to_post(image, title, font_path, title_size, title_color,
                          "center", 30, title_spacing, 980, word, word_color, is_rtl=False)
    elif lang == 'ar':
        font_path = os.path.join(get_dir(), 'fonts/ArbFONTS-Somar-Bold.otf')
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font file '{font_path}' not found.")
        add_title_to_post(image, title, font_path, title_size, title_color,
                          "center", 30, title_spacing, 920, word, word_color, is_rtl=True)
    else:
        raise ValueError("Language must be 'fr' or 'ar'.")

    # Add tag (Archive or Illustration)

    tag_map = {
        ("archive", "fr"): 'logo360/ARC.png',
        ("archive", "ar"): 'logo360/ARCAR.png',
        ("illustration", "fr"): 'logo360/IL.png',
        ("illustration", "ar"): 'logo360/ILAR.png'
    }
    if mytag in ["archive", "illustration"] and (mytag, lang) in tag_map:
        tag_path = os.path.join(get_dir(), tag_map[(mytag, lang)])
        if not os.path.isfile(tag_path):
            raise FileNotFoundError(f"The file '{tag_path}' does not exist.")
        if not os.access(tag_path, os.R_OK):
            raise PermissionError(f"The file '{tag_path}' cannot be read due to insufficient permissions.")
        itag = Image.open(tag_path)
        image.paste(itag, itag if itag.mode == 'RGBA' else None)

    # Preview mode
    if image_output_path == "preview":
            return image

    # Ensure output directory exists

    os.makedirs(image_output_path, exist_ok=True)
    output_path = os.path.join(image_output_path, "processed_image.jpeg")

    # Flatten RGBA to RGB with black background

    background_color = (0, 0, 0)  # background
    rgb_image = Image.new("RGB", image.size, background_color)
    rgb_image.paste(image, mask=image.split()[3])  # merge alpha channel

    # Save as JPEG

    rgb_image.save(output_path, format='JPEG', quality=100)

# Function to create footix image

def footix(image_source_path, image_output_path, crop_position):

    logo_path = os.path.join(get_dir(), 'logo360/Footix.png')

    # Checks

    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")

    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file '{logo_path}' not found.")

    if not logo_path.lower().endswith('.png'):
        raise ValueError("The logo must be in PNG format.")

    os.makedirs(image_output_path, exist_ok=True)

    if not os.access(image_output_path, os.W_OK):
        raise PermissionError(f"Cannot write to the directory '{image_output_path}'.")

    # Open image

    if is_high_res(image_source_path):
        image = convert_to_hd(image_source_path)
    else:
        image = Image.open(image_source_path)

    image = image.convert("RGBA")

    # Open logo

    logo = Image.open(logo_path).convert("RGBA")

    # Resize image if smaller than 1920x1080

    target_width, target_height = 1920, 1080

    if image.width < target_width or image.height < target_height:
        aspect_ratio = image.width / image.height

        if image.width < target_width:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Crop image

    if crop_position not in ['right', 'left', 'center']:
        raise ValueError("Invalid crop position. Choose 'right', 'left', or 'center'.")

    if crop_position == 'right':
        image = image.crop(
            (image.width - target_width, 0, image.width, target_height)
        )
    elif crop_position == 'left':
        image = image.crop(
            (0, 0, target_width, target_height)
        )
    else:  # center
        left = (image.width - target_width) // 2
        top = (image.height - target_height) // 2
        image = image.crop(
            (left, top, left + target_width, top + target_height)
        )

    # Paste logo

    image.paste(logo, (0, 0), logo)

    # Flatten RGBA to RGB with black background
    
    background_color = (0, 0, 0)
    rgb_image = Image.new("RGB", image.size, background_color)
    rgb_image.paste(image, mask=image.split()[3])

    # Save output

    output_path = os.path.join(image_output_path, "footix.jpg")
    rgb_image.save(output_path, format="JPEG", quality=100)

