import asyncio
import os
import logging
from typing import Optional
import re

import httpx
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker

from llm_workers.openai_describe import describe_image_with_openai_vision, name_description_based_of_vision_description
from season_pass_invite.config import SYS_KEY, API_URL, GEN_IMG_URL, OLLAMA_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables to configure the script
TOPIC_NAME = os.getenv('TOPIC_NAME', "comfy_season_blend")
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://demo:demo@localhost:8080/engine-rest')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'pixelpact')
X_ACCOUNT = os.getenv('X_ACCOUNT', 'xgurunetwork')
X_LINK = os.getenv('X_LINK', 'https://v2.dex.guru/gen/')

# Logging the script startup
logging.info("Starting Image Generation Worker")

# Configuration for the Camunda External Task Client
default_config = {
    "maxTasks": 1,
    "lockDuration": 30000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 10
}

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

async def gen_image_client(img1_url, img2_url):
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-SYS-KEY": os.getenv('X_SYS_KEY', SYS_KEY)
        }

        parameters = {
            "src1_img_url": img1_url,
            "src2_img_url": img2_url,
        }

        response = await client.post(f"{GEN_IMG_URL}", json=parameters, headers=headers, timeout=120)
        if response.status_code >= 400:
            error_msg = f"HTTP error response: {response.status_code} {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)

        logging.info(f"Art operation response status code: {response.status_code}")
        logging.info(f"Art operation response body: {response.text}")
        return response.json()['generated_image_path']


async def get_user_id_by_camunda_user_id(camunda_user_id: str) -> None:
    """Post the art details to the API."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-SYS-KEY": os.getenv('X_SYS_KEY', SYS_KEY)
        }

        response = await client.get(f"{API_URL}/users?camunda_user_id={camunda_user_id}", headers=headers)
        if response.status_code >= 400:
            error_msg = f"HTTP error response: {response.status_code} {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)

        logging.info(f"Art operation response status code: {response.status_code}")
        logging.info(f"Art operation response body: {response.text}")
        return response.json()['id']


async def generate_and_upload_image(src1_art_id: str, src2_art_id: str, camunda_user_id: str) -> None | tuple:
    # Fetch URLs if needed
    image1_url, image2_url, user_id = await asyncio.gather(
        fetch_image_url(src1_art_id),
        fetch_image_url(src2_art_id),
        get_user_id_by_camunda_user_id(camunda_user_id)
    )
    s3_url = await gen_image_client(image1_url, image2_url)


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
    tweet = f"{clean_tweet(gen_post)}"

    if X_ACCOUNT not in tweet:
        tweet = f"{clean_tweet(gen_post)} {X_ACCOUNT} "
    # Post the art details to the API
    art_details = {"name": name, "type": "generated_art", "description": short_description,
                   "user_id": user_id, "description_prompt": full_story, "tags": tags}

    art_details = await post_art_details(s3_url, art_details)

    tweet += f" {X_LINK}{art_details['id']}"

    return art_details, tags, tweet


# Function to handle tasks from Camunda
def handle_task(task: ExternalTask) -> TaskResult:
    variables = task.get_variables()
    src1_art_id = variables.get("src1_art_id")
    src2_art_id = variables.get("src2_art_id")
    camunda_user_id = variables.get("camunda_user_id")

    loop = asyncio.get_event_loop()
    try:
        generated_art = loop.run_until_complete(generate_and_upload_image(src1_art_id, src2_art_id, camunda_user_id))
        if not generated_art:
            raise Exception("Empty generated Art")
        art_details, tags, tweet = generated_art
        variables["generated_art_id"] = art_details['id']
        variables["gen_token_description"] = art_details['description']
        variables["gen_token_name"] = art_details['name']

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
    ExternalTaskWorker(worker_id="2", base_url=CAMUNDA_URL, config=default_config).subscribe([TOPIC_NAME], handle_task)