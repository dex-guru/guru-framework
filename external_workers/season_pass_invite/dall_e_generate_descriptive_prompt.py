import asyncio
import json
import os
import logging
from camunda.external_task.external_task import ExternalTask, TaskResult
from camunda.external_task.external_task_worker import ExternalTaskWorker
from openai import AsyncOpenAI
from openai.types.chat.completion_create_params import ResponseFormat

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables to configure the script
TOPIC_NAME = os.getenv('TOPIC_NAME', "DallEGenerateDescriptivePrompt")
CAMUNDA_URL = os.getenv('CAMUNDA_URL', 'http://demo:demo@localhost:8080/engine-rest')

# Logging the script startup
logging.info("Starting Dali Generate Art Prompt script")

# Configuration for the Camunda External Task Client
default_config = {
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 15000,
    "sleepSeconds": 10
}

# Initialize the AsyncOpenAI client with an API key from environment variables
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Main function to describe images using OpenAI's model
async def describe_image_with_openai_vision(image_url, name, description, image_type) -> tuple[bool, str]:
    # Example of logging an operation
    logging.info(f"Generating description for {image_type} image: {image_url}")
    if image_type == 'person':
        prompt = "Generate a description of a person from a photograph. Focus on the individual's body type, facial features such as the shape of their face, the hair's length, style, and color, as well as any notable expressions or gestures they may be making. The description should serve to convey the person's likeness without revealing their personal identity. Maximum 250 words"
    elif image_type == 'generated_art':
        prompt = "Provide name and description for the artwork based on the visual elements, colors, textures, and any distinctive stylistic features present in the image. Focus on describing the composition, any patterns or motifs, the use of light and shadow, and overall thematic presence. Maximum length of name 50 characters and description 250 words."
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
    bool, str]:
    # Define prompt based on the image type
    logging.info(f"Generating description for {image_type} description: {vision_description}")
    if image_type == 'person':
        prompt = (f"Generate 2 words name and short, brief description for SEO page metadata "
                  f"sentences description of the person on portrait: {vision_description}")
    elif image_type == 'generated_art':
        prompt = (f"Generate 2 words name and short, brief description for SEO page metadata of AI generated art:"
                  f" {vision_description}")
    else:
        prompt = (f"Generate 2 words name and short, brief description for SEO page metadata"
                  f" sentences description of the artwork: {vision_description}")
    response_format = ResponseFormat(type="json_object")
    # Call the OpenAI API
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format=response_format,
            max_tokens=300,
            n=1,
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],

        )

        # Process the response
        if response.choices:
            description_text = response.choices[0].message.content
            try:
                name_description_dict = json.loads(description_text)
                if "name" not in name_description_dict or "description" not in name_description_dict:
                    if retries > 0:
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
    response_format = ResponseFormat(type="json_object")
    # Call the OpenAI API
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            response_format=response_format,
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
            try:
                name_description_dict = json.loads(description_text)
                if "gen_post" not in name_description_dict:
                    if retries > 0:
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
            error_message = "No opst generated."
            logging.error(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"API request failed: {str(e)}"
        logging.error(error_message)
        return False, error_message


# Function to handle tasks from Camunda
def handle_task(task: ExternalTask) -> TaskResult:
    # Task handling code with added logging
    logging.info(f"Handling task")
    variables = task.get_variables()
    img_picture = variables.get("img_picture")
    art_name = variables.get("name")
    art_description = variables.get("description")
    image_type = variables.get("type")
    loop = asyncio.get_event_loop()
    try:

        status, vision_result = loop.run_until_complete(describe_image_with_openai_vision(img_picture, art_name,
                                                                                          art_description, image_type))
        if not status:
            return task.bpmn_error(
                "art_description_generation_failed",
                vision_result,
                variables
            )
        if art_name == 'default' or art_description == 'default':
            status, name_description = loop.run_until_complete(name_description_based_of_vision_description(image_type,
                                                                                                            vision_result))
            if not status:
                return task.bpmn_error(
                    "art_description_generation_failed",
                    name_description,
                    variables
                )
            variables["gen_token_name"] = name_description.get("name")
            variables["description"] = name_description.get("description")
        variables["description_prompt"] = vision_result

        return task.complete(variables)
    except Exception as e:
        logging.error(f"Error during art description generation: {str(e)}")
        return task.failure(
            "ArtDescriptionGenerationError",
            f"Failed to generate art description: {str(e)[:50]}",
            max_retries=1,
            retry_timeout=1000
        )


if __name__ == '__main__':
    # Worker initialization with logging
    logging.info("Initializing Camunda External Task Worker")
    ExternalTaskWorker(worker_id="1", base_url=CAMUNDA_URL, config=default_config).subscribe([TOPIC_NAME], handle_task)
