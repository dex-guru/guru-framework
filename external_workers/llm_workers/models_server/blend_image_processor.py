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
    ConditioningZeroOut,
    CLIPTextEncode,
    SaveImage,
    CLIPVisionLoader,
    LoadImage,
    CLIPVisionEncode,
    EmptyLatentImage,
    unCLIPConditioning,
    CheckpointLoaderSimple,
    VAEDecode,
    KSampler,
    NODE_CLASS_MAPPINGS,
)


class BlendImagesProcessor:
    def __init__(self, gen_style_prompt: str = "Meditative character, vibrant hues, blue, green, orange,"
                                               " swirling patterns, robots, stormtroopers, dynamic poses,"
                                               " harmony, contrast, light, shadow, depth, tranquility,"
                                               " wonder, high-value NFT art",):
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

    def generate_image(self, image1: str, image2: str, output: str) -> None:
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
            saveimage_18 = self.saveimage.save_images(
                filename_prefix=output, images=get_value_at_index(vaedecode_17, 0)
            )
            return saveimage_18

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