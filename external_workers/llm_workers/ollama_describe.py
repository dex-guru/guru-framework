import base64
import requests
import asyncio
import json
import os
import logging
from ollama import AsyncClient

from openai.types.chat.completion_create_params import ResponseFormat

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the AsyncOpenAI client with an API key from environment variables
X_ACCOUNT = os.getenv('X_ACCOUNT', 'xgurunetwork')

client = AsyncClient(host=os.getenv("OLLAMA_URL", "http://172.16.5.239:11434"))


def download_image_to_base64(url):
    response = requests.get(url)
    if response.status_code == 200:
        base64_string = base64.b64encode(response.content).decode('utf-8')
        logging.info(f"Image successfully downloaded and encoded.")
        return base64_string
    else:
        logging.error("Failed to download image")
        return None

async def describe_image_with_openai_vision(image_url, name, description, image_type) -> tuple[bool, str]:
    base64_string = download_image_to_base64(image_url)
    if not base64_string:
        return False, "Failed to download or encode image."

    logging.info(f"Generating description for {image_type} image: {image_url}")
    if image_type == 'person':
        prompt = "Generate a description of a person from a photograph. Focus on the individual's body type, facial features such as the shape of their face, the hair's length, style, and color, as well as any notable expressions or gestures they may be making. The description should serve to convey the person's likeness without revealing their personal identity. Maximum 250 words"
    elif image_type == 'generated_art':
        prompt = "Provide a detailed analysis of the visual elements, colors, textures, and any distinctive stylistic features present in the image. Focus on describing the composition, any patterns or motifs, the use of light and shadow, and overall thematic presence. Maximum length 250 words."
    else:
        prompt = "Provide a detailed analysis of the visual elements, colors, textures, and any distinctive stylistic features present in the image. Focus on describing the composition, any patterns or motifs, the use of light and shadow, and overall thematic presence. Maximum length 250 words."

    if name and description:
        prompt = f"{prompt}\n\nArtwork Name: {name}\n\nArtwork Description: {description}"
    else:
        prompt = f"{prompt} generate a name and description for the artwork."

    try:
        response = await client.generate(model="llava", prompt=prompt, images=[base64_string])
        # Process the response
        if response['done']:
            description_text = response['response']
            return True, description_text.strip()
        message = f"Error while generating description for image: {response}"
        logging.error(message)
        return False, message
    except Exception as e:
        message = f"Error while generating description for image: {str(e)}"
        logging.error(message)
        return False, message


async def name_description_based_of_vision_description(image_type, vision_description, retries: int = 2) -> tuple[
    bool, dict]:
    # Define prompt based on the image type
    logging.info(f"Generating description for {image_type} description: {vision_description}")
    prompt = f""""
    You are an expert in art description and creative storytelling. Based on the provided description of art, generate a JSON object with the following parameters:
    - name (a maximum of 2 words)
    - short_description (a maximum of 60 symbols, serving as a catchy, condensed version of the full story)
    - full_story (a compelling and imaginative narrative that uses best practices in storytelling, as if a group of top marketers spent a month crafting it, targeting a progressive crypto and artist community. Ensure the story is engaging, concise, and formatted as a single paragraph without unnecessary line breaks or spaces)
    - tags (an array of 10 individual tags that are relevant to the story)
    - tweet (a cool Twitter post that people would love to share about minting their unique NFT. The post must be 140 characters max and mntion twitter account {X_ACCOUNT}. If the length is less than 140 characters, add a brief summary of the full story to reach the character limit)

    Example of art description: {vision_description}
    """

    system_content = "Maximum 15 symbols. You are an assistant who describes the content and composition of images Ffor NFT Listings. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise."
    try:

        response = await client.chat(
            model="phi3:medium-128k",
            format="json",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],

        )

        # Process the response

        description_text = response["message"]["content"]
        try:
            name_description_dict = json.loads(description_text)
            for key in ['name', 'short_description', 'full_story', 'tags']:
                if not name_description_dict.get(key) and retries > 0:
                    return await name_description_based_of_vision_description(image_type,
                                                                              vision_description, retries - 1)
            else:
                return True, name_description_dict
        except Exception as e:
            error_message = f"Error while processing response: {str(e)}"
            logging.error(error_message)
            return False, error_message
        return True, description_text
    except Exception as e:
        error_message = f"API request failed: {str(e)}"
        logging.error(error_message)
        return False, error_message



if __name__ == '__main__':
    # Worker initialization with logging
    logging.info("Initializing Camunda External Task Worker")
    # description = "This ultra-detailed digital art piece captures the essence of a high-speed journey on Japan's iconic Shinkansen (bullet train), blending the train's sleek design and efficiency with the vibrant and fleeting landscapes visible through its windows. The scene is interspersed with imaginative depictions of animals and geometric patterns, adding layers of complexity and intrigue. Crafted to emulate a 30-megapixel, 4k photograph taken with a CanonEOS 5D Mark IV DSLR using an 85mm lens, the artwork exhibits sharp focus, intricate detail, and the subtle interplay of light and shadow achieved through long exposure and diffuse backlighting. The composition's perfect contrast, high sharpness, face symmetry, and depth of field, alongside advanced techniques like ray tracing and global illumination, contribute to its lifelike and ultra-high-definition 8k quality, making it a masterpiece of digital artistry."
    # image_type = "art"
    # results = asyncio.run(name_description_based_of_vision_description(image_type, description))
    results = asyncio.run(describe_image_with_openai_vision("https://pixelpact.s3.us-east-2.amazonaws.com/images/34a5f21c-b01c-4843-bbb0-2cbfb763dd99.jpg", "Symphony", "Symphony", "ART"))

    print(results)