import asyncio
import os
import logging
import uuid
import re

from typing import Optional

import httpx
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

from season_pass_invite.config import SYS_KEY, API_URL
from season_pass_invite.dall_e_generate_descriptive_prompt import describe_image_with_openai_vision, \
    name_description_based_of_vision_description
from season_pass_invite.utils import upload_file_to_s3_binary

from season_pass_invite.gen_img import BlendImagesProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables to configure the script
TOPIC_NAME = os.getenv('TOPIC_NAME', "comfy_season_blend")
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://demo:demo@localhost:8080/engine-rest')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'pixelpact')

# Logging the script startup
logging.info("Starting Image Generation Worker")

# Configuration for the Camunda External Task Client
default_config = {
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 10
}

model = BlendImagesProcessor()

async def fetch_image_url(art_id: str) -> Optional[str]:
    async with httpx.AsyncClient() as _client:
        headers = {
            "X-SYS-KEY": SYS_KEY
        }
        response = await _client.get(f"{API_URL}/arts/{art_id}", headers=headers)
        if response.status_code == 200:
            art = response.json()
            logging.info(f"art: {art}")
            art_url = art['img_picture']
            return art_url
        else:
            logging.error(f"Failed to fetch art with ID {art_id}")
            return None


def check_if_image_exists(art_id: str) -> Optional[str]:
    """Check if an image with the given art_id already exists in the local temporary directory."""
    tmp_dir = "./tmp"
    for filename in os.listdir(tmp_dir):
        if filename.startswith(art_id):
            return os.path.join(tmp_dir, filename)
    return None


async def download_image(image_url: str, art_id: str) -> str:
    filename = f"{art_id}.jpg"
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        with open(f"./input/{filename}", 'wb') as f:
            f.write(response.content)
    return filename


async def post_art_details(img_art_thumbnail: str, art_details: dict) -> None:
    """Post the art details to the API."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-SYS-KEY": os.getenv('X_SYS_KEY', SYS_KEY)
        }
        art_details["img_picture"] = img_art_thumbnail

        response = await client.post(f"{API_URL}/art", json=art_details, headers=headers)
        if response.status_code >= 400:
            error_msg = f"HTTP error response: {response.status_code} {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)

        logging.info(f"Art operation response status code: {response.status_code}")
        logging.info(f"Art operation response body: {response.text}")
        return response.json()

async def generate_and_upload_image(src1_art_id: str, src2_art_id: str) -> None | tuple:
    image1_filename = check_if_image_exists(src1_art_id)
    image2_filename = check_if_image_exists(src2_art_id)

    # Fetch URLs if needed
    image1_url, image2_url = await asyncio.gather(
        fetch_image_url(src1_art_id) if not image1_filename else None,
        fetch_image_url(src2_art_id) if not image2_filename else None
    )

    # Download images if they don't exist locally
    if not image1_filename:
        if not image1_url:
            raise ValueError(f"Failed to fetch image for art ID {src1_art_id}")
        image1_filename = await download_image(image1_url, src1_art_id)

    if not image2_filename:
        if not image2_url:
            raise ValueError(f"Failed to fetch image for art ID {src2_art_id}")
        image2_filename = await download_image(image2_url, src2_art_id)
    output_filename = f"{uuid.uuid4()}"
    model.generate_image(image1_filename, image2_filename, output_filename)

    with open(f"./output/{output_filename}_00001_.png", 'rb') as f:
        image_bytes = f.read()

    s3_file_name = f"generated_images/{output_filename}.png"
    s3_url = upload_file_to_s3_binary(image_bytes, AWS_S3_BUCKET, s3_file_name)

    visual_description = await describe_image_with_openai_vision(s3_url, "default", "default",
                                                                 "generated_art",)

    status, name_description = await name_description_based_of_vision_description("generated_art",
                                                                                  visual_description[1])
    if not status:
        raise Exception("Error while generating generate_picture_metadata")
    name = name_description["name"]
    short_description = name_description["short_description"]
    full_story = name_description["full_story"]
    tags = name_description["tags"]
    # gen_post = await post_based_of_video_description("generated_art", full_story)
    gen_post = name_description["tweet"]
    # Post the art details to the API
    art_details = {"name": name, "type": "generated_art", "description": short_description,
                   "user_id": "d122eb30-fae3-4947-bd6e-06847a02e1ba", "description_prompt": full_story}

    art_details = await post_art_details(s3_url, art_details)
    return art_details, tags, gen_post, output_filename

def clean_tweet(tweet):
    # Remove hashtags
    tweet_no_hashtags = re.sub(r'#\S+', '', tweet)

    # Check if the tweet is longer than 200 characters
    if len(tweet_no_hashtags) > 200:
        tweet_no_hashtags = tweet_no_hashtags[:200]

        # Find the last dot before the cutoff point
        last_dot_index = tweet_no_hashtags.rfind('.')
        if last_dot_index != -1:
            tweet_no_hashtags = tweet_no_hashtags[:last_dot_index + 1]
        else:
            # If no dot is found, trim to the nearest word
            last_space_index = tweet_no_hashtags.rfind(' ')
            if last_space_index != -1:
                tweet_no_hashtags = tweet_no_hashtags[:last_space_index]

    # Return the cleaned tweet
    return tweet_no_hashtags.strip()


# Function to handle tasks from Camunda
def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    src1_art_id = variables.get("src1_art_id")
    src2_art_id = variables.get("src2_art_id")

    loop = asyncio.get_event_loop()
    try:
        generated_art = loop.run_until_complete(generate_and_upload_image(src1_art_id, src2_art_id))
        if not generated_art:
            raise Exception("Empty generated Art")
        art_details, tags, gen_post, output_filename = generated_art
        variables["generated_art_id"] = art_details['id']
        variables["gen_token_description"] = art_details['description']
        variables["gen_token_name"] = art_details['name']
        tweet = f"{clean_tweet(gen_post)}"

        if "xgurunetwork" not in tweet:
            tweet = f"{clean_tweet(gen_post)} @xgurunetwork "

        tweet += f"Season 2 Pass https://v2.dex.guru/api/gen/{output_filename}.png"

        variables["gen_post"] = tweet
        variables["gen_token_tags"] = tags

        return task.complete(variables)
    except Exception as e:
        logging.error(f"Error during image generation: {str(e)}")
        return task.failure(
            "ImageGenerationFailure",
            f"Failed to generate image: {str(e)}",
            max_retries=1,
            retry_timeout=1000
        )


if __name__ == '__main__':
    logging.info("Initializing Camunda External Task Worker")
    ExternalTaskWorker(worker_id="1", base_url=CAMUNDA_URL, config=default_config).subscribe([TOPIC_NAME], handle_task)
