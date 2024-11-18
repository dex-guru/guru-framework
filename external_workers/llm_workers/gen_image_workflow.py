import asyncio
import json
import logging
import urllib.parse
import urllib.request
import uuid

import websocket

from llm_workers.models_server.utils import upload_file_to_s3_binary


class ImageGenerator:
    def __init__(self, server_address,
                 prompt_file_path):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.prompt_data = self.load_prompt(prompt_file_path)

    def load_prompt(self, prompt_file_path):
        """Load prompt from a JSON file."""
        with open(prompt_file_path, 'r') as file:
            return json.load(file)

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(self.server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    async def get_images(self, ws, prompt):
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        output_images = {}
        current_node = ""
        try:
            while True:
                out = await asyncio.wait_for(asyncio.to_thread(ws.recv),
                                             timeout=60)  # Wait for a message with a 60-second timeout
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['prompt_id'] == prompt_id:
                            if data['node'] is None:
                                break  # Execution is done
                            else:
                                current_node = data['node']
                else:
                    if current_node == '18':
                        logging.info(f"Received image data for prompt_id : {prompt_id}")
                        images_output = output_images.get(current_node, [])
                        images_output.append(out[8:])
                        output_images[current_node] = images_output
        except asyncio.TimeoutError:
            logging.error("Timed out waiting for the WebSocket message.")
            return []

        return output_images

    async def gen_image(self, src_image_url_1: str, src_image_url_2: str, image_name: str = "generated_image"):
        # Establish WebSocket connection
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")

        # Generate images
        self.prompt_data["31"]["inputs"]["image_url"] = src_image_url_1
        self.prompt_data["32"]["inputs"]["image_url"] = src_image_url_2
        images = await self.get_images(ws, self.prompt_data)

        # Get the first image (assuming there's at least one)
        for node_id in images:
            for image_data in images[node_id]:
                s3_url = upload_file_to_s3_binary(image_data, image_name)
                return {"image_url": s3_url}

        return {"error": "No images generated"}


# Example usage
if __name__ == "__main__":
    server_address = "127.0.0.1:8188"
    prompt_file_path = "path/to/your/prompt.json"

    image_gen = ImageGenerator(server_address, prompt_file_path)
    result = image_gen.gen_image(image_name="test_image")
    print(result)
