import logging
import os
import uuid

import aiohttp

from llm_workers.models_server.utils import upload_file_to_s3_binary

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def download_image(image_url: str) -> str:
    # Extract the filename from the image URL
    filename = os.path.basename(image_url)
    # Ensure it has a .jpg extension
    if not filename.endswith('.jpg'):
        filename = f"{filename}.jpg"

    # Define the path where the image will be saved
    filepath = os.path.join('input', filename)

    # Create the directory if it doesn't exist
    os.makedirs('input', exist_ok=True)

    if not os.path.exists(filepath):
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f'Failed to download image from {image_url}')
                with open(filepath, 'wb') as f:
                    f.write(await response.read())

    return filepath.replace('input/', '')


async def generate_and_upload_image(image1_url: str, image2_url: str, model) -> str:
    image1_filename = await download_image(image1_url)
    image2_filename = await download_image(image2_url)
    output_filename = f"{uuid.uuid4()}"
    model.generate_image(image1_filename, image2_filename, output_filename)

    with open(f"./output/{output_filename}_00001_.png", 'rb') as f:
        image_bytes = f.read()

    s3_file_name = f"generated_images/{output_filename}.png"
    s3_url = upload_file_to_s3_binary(image_bytes, s3_file_name)
    return s3_url
