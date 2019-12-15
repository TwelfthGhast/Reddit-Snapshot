from PIL import Image
from io import BytesIO


def save_image(img, post_id, location=""):
    # open request image stream - keep this in memory as faster than disk I/O
    try :
        byteImg = Image.open(BytesIO(img.content))
    except IOError:
        return [False, "I/O error in reading image"]
    # save the img
    byteImg.save(f"{location}{post_id}.png")

    return [True, "Success"]
