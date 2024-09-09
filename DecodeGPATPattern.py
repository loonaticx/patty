from typing import Any
from PIL import Image
import struct
import numpy as np
from BinaryReader import BinaryReader as Reader


# https://developer.gimp.org/core/standards/pat/
def readFile(reader: Reader):
    # header_size = reader.read(4)
    # size of pattern header (24) + length of pattern name
    header_size = reader.unpack(">I")[0]
    version = reader.unpack(">I")[0]
    assert version == 1
    pattern_width = reader.unpack(">I")[0]
    pattern_height = reader.unpack(">I")[0]
    pattern_depth = reader.unpack(">I")[0]
    magic_number = reader.unpack(">I")[0]  # magic number will always be GPAT
    # header_size - 1 says the document
    # total = header_size + 24
    # header_size - 25?
    # header_body = reader.read(header_size - 1)  # -23?
    # 30 - 24 = 6
    # so + 24?
    # header_size = 32
    # c = 32 - 1 -> 31
    # name = header_size - 24
    # name = 8
    pattern_name = reader.read(header_size - 24).decode('utf-8').split('\x00', 1)[0]
    # pattern_name = reader.read(header_size - 24)

    # H is unsigned short [2]
    # I is unsigned int [4]
    # B is unsigned char [1]
    pattern_size = pattern_width * pattern_height * pattern_depth

    # nbPatterns = reader.unpack(">I")[0]
    print("header_size:", header_size)

    print("version:", version)
    print("pattern_width:", pattern_width)
    print("pattern_height:", pattern_height)
    print("pattern_depth:", pattern_depth)
    print("magic_number:", magic_number)
    print("pattern_name:", pattern_name)

    """
    for (int i = 0; i <= pattern_size / pattern_depth; i += pattern_depth)
    """
    iterations = []
    pixelValues = []
    pixie = []
    # for i in range(0, pattern_size//pattern_depth, pattern_depth):
    #     pixel_R = reader.unpack(">B")[0]
    #     pixel_G = reader.unpack(">B")[0]
    #     pixel_B = reader.unpack(">B")[0]
    #     # iterations.append(i)
    #     pixelValues.append([pixel_R, pixel_G, pixel_B])

    """
    while len(pixelValues) < pattern_size // pattern_depth:
        if len(pixelValues) + pattern_depth == pattern_size // pattern_depth:
            print(f"Uh oh  {len(pixelValues)}")
            break
        pixel_R = reader.unpack(">B")[0]
        pixel_G = reader.unpack(">B")[0]
        pixel_B = reader.unpack(">B")[0]
        # iterations.append(i)
        # print(len(pixelValues))
        # 13222
        pixelValues.append([pixel_R, pixel_G, pixel_B])
        pixie.extend([pixel_R, pixel_G, pixel_B])
    """
    pixie = reader.read(pattern_size)
    print("pattern_size:", pattern_size)
    # we want 13225
    print(pattern_width * pattern_height)

    print(len(pixelValues))

    # print(len(iterations))
    pixelValues = np.array(pixie)
    print(pixelValues)

    colors = bytes(pixelValues)
    img = Image.frombytes('RGB', (pattern_width, pattern_height), colors)
    print(f"Size = {img.size}")
    img.show()


if __name__ == "__main__":

    with open("samples/Craters.pat", "rb") as f:
        data = f.read()

    reader = Reader(data)
    readFile(reader)
    print("remaining:", reader.remaining())
