#!/usr/bin/python3

#Created by marwa BIFISSE with the help of Chatgpt, the enemy of humanity

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageColor, UnidentifiedImageError #some function to manipulate images using Pillow 
import os # this will allow me to manipulate dirs and files
import re
from files import get_dir #instead of using os.cwd, i created this function to return full path of executed script, so i can load elements correctly

#get image resolution
def get_image_resolution(image_path):
        # Check if file exists and is readable
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"The file '{image_path}' does not exist.")
    if not os.access(image_path, os.R_OK):
        raise PermissionError(f"The file '{image_path}' cannot be read due to insufficient permissions.")
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height

# Create a gradient shadow image.
def create_gradient_shadow_bottom(width, shadow_height):
    # Create the shadow image with an RGBA mode
    shadow = Image.new('RGBA', (width, shadow_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    # Create the gradient shadow
    for y in range(shadow_height):
        alpha = int(255 * (y / shadow_height))  # Opaque at the top, transparent at the bottom
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    # Reduce the opacity of the entire shadow by 50%
    shadow = shadow.convert('RGBA')
    shadow_with_reduced_opacity = Image.new('RGBA', shadow.size)
    for x in range(shadow.width):
        for y in range(shadow.height):
            r, g, b, a = shadow.getpixel((x, y))
            a = int(a * 0.5)  # Reduce opacity by 50%
            shadow_with_reduced_opacity.putpixel((x, y), (r, g, b, a))
    
    return shadow_with_reduced_opacity

def create_gradient_shadow_top(width, shadow_height):
    # Create the shadow image with an RGBA mode
    shadow = Image.new('RGBA', (width, shadow_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    # Create the gradient shadow from top (opaque) to bottom (transparent)
    for y in range(shadow_height):
        alpha = int(255 * ((shadow_height - y) / shadow_height))  # Opaque at the top, transparent at the bottom
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha)) #i think here where i can change color of shadow
    
    # Reduce the opacity of the entire shadow by 50%
    shadow = shadow.convert('RGBA')
    shadow_with_reduced_opacity = Image.new('RGBA', shadow.size)
    for x in range(shadow.width):
        for y in range(shadow.height):
            r, g, b, a = shadow.getpixel((x, y))
            a = int(a * 0.5)  # Reduce opacity by 50%
            shadow_with_reduced_opacity.putpixel((x, y), (r, g, b, a))
    
    return shadow_with_reduced_opacity

#Function to crop image to specific size and add logo (if it's value not empty) and arrow (if image is rectangle)
def add_logo_to_image(image_source_path, logo_path, image_output_path, logo_position, image_width, image_height, crop_position, logo_margin, logo_decrease_percent, arrow_path=None, arrow_position='bottom-right', logo_opacity=None,square=None, city=None, imageone=None, title=None, lang=None):
    # Check if the image source and logo files exist
    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")
    if logo_path:
        if not os.path.isfile(logo_path):
            raise FileNotFoundError(f"Logo file '{logo_path}' not found.")
    
    if arrow_path:
        if not os.path.isfile(arrow_path):
            raise FileNotFoundError(f"Arrow file '{arrow_path}' not found.")
        if not arrow_path.lower().endswith('.png'):
            raise ValueError("The arrow must be in PNG format.")
    
    if not os.access(os.path.dirname(image_output_path), os.W_OK):
        raise PermissionError(f"Cannot write to the directory '{os.path.dirname(image_output_path)}'.")
    if logo_path:
        if not logo_path.lower().endswith('.png'):
            raise ValueError("The logo must be in PNG format.")
    
    # Open the image and logo, if image is HighRes, we should lower size to proprely crop the image
    if is_high_res(image_source_path):
        image=convert_to_hd(image_source_path)
    else:
        image = Image.open(image_source_path)
    if logo_path:
        logo = Image.open(logo_path)
    
    # Resize the image if it's smaller than specified dimensions
    if image.size[0] < image_width or image.size[1] < image_height:
        # Calculate new dimensions
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
        
        image = image.resize((new_width, new_height), Image.ANTIALIAS)
    
    # Crop the image to the specified dimensions
    if crop_position in ['right', 'left', 'center']:
        if crop_position == 'right':
            image = image.crop((image.size[0] - image_width, 0, image.size[0], image_height))
        elif crop_position == 'left':
            image = image.crop((0, 0, image_width, image_height))
        elif crop_position == 'center':
            left = (image.size[0] - image_width) // 2
            top = (image.size[1] - image_height) // 2
            image = image.crop((left, top, left + image_width, top + image_height))
    else:
        raise ValueError("Invalid crop position. Choose either 'right', 'left', or 'center'.")
    
    # Resize the image to match the specified dimensions (if needed)
    image = image.resize((image_width, image_height), Image.ANTIALIAS)

     # Add gradient shadow to the bottom of the image (gradient file or draw it)
    if image_height==1080 and image_width==1080:
        sh_path=os.path.join(get_dir(),'shadows/ShadowSB.png')
        # Check if file exists and is readable
        if not os.path.isfile(sh_path):
            raise FileNotFoundError(f"The file '{sh_path}' does not exist.")
        if not os.access(sh_path, os.R_OK):
            raise PermissionError(f"The file '{sh_path}' cannot be read due to insufficient permissions.")
        shadowsb = Image.open(sh_path)
        image.paste(shadowsb , shadowsb if shadowsb.mode == 'RGBA' else None)
    elif image_height==1350 and image_width==1080:
        sh_path=os.path.join(get_dir(),'shadows/ShadowT.png')
        # Check if file exists and is readable
        if not os.path.isfile(sh_path):
            raise FileNotFoundError(f"The file '{sh_path}' does not exist.")
        if not os.access(sh_path, os.R_OK):
            raise PermissionError(f"The file '{sh_path}' cannot be read due to insufficient permissions.")
        shadowsb = Image.open(sh_path)
        image.paste(shadowsb , shadowsb if shadowsb.mode == 'RGBA' else None)
    else:
        shadow_height = int(image_height * 0.1)  # Shadow height can be adjusted as needed
        shadow = create_gradient_shadow_bottom(image_width, shadow_height)
        image.paste(shadow, (0, image_height - shadow_height), shadow)

    #if image is 1080x1080 and fist one in Diapo, add title for 1st image in slide
    if square=='on' and imageone==0 and image_height==1080 and image_width==1080:
        # Add gradient shadow to the top of the image
        shadow_height = int(image_height * 0.6)  # Adjust shadow height as needed
        shadow = create_gradient_shadow_top(image_width, shadow_height)
        image.paste(shadow, (0, 0), shadow)

    if logo_path:

        # Validate the logo decrease percentage
        if logo_decrease_percent < 0 or logo_decrease_percent > 90:
            raise ValueError("The logo decrease percentage must be between 0 and 90.")
        
        # Calculate the new logo size after decreasing
        decrease_factor = (100 - logo_decrease_percent) / 100
        new_logo_width = int(logo.size[0] * decrease_factor)
        new_logo_height = int(logo.size[1] * decrease_factor)
        
        # Resize the logo to the decreased size
        logo = logo.resize((new_logo_width, new_logo_height), Image.ANTIALIAS)
        
        # Ensure the logo size plus margins fits within the image
        if new_logo_width + 2 * logo_margin > image_width or new_logo_height + 2 * logo_margin > image_height:
            raise ValueError("The logo with margins cannot be larger than the image size.")
        
        # Apply opacity to the logo if specified
        if logo_opacity is not None:
            if not (0 <= logo_opacity <= 255):
                raise ValueError("Opacity must be between 0 (fully transparent) and 255 (fully opaque).")
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Adjust the opacity
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: p * (logo_opacity / 255.0))
            logo.putalpha(alpha)
        
        # Calculate the position to place the logo considering the margin
        if logo_position == 'top-left':
            logo_position = (logo_margin, logo_margin)
        elif logo_position == 'top-right':
            logo_position = (image.size[0] - new_logo_width - logo_margin, logo_margin)
        elif logo_position == 'bottom-left':
            logo_position = (logo_margin, image.size[1] - new_logo_height - logo_margin)
        elif logo_position == 'bottom-right':
            logo_position = (image.size[0] - new_logo_width - logo_margin, image.size[1] - new_logo_height - logo_margin)
        elif logo_position == 'center':
            logo_position = ((image.size[0] - new_logo_width) // 2, (image.size[1] - new_logo_height) // 2)
        elif logo_position == 'top-center':
            logo_position = ((image.size[0] - new_logo_width) // 2, logo_margin)
        elif logo_position == 'bottom-center':
            logo_position = ((image.size[0] - new_logo_width) // 2, image.size[1] - new_logo_height - logo_margin)
        else:
            raise ValueError("Invalid logo position. Choose either 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center', 'top-center', or 'bottom-center'.")

        # Paste the logo onto the cropped image
        image.paste(logo, logo_position, logo if logo.mode == 'RGBA' else None)
    else:
        # Validate the logo decrease percentage
        if logo_decrease_percent < 0 or logo_decrease_percent > 90:
            raise ValueError("The logo decrease percentage must be between 0 and 90.")
        
        # Calculate decrease factor for arrow
        decrease_factor = (100 - logo_decrease_percent) / 100

    #if size is 1080x1080 and 1st image draw title and logo title logo
    if square=='on' and imageone==0 and image_width==1080 and image_height==1080:
        sh_path=os.path.join(get_dir(),'shadows/ShadowST.png')
        # Check if file exists and is readable
        if not os.path.isfile(sh_path):
            raise FileNotFoundError(f"The file '{sh_path}' does not exist.")
        if not os.access(sh_path, os.R_OK):
            raise PermissionError(f"The file '{sh_path}' cannot be read due to insufficient permissions.")
        # Open the image
        ltitle = Image.open(sh_path)
        #paste image
        image.paste(ltitle, ltitle if ltitle.mode == 'RGBA' else None)

        st_path=os.path.join(get_dir(),'logo360/LogoTitle.png')
        # Check if file exists and is readable
        if not os.path.isfile(st_path):
            raise FileNotFoundError(f"The file '{st_path}' does not exist.")
        if not os.access(st_path, os.R_OK):
            raise PermissionError(f"The file '{st_path}' cannot be read due to insufficient permissions.")
        # Open the image        
        ltitle=Image.open(st_path)
        #paste image
        image.paste(ltitle, ltitle if ltitle.mode == 'RGBA' else None)

        if lang=='fr':

            #font selection
            font_path=os.path.join(get_dir(),'fonts/DIN-Condensed-Bold.ttf')
            font_size=100
            if not os.path.isfile(font_path):
                raise FileNotFoundError(f"Font file '{font_path}' not found.")

            # Load the font
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError as e:
                raise IOError(f"Could not load font '{font_path}': {e}")
            add_title_to_image(image,title,font_path,font_size,'white','center',50,30,120)

        elif lang=='ar':

            #font selection
            font_size=100
            font_path=os.path.join(get_dir(),'fonts/ArbFONTS-Somar-Bold.otf')
            if not os.path.isfile(font_path):
                raise FileNotFoundError(f"Font file '{font_path}' not found.")

            # Load the font
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError as e:
                raise IOError(f"Could not load font '{font_path}': {e}")
            add_title_to_image(image,title,font_path,font_size,'white','center',50,-10,80)
    
    # Optionally add an arrow
    if arrow_path:
        arrow = Image.open(arrow_path)
        if not arrow_path.lower().endswith('.png'):
            raise ValueError("The arrow must be in PNG format.")
        
        # Calculate the new arrow size after decreasing
        arrow_width = int(arrow.size[0] * decrease_factor)
        arrow_height = int(arrow.size[1] * decrease_factor)
        arrow = arrow.resize((arrow_width, arrow_height), Image.ANTIALIAS)
        
        # Apply opacity to the arrow if specified
        if logo_opacity is not None:
            if arrow.mode != 'RGBA':
                arrow = arrow.convert('RGBA')
            
            # Adjust the opacity
            alpha = arrow.split()[3]
            alpha = alpha.point(lambda p: p * (logo_opacity / 255.0))
            arrow.putalpha(alpha)
        
        # Calculate the position to place the arrow considering the margin
        if arrow_position == 'top-left':
            arrow_position = (logo_margin, logo_margin)
        elif arrow_position == 'top-right':
            arrow_position = (image.size[0] - arrow_width - logo_margin, logo_margin)
        elif arrow_position == 'bottom-left':
            arrow_position = (logo_margin, image.size[1] - arrow_height - logo_margin)
        elif arrow_position == 'bottom-right':
            arrow_position = (image.size[0] - arrow_width - logo_margin, image.size[1] - arrow_height - logo_margin)
        else:
            raise ValueError("Invalid arrow position. Choose either 'top-left', 'top-right', 'bottom-left', or 'bottom-right'.")
        
        # Paste the arrow onto the image
        image.paste(arrow, arrow_position, arrow if arrow.mode == 'RGBA' else None)

    #if size is 1080x1080 draw city text
    if square=='on' and image_width==1080 and image_height==1080:
        if city!='':
            sep_path=os.path.join(get_dir(),'logo360/LogoSep.png')
            # Check if file exists and is readable
            if not os.path.isfile(sep_path):
                raise FileNotFoundError(f"The file '{sep_path}' does not exist.")
            if not os.access(sep_path, os.R_OK):
                raise PermissionError(f"The file '{sep_path}' cannot be read due to insufficient permissions.")
            # Open the image
            sep = Image.open(sep_path)
            #paste image
            image.paste(sep, sep if sep.mode == 'RGBA' else None)

        if lang=='fr' and city!='':
            #font selection
            font_size=53
            font_path=os.path.join(get_dir(),'fonts/DIN-Condensed-Bold.ttf')
       
            if not os.path.isfile(font_path):
                raise FileNotFoundError(f"Font file '{font_path}' not found.")

            # Load the font
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError as e:
                raise IOError(f"Could not load font '{font_path}': {e}")
            myfont = ImageFont.truetype(font_path,font_size)
            draw = ImageDraw.Draw(image)
            draw.text((160, 1010), city, font=myfont, fill='white')
        elif lang=='ar' and city!='':
            #font selection
            font_size=53
            font_path=os.path.join(get_dir(),'fonts/ArbFONTS-Somar-Bold.otf')
       
            if not os.path.isfile(font_path):
                raise FileNotFoundError(f"Font file '{font_path}' not found.")

            # Load the font
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError as e:
                raise IOError(f"Could not load font '{font_path}': {e}")
            myfont = ImageFont.truetype(font_path,font_size)
            draw = ImageDraw.Draw(image)
            draw.text((160, 995), city, font=myfont, fill='white')

        # draw.text((160, 1010), city, font=myfont, fill='white') ar version

    # Save the output image
    image.save(image_output_path)

#batch process multiple images
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
        output_path = os.path.join(image_output_dir, f"processed_image_{i + 1}.png")
        
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

#For 1080x1080, function to align text to center
def add_title_to_image(image, text, font_path, font_size, text_color, align='left', margin=10, spacing=0, y_position=None):
    # Draw on the provided image
    draw = ImageDraw.Draw(image)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Image dimensions
    image_width, image_height = image.size

    # Calculate available width for text after applying margins
    max_text_width = image_width - 2 * margin

    # Calculate text height to position it vertically, considering y_position if provided
    lines = []
    words = text.split()
    current_line = []

    # Wrap text based on available width
    for word in words:
        current_line.append(word)
        w, h = draw.textsize(' '.join(current_line), font=font)
        if w > max_text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Calculate the total height of the text block with spacing
    text_height = sum([draw.textsize(line, font=font)[1] + spacing for line in lines]) - spacing

    # Set vertical position
    if y_position is not None:
        y = y_position
    else:
        y = (image_height - text_height) // 2  # Vertical center

    # Draw each line on the image
    for line in lines:
        line_width, line_height = draw.textsize(line, font=font)

        # Calculate x position based on alignment
        if align == 'left':
            x = margin
        elif align == 'center':
            x = (image_width - line_width) // 2
        elif align == 'right':
            x = image_width - line_width - margin
        else:
            raise ValueError("Invalid alignment value. Use 'left', 'center', or 'right'.")

        # Validate x position
        if x < 0 or x > image_width - line_width:
            raise ValueError("Calculated x position is out of image bounds.")

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

#This function is used to respect the aspect ratio
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

#If image is HighRes, it will be converted to HD
def convert_to_hd(image_path, max_width=1920, max_height=1080):
    if is_high_res(image_path):
        try:
            with Image.open(image_path) as img:
                # Calculate the new dimensions while maintaining the aspect ratio
                new_width, new_height = calculate_new_dimensions(img.width, img.height, max_width, max_height)
                
                # Resize the image
                img_hd = img.resize((new_width, new_height), Image.ANTIALIAS)
                
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

#Function to add text with highlight word to Post (1080x1350)
def old_add_title_to_post(image, text, font_path, font_size, text_color, align='left', margin=10, spacing=0, y_position=None, highlight_word=None, highlight_color=None):
    # Convert hex color codes to RGB
    text_color = ImageColor.getrgb(text_color)
    if highlight_color:
        highlight_color = ImageColor.getrgb(highlight_color)

    # Draw on the provided image
    draw = ImageDraw.Draw(image)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Image dimensions
    image_width, image_height = image.size

    # Calculate available width for text after applying margins
    max_text_width = image_width - 2 * margin

    # Calculate text height to position it vertically, considering y_position if provided
    lines = []
    words = text.split()
    current_line = []

    # Wrap text based on available width
    for word in words:
        current_line.append(word)
        w, h = draw.textsize(' '.join(current_line), font=font)
        if w > max_text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Calculate the total height of the text block with spacing
    text_height = sum([draw.textsize(line, font=font)[1] + spacing for line in lines]) - spacing

    # Set vertical position
    if y_position is not None:
        y = y_position
    else:
        y = (image_height - text_height) // 2  # Vertical center

    # Draw each line on the image
    for line in lines:
        line_width, line_height = draw.textsize(line, font=font)

        # Calculate x position based on alignment
        if align == 'left':
            x = margin
        elif align == 'center':
            x = (image_width - line_width) // 2
        elif align == 'right':
            x = image_width - line_width - margin
        else:
            raise ValueError("Invalid alignment value. Use 'left', 'center', or 'right'.")

        # Validate x position
        if x < 0 or x > image_width - line_width:
            raise ValueError("Calculated x position is out of image bounds.")

        # Draw the line with highlight if necessary
        words_in_line = line.split()
        current_x = x
        for word in words_in_line:
            word_width, _ = draw.textsize(word, font=font)
            # Check if this word should be highlighted
            if word == highlight_word and highlight_color:
                draw.text((current_x, y), word, font=font, fill=highlight_color)
            else:
                draw.text((current_x, y), word, font=font, fill=text_color)
            current_x += word_width + draw.textsize(' ', font=font)[0]  # Adding space width

        y += line_height + spacing

    return image

def add_title_to_post(image, text, font_path, font_size, text_color, align='left', margin=10, spacing=0, y_position=None, highlight_word=None, highlight_color=None, is_rtl=False):
    # Convert hex color codes to RGB
    text_color = ImageColor.getrgb(text_color)
    if highlight_color:
        highlight_color = ImageColor.getrgb(highlight_color)

    # Draw on the provided image
    draw = ImageDraw.Draw(image)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Image dimensions
    image_width, image_height = image.size

    # Calculate available width for text after applying margins
    max_text_width = image_width - 2 * margin

    # Wrap text based on available width
    lines = []
    words = text.split()
    current_line = []

    for word in words:
        current_line.append(word)
        w, h = draw.textsize(' '.join(current_line), font=font)
        if w > max_text_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Reverse the order of words in each line for RTL support
    if is_rtl:
        lines = [line.split()[::-1] for line in lines]  # Reverse words in each line
        lines = [' '.join(line) for line in lines]  # Rejoin words into lines

    # Calculate the total height of the text block with spacing
    text_height = sum([draw.textsize(line, font=font)[1] + spacing for line in lines]) - spacing

    # Set vertical position
    if y_position is not None:
        y = y_position
    else:
        y = (image_height - text_height) // 2  # Vertical center

    # Draw each line on the image
    for line in lines:
        line_width, line_height = draw.textsize(line, font=font)

        # Calculate x position based on alignment
        if align == 'left':
            x = margin if not is_rtl else image_width - line_width - margin
        elif align == 'center':
            x = (image_width - line_width) // 2
        elif align == 'right':
            x = image_width - line_width - margin if not is_rtl else margin
        else:
            raise ValueError("Invalid alignment value. Use 'left', 'center', or 'right'.")

        # Validate x position
        if x < 0 or x > image_width - line_width:
            raise ValueError("Calculated x position is out of image bounds.")

        # Draw the line with highlight if necessary
        words_in_line = line.split()
        current_x = x
        for word in words_in_line:
            word_width, _ = draw.textsize(word, font=font)

            # Check if this word should be highlighted
            if re.search(rf"\b{re.escape(word)}\b", highlight_word) and highlight_color:
                draw.text((current_x, y), word, font=font, fill=highlight_color)
            else:
                draw.text((current_x, y), word, font=font, fill=text_color)
            current_x += word_width + draw.textsize(' ', font=font)[0]  # Adding space width

        y += line_height + spacing

    return image

#Function to create post 1080x1350
def create_post(image_source_path, image_output_path, image_width, image_height, crop_position, title, word, lang, title_size, title_spacing, title_color,word_color, mytag=None):
    # Check if the image source and logo files exist
    logo_path=os.path.join(get_dir(),'logo360/LogoP.png')
    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file '{logo_path}' not found.")

    if not os.access(os.path.dirname(image_output_path), os.W_OK):
        raise PermissionError(f"Cannot write to the directory '{os.path.dirname(image_output_path)}'.")

    if not logo_path.lower().endswith('.png'):
        raise ValueError("The logo must be in PNG format.")

    # Open the image and logo, if image is HighRes, we should lower size to proprely crop the image
    if is_high_res(image_source_path):
        image=convert_to_hd(image_source_path)
    else:
        image = Image.open(image_source_path)

    logo = Image.open(logo_path)

    # Resize the image if it's smaller than specified dimensions
    if image.size[0] < image_width or image.size[1] < image_height:
        # Calculate new dimensions
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

        image = image.resize((new_width, new_height), Image.ANTIALIAS)

    # Crop the image to the specified dimensions
    if crop_position in ['right', 'left', 'center']:
        if crop_position == 'right':
            image = image.crop((image.size[0] - image_width, 0, image.size[0], image_height))
        elif crop_position == 'left':
            image = image.crop((0, 0, image_width, image_height))
        elif crop_position == 'center':
            left = (image.size[0] - image_width) // 2
            top = (image.size[1] - image_height) // 2
            image = image.crop((left, top, left + image_width, top + image_height))
    else:
        raise ValueError("Invalid crop position. Choose either 'right', 'left', or 'center'.")

    # Resize the image to match the specified dimensions (if needed)
    image = image.resize((image_width, image_height), Image.ANTIALIAS)

     # Add gradient shadow to the bottom of the image (gradient file or draw it)
    sh_path=os.path.join(get_dir(),'shadows/ShadowPS.png')
    # Check if file exists and is readable
    if not os.path.isfile(sh_path):
        raise FileNotFoundError(f"The file '{sh_path}' does not exist.")
    if not os.access(sh_path, os.R_OK):
        raise PermissionError(f"The file '{sh_path}' cannot be read due to insufficient permissions.")
    shadowsb = Image.open(sh_path)
    image.paste(shadowsb , shadowsb if shadowsb.mode == 'RGBA' else None)

    # Paste the logo onto the cropped image
    image.paste(logo, None, logo if logo.mode == 'RGBA' else None)
    font_path=''
    if lang=='fr':
        font_path=os.path.join(get_dir(),'fonts/DIN-Condensed-Bold.ttf')
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font file '{font_path}' not found.")
        #add_title_to_post(image,title,font_path,title_size,title_color,"center",0,title_spacing,980,word,word_color)
        add_title_to_post(image,title,font_path,title_size,title_color,"center",30,title_spacing,980,word,word_color,False)

    elif lang=='ar':
        font_path=os.path.join(get_dir(),'fonts/ArbFONTS-Somar-Bold.otf')

        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font file '{font_path}' not found.")
        add_title_to_post(image,title,font_path,title_size,title_color,"center",30,title_spacing,920,word,word_color,True)
    else:
        raise ValueError("Must be fr or fr")
    
    #add tag (Archive or Illustration)
    if mytag=="archive" and lang=="fr":
        tag_path=os.path.join(get_dir(),'logo360/ARC.png')
        # Check if file exists and is readable
        if not os.path.isfile(tag_path):
            raise FileNotFoundError(f"The file '{tag_path}' does not exist.")
        if not os.access(tag_path, os.R_OK):
            raise PermissionError(f"The file '{tag_path}' cannot be read due to insufficient permissions.")
        # Open the image
        itag = Image.open(tag_path)
        #paste image
        image.paste(itag, itag if itag.mode == 'RGBA' else None)
    elif mytag=="archive" and lang=="ar":
        tag_path=os.path.join(get_dir(),'logo360/ARCAR.png')
        # Check if file exists and is readable
        if not os.path.isfile(tag_path):
            raise FileNotFoundError(f"The file '{tag_path}' does not exist.")
        if not os.access(tag_path, os.R_OK):
            raise PermissionError(f"The file '{tag_path}' cannot be read due to insufficient permissions.")
        # Open the image
        itag = Image.open(tag_path)
        #paste image
        image.paste(itag, itag if itag.mode == 'RGBA' else None)
    elif mytag=="illustration" and lang=="fr":
        tag_path=os.path.join(get_dir(),'logo360/IL.png')
        # Check if file exists and is readable
        if not os.path.isfile(tag_path):
            raise FileNotFoundError(f"The file '{tag_path}' does not exist.")
        if not os.access(tag_path, os.R_OK):
            raise PermissionError(f"The file '{tag_path}' cannot be read due to insufficient permissions.")
        # Open the image
        itag = Image.open(tag_path)
        #paste image
        image.paste(itag, itag if itag.mode == 'RGBA' else None)
    elif mytag=="illustration" and lang=="ar":
        tag_path=os.path.join(get_dir(),'logo360/ILAR.png')
        # Check if file exists and is readable
        if not os.path.isfile(tag_path):
            raise FileNotFoundError(f"The file '{tag_path}' does not exist.")
        if not os.access(tag_path, os.R_OK):
            raise PermissionError(f"The file '{tag_path}' cannot be read due to insufficient permissions.")
        # Open the image
        itag = Image.open(tag_path)
        #paste image
        image.paste(itag, itag if itag.mode == 'RGBA' else None)

    # Ensure the output directory exists
    if not os.path.exists(image_output_path):
        os.makedirs(image_output_path)

    output_path = os.path.join(image_output_path, f"processed_image.png")

    # Save the output image
    image.save(output_path)

#Function to create footix
def footix (image_source_path, image_output_path, crop_position):

    logo_path=os.path.join(get_dir(),'logo360/Footix.png')

    # Check if the image source and logo files exist
    if not os.path.isfile(image_source_path):
        raise FileNotFoundError(f"Image source file '{image_source_path}' not found.")
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file '{logo_path}' not found.")
    if not os.access(os.path.dirname(image_output_path), os.W_OK):
        raise PermissionError(f"Cannot write to the directory '{os.path.dirname(image_output_path)}'.")
    if not logo_path.lower().endswith('.png'):
        raise ValueError("The logo must be in PNG format.")
    # Open the image and logo, if image is HighRes, we should lower size to proprely crop the image
    if is_high_res(image_source_path):
        image=convert_to_hd(image_source_path)
    else:
        image = Image.open(image_source_path)

    logo = Image.open(logo_path)

    # Resize the image if it's smaller than specified dimensions
    if image.size[0] < 1920 or image.size[1] < 1080:
        # Calculate new dimensions
        new_width = max(1920, 1000)
        new_height = max(1080, 1000)
        
        if image.size[0] < new_width:
            aspect_ratio = image.size[1] / image.size[0]
            new_height = int(1920 * aspect_ratio)
        elif image.size[1] < new_height:
            aspect_ratio = image.size[0] / image.size[1]
            new_width = int(1080 * aspect_ratio)
        
        image = image.resize((new_width, new_height), Image.ANTIALIAS)

    # Crop the image to the specified dimensions
    if crop_position in ['right', 'left', 'center']:
        if crop_position == 'right':
            image = image.crop((image.size[0] - 1920, 0, image.size[0], 1080))
        elif crop_position == 'left':
            image = image.crop((0, 0, 1920, 1080))
        elif crop_position == 'center':
            left = (image.size[0] - 1920) // 2
            top = (image.size[1] - 1080) // 2
            image = image.crop((left, top, left + 1920, top + 1080))
        else:
            raise ValueError("Invalid crop position. Choose either 'right', 'left', or 'center'.")
        
    image.paste(logo, logo if logo.mode == 'RGBA' else None)
    image_output=os.path.join(image_output_path, "footix.png")

    # Save the output image
    image.save(image_output)