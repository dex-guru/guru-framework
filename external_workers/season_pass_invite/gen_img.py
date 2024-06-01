import os
import random
import sys
from typing import Sequence, Mapping, Any, Union
import torch
import click

# Functions for setup and utility
def get_value_at_index(obj: Union[Sequence, Mapping], index: int) -> Any:
    """Returns the value at the given index of a sequence or mapping."""
    try:
        return obj[index]
    except KeyError:
        return obj["result"][index]

def find_path(name: str, path: str = None) -> str:
    """Recursively looks at parent folders starting from the given path until it finds the given name."""
    if path is None:
        path = os.getcwd()
    if name in os.listdir(path):
        path_name = os.path.join(path, name)
        print(f"{name} found: {path_name}")
        return path_name
    parent_directory = os.path.dirname(path)
    if parent_directory == path:
        return None
    return find_path(name, parent_directory)

def add_comfyui_directory_to_sys_path() -> None:
    """Add 'ComfyUI' to the sys.path"""
    comfyui_path = find_path("ComfyUI")
    if comfyui_path is not None and os.path.isdir(comfyui_path):
        sys.path.append(comfyui_path)
        print(f"'{comfyui_path}' added to sys.path")

def add_extra_model_paths() -> None:
    """Parse the optional extra_model_paths.yaml file and add the parsed paths to the sys.path."""
    from main import load_extra_path_config
    extra_model_paths = find_path("extra_model_paths.yaml")
    if extra_model_paths is not None:
        load_extra_path_config(extra_model_paths)
    else:
        print("Could not find the extra_model_paths config file.")

add_comfyui_directory_to_sys_path()
add_extra_model_paths()

from nodes import (
    CLIPVisionEncode,
    CheckpointLoaderSimple,
    CLIPVisionLoader,
    LoadImage,
    unCLIPConditioning,
    VAEDecode,
    ConditioningZeroOut,
    EmptyLatentImage,
    SaveImage,
    KSampler,
    CLIPTextEncode,
)

# from nodes_ollama import NODE_CLASS_MAPPINGS


class BlendImagesProcessor:
    def __init__(self, gen_style_prompt: str = "Meditative character, vibrant hues, blue, green, orange,"
                                               " swirling patterns, robots, stormtroopers, dynamic poses,"
                                               " harmony, contrast, light, shadow, depth, tranquility,"
                                               " wonder, high-value NFT art"):
        self.checkpointloadersimple = CheckpointLoaderSimple()
        clipvisionloader = CLIPVisionLoader()
        self.cliptextencode = CLIPTextEncode()
        self.loadimage = LoadImage()
        self.clipvisionencode = CLIPVisionEncode()
        emptylatentimage = EmptyLatentImage()
        self.conditioningzeroout = ConditioningZeroOut()
        self.unclipconditioning = unCLIPConditioning()
        self.ksampler = KSampler()
        self.vaedecode = VAEDecode()
        self.saveimage = SaveImage()
        self.loadimage = LoadImage()
        self.gen_style_prompt = gen_style_prompt
        self.emptylatentimage_16 = emptylatentimage.generate(
            width=1024, height=1024, batch_size=1
        )
        self.clipvisionloader_2 = clipvisionloader.load_clip(
            clip_name="clip_vision_g.safetensors"
        )
        self.llavadescriber = NODE_CLASS_MAPPINGS["LLaVaDescriber"]()
        self.if_displaytext = NODE_CLASS_MAPPINGS["IF_DisplayText"]()
        self.if_savetext = NODE_CLASS_MAPPINGS["IF_SaveText"]()

    def generate_image(self, image1: str, image2: str, output: str) -> tuple:
        with torch.inference_mode():
            self.checkpointloadersimple_1 = self.checkpointloadersimple.load_checkpoint(
                ckpt_name="sd_xl_base_1.0.safetensors"
            )

            cliptextencode_3 = self.cliptextencode.encode(
                text=self.gen_style_prompt,
                clip=get_value_at_index(self.checkpointloadersimple_1, 1),
            )
            cliptextencode_4 = self.cliptextencode.encode(
                text="", clip=get_value_at_index(self.checkpointloadersimple_1, 1)
            )

            conditioningzeroout_5 = self.conditioningzeroout.zero_out(
                conditioning=get_value_at_index(cliptextencode_3, 0)
            )
            conditioningzeroout_6 = self.conditioningzeroout.zero_out(
                conditioning=get_value_at_index(cliptextencode_4, 0)
            )
            loadimage_1 = self.loadimage.load_image(image=image1)
            loadimage_2 = self.loadimage.load_image(image=image2)
            clipvisionencode_1 = self.clipvisionencode.encode(
                clip_vision=get_value_at_index(self.clipvisionloader_2, 0),
                image=get_value_at_index(loadimage_1, 0),
            )
            clipvisionencode_2 = self.clipvisionencode.encode(
                clip_vision=get_value_at_index(self.clipvisionloader_2, 0),
                image=get_value_at_index(loadimage_2, 0),
            )

            unclipconditioning_11 = self.unclipconditioning.apply_adm(
                strength=1,
                noise_augmentation=0,
                conditioning=get_value_at_index(conditioningzeroout_5, 0),
                clip_vision_output=get_value_at_index(clipvisionencode_1, 0),
            )
            unclipconditioning_12 = self.unclipconditioning.apply_adm(
                strength=1,
                noise_augmentation=0,
                conditioning=get_value_at_index(unclipconditioning_11, 0),
                clip_vision_output=get_value_at_index(clipvisionencode_2, 0),
            )
            ksampler_13 = self.ksampler.sample(
                seed=random.randint(1, 2 ** 64),
                steps=25,
                cfg=8,
                sampler_name="euler",
                scheduler="normal",
                denoise=1,
                model=get_value_at_index(self.checkpointloadersimple_1, 0),
                positive=get_value_at_index(unclipconditioning_12, 0),
                negative=get_value_at_index(conditioningzeroout_6, 0),
                latent_image=get_value_at_index(self.emptylatentimage_16, 0),
            )
            vaedecode_17 = self.vaedecode.decode(
                samples=get_value_at_index(ksampler_13, 0),
                vae=get_value_at_index(self.checkpointloadersimple_1, 2),
            )
            self.saveimage.save_images(
                filename_prefix=output, images=get_value_at_index(vaedecode_17, 0)
            )

            # llavadescriber = NODE_CLASS_MAPPINGS["LLaVaDescriber"]()
            #
            # save_post = llavadescriber.ollama_image_describe(
            #     model="llava:7b-v1.6",
            #     api_host="http://0.0.0.0:11434",
            #     timeout=300,
            #     temperature=0.2,
            #     seed_number=-1,
            #     max_tokens=50,
            #     keep_model_alive=-1,
            #     system_context="Maximum 260 symbols. You are an assistant who describes the content and composition of images. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise.",
            #     prompt="Maximum 260 symbols. Generate a tweet announcing the completion of a new digital artwork on Guru Network and the excitement of minting it soon. Use hashtags #NFTCommunity, #DigitalArt, and #GuruNetwork. Mention @xgurunetwork",
            #     image=get_value_at_index(vaedecode_17, 0),
            # )
            #
            # name_save = llavadescriber.ollama_image_describe(
            #     model="llava:7b-v1.6",
            #     api_host="http://0.0.0.0:11434",
            #     timeout=300,
            #     temperature=0.2,
            #     seed_number=0,
            #     max_tokens=200,
            #     keep_model_alive=-1,
            #     system_context="Maximum 15 symbols. You are an assistant who describes the content and composition of images. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise.",
            #     prompt="Return a unique name of this image as summary. Maximum 2 words. Be creative. In the beginning add word Guru",
            #     image=get_value_at_index(vaedecode_17, 0),
            # )
            #
            # description_save = llavadescriber.ollama_image_describe(
            #     model="llava:7b-v1.6",
            #     api_host="http://0.0.0.0:11434",
            #     timeout=300,
            #     temperature=0.2,
            #     seed_number=0,
            #     max_tokens=200,
            #     keep_model_alive=-1,
            #     system_context="Maximum 15 symbols. You are an assistant who describes the content and composition of images. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise.",
            #     prompt="Return a brief description for the generated art, which would go to NFT Descripption in collection.",
            #     image=get_value_at_index(vaedecode_17, 0),
            # )
            #
            # tags_save = llavadescriber.ollama_image_describe(
            #     model="llava:7b-v1.6",
            #     api_host="http://0.0.0.0:11434",
            #     timeout=300,
            #     temperature=0.2,
            #     seed_number=0,
            #     max_tokens=200,
            #     keep_model_alive=-1,
            #     system_context="You are an assistant who describes the content and composition of images. \n                    Describe only what you see in the image, not what you think the image is about.Be factual and literal. \n                    Do not use metaphors or similes. \n                    Be concise.",
            #     prompt="Return a list of 10 danbooru tags for this image, formatted as lowercase, separated by commas.",
            #     image=get_value_at_index(vaedecode_17, 0),
            # )
            #
            # return name_save, description_save, tags_save, save_post

# Main function with click for CLI
@click.command()
@click.option('--image1', required=True, help='First input image name')
@click.option('--image2', required=True, help='Second input image name')
@click.option('--output', required=True, help='Output image name')
def main(image1, image2, output):
    model = BlendImagesProcessor()
    model.generate_image(image1, image2, output)

if __name__ == "__main__":
    main()