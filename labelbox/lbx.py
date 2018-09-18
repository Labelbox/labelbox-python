"Module for interacting with the LBX file format."

def encode(image):
    """Converts a `PIL.Image` to a `io.BytesIO` with LBX encoded data.

    Args:
        image (`PIL.Image`): The image to encode.

    Returns:
        A `io.BytesIO` containing the LBX encoded image.
    """
    pass

def decode(lbx):
    """Decodes a `io.BytesIO` with LBX encoded data into a `PIL.Image`.

    Args:
        lbxA (`io.BytesIO`): A byte buffer containing the LBX encoded image data.

    Returns:
        A `PIL.Image` of the decoded data.
    """
    pass
