import requests
from PIL import Image
from io import BytesIO


def save_image(url, post_id, location=""):
    # Load the img url
    try:
        img = requests.get(url, stream=True)
    except:
        return False

    # check that the image is valid
    if img.status_code != 200 or img == False:
        return False

    # Try to validate file is an image by checking magic bytes
    # https://en.wikipedia.org/wiki/List_of_file_signatures

    magic_bytes = [
        # jpeg
        b'\xff\xd8\xff\xe0',
        b'\xff\xd8\xff\xdb',
        b'\xff\xd8\xff\xee',
        b'\xff\xd8\xff\xe1',
        # png
        b'\x89\x50\x4E\x47'
    ]

    is_image = False

    for header in magic_bytes:
        if img.content[:4] == header:
            is_image = True


    if not is_image:
        return False

    # open request image stream - keep this in memory as faster than disk I/O
    try :
        byteImg = Image.open(BytesIO(img.content))
    except IOError:
        raise ValueError("Issue with opening image.")

    # save the img
    byteImg.save(f"{location}{post_id}.png")

    return True
