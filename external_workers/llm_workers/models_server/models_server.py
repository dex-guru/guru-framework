import os

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from llm_workers.models_server.blend_image_processor import BlendImagesProcessor
from llm_workers.models_server.generate_image import generate_and_upload_image

# from llm_workers.models_server.generate_image import generate_and_upload_image

# Define the directory to save the images
IMAGE_DIR = 'images'

# Ensure the directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

model = BlendImagesProcessor()

class GenImageView(web.View):
    def __init__(self, request: Request) -> None:
        self._request = request

    async def post(self) -> Response:
        if not self._request.can_read_body:
            return web.json_response({'error': 'Request body is required'}, status=400)
        data = await self._request.json()
        src1_img_url = data.get('src1_img_url')
        src2_img_url = data.get('src2_img_url')

        if not src1_img_url or not src2_img_url:
            return web.json_response({'error': 'src1_img_url and src2_img_url are required'}, status=400)

        # Call the generate_image method
        generated_image = await generate_and_upload_image(src1_img_url, src2_img_url, model)
        # Assuming generate_image returns a path to the generated image
        return web.json_response({'generated_image_path': generated_image})


# Setting up the application and routes
app = web.Application()
app.router.add_view('/generate', GenImageView)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
