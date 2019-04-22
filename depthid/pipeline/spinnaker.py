from time import sleep

from numpy import ndarray
from PySpin import Image, HQ_LINEAR, IEnumerationT_PixelFormatEnums, Camera


def convert_format(data: Image, output_format: IEnumerationT_PixelFormatEnums) -> Image:
    """Transforms PySpin image into specified output format.

    Arguments:
        data (Image): Source image
        output_format (IEnumerationT_PixelFormatEnums): Output format

    Returns:
        data (Image)
    """
    return data.Convert(output_format, HQ_LINEAR)


def transform_ndarray(data: Image) -> ndarray:
    """Transforms PySpin image into numpy ndarray.

    Arguments:
        data (Image): Source image.

    Returns:
        data (ndarray)
    """
    return data.GetNDArray()


def capture(camera: Camera, wait_before: float, wait_after: float) -> Image:
    """Captures image from camera.

    Arguments:
        camera (PySpinCamera): Instance of camera to capture from.
        wait_before (float): Seconds to wait before performing capture.
        wait_after (float): Seconds to wait after performing capture.

    Returns:
        data (Image)
    """
    sleep(wait_before)
    image = camera.GetNextImage()
    image.Release()
    sleep(wait_after)
    return image


def save(data: Image, filename: str) -> bool:
    """Saves provided image to disk using specified filename.

    Arguments:
        data (Image): Image to save.
        filename (str): Filename to save image as.

    Returns:
        success (bool)
    """
    return data.Save(filename)
