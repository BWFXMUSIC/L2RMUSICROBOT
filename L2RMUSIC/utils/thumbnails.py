import asyncio
import os
import random
import re
import aiofiles
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter,
                 ImageFont, ImageOps)
from youtubesearchpython import VideosSearch  # Fixed import
import numpy as np
from config import YOUTUBE_IMG_URL


# Helper function to generate random colors
def make_col():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


# Function to resize the image while maintaining the aspect ratio
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


# Function to truncate text into two parts for better readability
def truncate(text):
    words = text.split(" ")
    text1 = ""
    text2 = ""
    for word in words:
        if len(text1) + len(word) < 30:
            text1 += " " + word
        elif len(text2) + len(word) < 30:
            text2 += " " + word

    return [text1.strip(), text2.strip()]


# Main function to download and process the YouTube thumbnail
async def get_thumb(videoid):
    try:
        # Check if cached image already exists
        if os.path.isfile(f"cache/{videoid}.jpg"):
            return f"cache/{videoid}.jpg"

        # Perform a YouTube search to get the thumbnail
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)

        # Extract data from search results
        for result in (await results.next())["result"]:
            title = re.sub("\W+", " ", result.get("title", "Unsupported Title")).title()
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Fetch thumbnail image asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://img.youtube.com/vi/{videoid}/maxresdefault.jpg") as resp:
                if resp.status == 200:
                    cache_path = f"cache/thumb{videoid}.jpg"
                    async with aiofiles.open(cache_path, mode="wb") as f:
                        await f.write(await resp.read())

        # Open and process the image
        youtube = Image.open(f"cache/thumb{videoid}.jpg")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")

        # Apply a background blur effect
        background = image2.filter(filter=ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        image2 = background

        # Load and change circle color
        circle = Image.open("L2RMUSIC/assets/circle.png").convert('RGBA')
        color = make_col()

        # Change the circle color by replacing the white areas
        data = np.array(circle)
        red, green, blue, alpha = data.T
        white_areas = (red == 255) & (blue == 255) & (green == 255)
        data[..., :-1][white_areas.T] = color
        circle = Image.fromarray(data)

        # Crop the image to add the thumbnail in a specific area
        image3 = image1.crop((280, 0, 1000, 720))
        lum_img = Image.new('L', [720, 720], 0)
        draw = ImageDraw.Draw(lum_img)
        draw.pieslice([(0, 0), (720, 720)], 0, 360, fill=255, outline="white")

        # Combine the cropped image and luminosity image
        img_arr = np.array(image3)
        lum_img_arr = np.array(lum_img)
        final_img_arr = np.dstack((img_arr, lum_img_arr))
        image3 = Image.fromarray(final_img_arr)
        image3 = image3.resize((600, 600))

        # Paste the processed images onto the final image
        image2.paste(image3, (50, 70), mask=image3)
        image2.paste(circle, (0, 0), mask=circle)

        # Set fonts for text
        font1 = ImageFont.truetype('L2RMUSIC/assets/font.ttf', 30)
        font2 = ImageFont.truetype('L2RMUSIC/assets/font2.ttf', 70)
        font3 = ImageFont.truetype('L2RMUSIC/assets/font2.ttf', 40)
        font4 = ImageFont.truetype('L2RMUSIC/assets/font2.ttf', 35)

        # Draw text on the image
        image4 = ImageDraw.Draw(image2)
        image4.text((10, 10), "L2R MUSIC", fill="white", font=font1, align="left")
        image4.text((670, 150), "NOW PLAYING", fill="white", font=font2, stroke_width=2, stroke_fill="white", align="left")

        # Truncate and draw the title text
        title1 = truncate(title)
        image4.text((670, 300), text=title1[0], fill="white", stroke_width=1, stroke_fill="white", font=font3, align="left")
        image4.text((670, 350), text=title1[1], fill="white", stroke_width=1, stroke_fill="white", font=font3, align="left")

        # Add video details like views, duration, and channel
        image4.text((670, 450), text=f"Views: {views}", fill="white", font=font4, align="left")
        image4.text((670, 500), text=f"Duration: {duration}", fill="white", font=font4, align="left")
        image4.text((670, 550), text=f"Channel: {channel}", fill="white", font=font4, align="left")

        # Add border around the image
        image2 = ImageOps.expand(image2, border=20, fill=make_col())
        image2 = image2.convert('RGB')

        # Save the final image and return the file path
        image2.save(f"cache/{videoid}.jpg")
        return f"cache/{videoid}.jpg"

    except Exception as e:
        print(f"Error occurred: {e}")
        return YOUTUBE_IMG_URL  # Ensure this is defined in your config
