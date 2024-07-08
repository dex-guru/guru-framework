import json
import os
import logging

from openai import AsyncOpenAI
from openai.types.chat.completion_create_params import ResponseFormat

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the AsyncOpenAI client with an API key from environment variables
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Main function to describe images using OpenAI's model
async def describe_image_with_openai_vision(image_url, name, description, image_type) -> tuple[bool, str]:
    # Example of logging an operation
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
        response = await client.chat.completions.create(model="gpt-4-1106-vision-preview",
                                                        messages=[
                                                            {
                                                                "role": "user",
                                                                "content": [
                                                                    {"type": "text", "text": prompt},
                                                                    {"type": "image_url", "image_url": image_url}
                                                                ],
                                                            }
                                                        ])

        # Process the response
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            description_text = choice.message.content
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
    - tweet (a cool Twitter post that people would love to share about minting their unique NFT. The post must be 140 characters max and include @xgurunetwork. If the length is less than 140 characters, add a brief summary of the full story to reach the character limit)

    Example of art description: {vision_description}
    """

    system_content = "Maximum 15 symbols. You are an assistant who describes the content and composition of images Ffor NFT Listings. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise."
    response_format = ResponseFormat(type="json_object")
    model = "gpt-3.5-turbo-1106"
    # model = "gpt-4-1106-preview"
    try:
        response = await client.chat.completions.create(
            model=model,
            response_format=response_format,
            max_tokens=300,
            n=1,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],

        )

        # Process the response
        if response.choices:
            description_text = response.choices[0].message.content
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
        else:
            error_message = "No description generated."
            logging.error(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"API request failed: {str(e)}"
        logging.error(error_message)
        return False, error_message


async def post_based_of_video_description(image_type, vision_description, retries: int = 2) -> tuple[bool, dict]:
    # Define prompt based on the image type
    post_system_context = "Maximum 200 symbols. You are an assistant who describes the content and composition of images. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise."
    post_prompt = "Maximum 200 symbols. Generate a tweet announcing the completion of a new digital artwork on Guru Network and the excitement of minting it soon. Use hashtags #NFTCommunity, #DigitalArt, and #GuruNetwork. Mention @xgurunetwork. put it in gen_post field."
    # Call the OpenAI API
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            max_tokens=60,
            n=1,
            messages=[
                {"role": "system", "content": post_system_context},
                {"role": "user", "content": post_prompt}
            ],

        )

        # Process the response
        if response.choices:
            description_text = response.choices[0].message.content
            return True, description_text
        else:
            error_message = "No opst generated."
            logging.error(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"API request failed: {str(e)}"
        logging.error(error_message)
        return False, error_message


if __name__ == '__main__':
    # Worker initialization with logging
    logging.info("Initializing Camunda External Task Worker")