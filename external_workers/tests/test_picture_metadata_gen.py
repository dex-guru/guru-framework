import pytest

from main import clean_tweet
from season_pass_invite.dall_e_generate_descriptive_prompt import describe_image_with_openai_vision, \
    name_description_based_of_vision_description, post_based_of_video_description


@pytest.mark.asyncio
async def test_generate_picture_metadata():
    # picture_url = "https://i.seadn.io/s/raw/files/b5d20763321bb323e0ce188666e1415f.png"
    # visual_description = await describe_image_with_openai_vision(picture_url, "default", "default",
    #                                                              "generated_art")
    visual_description = (True, f"The image presents a stylized illustration featuring a group of characters with a "
                                f"vibrant and somewhat abstract background. The central figure stands out with a "
                                f"passive, relaxed pose, wearing headphones, and featuring simple, smooth facial "
                                f"features that are reminiscent of a typical emoji. This figure wears a sweatshirt "
                                f"with an apparent 'unamused' face emoji design, black pants, and chunky white sneakers,"
                                f" which suggest a contemporary urban style.\n\nSurrounding this central figure are"
                                f" three other characters, depicted in a dynamic and almost frenetic state, "
                                f"contrasting the central figure\'s calm demeanor. These characters are illustrated "
                                f"with exaggerated body proportions and postures that evoke movement and chaos. "
                                f"Their clothing is colorful, with various patterns and colors that seem haphazard"
                                f" and spontaneous, reinforcing the sense of dynamic energy.\n\nThe background "
                                f"is an explosion of abstract shapes and colors in a graffiti-like style, "
                                f"with earthy tones such as oranges and yellows blending with cooler shades"
                                f" of blue and green. The use of bold, undefined shapes and splashing color provides "
                                f"a sense of motion and disorder.\n\nLight and shadow are not heavily emphasized, "
                                f"with the illustration favoring flat colors and outlined forms, creating a strong "
                                f"graphic quality. The overall thematic presence seems to explore the contrast "
                                f"between stillness and action, possibly representing the concept of inner "
                                f"peace amid external chaos. The artwork\'s style is evocative of contemporary"
                                f" street art and urban culture, with a hint of commentary on social interaction "
                                f"and personal space in the digital age.")
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

    if "xgurunetwork" not in tweet:
        tweet = f"{clean_tweet(gen_post)} @xgurunetwork "

    tweet += "Season 2 Pass https://v2.dex.guru/api/gen/40ac3829-cef6-474a-9d18-22a9454aece7.jpg"
    # Post the art details to the API
    art_details = {"name": name, "type": "generated_art", "description": short_description,
                   "user_id": "d122eb30-fae3-4947-bd6e-06847a02e1ba", "description_prompt": full_story}

    assert art_details

if __name__ == '__main__':
    pytest.main()
