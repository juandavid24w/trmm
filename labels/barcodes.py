from io import BytesIO

from barcode import EAN13
from barcode.writer import SVGWriter


def get_barcode_image(number, width=None, height=None):
    number = f"{number:013}"

    file = BytesIO()
    writer = SVGWriter()
    writer.set_options(
        {
            "width": width,
            "height": height,
        }
    )

    EAN13(number, writer=writer).write(file, options={"write_text": False})

    return file
