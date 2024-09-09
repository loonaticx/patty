from PIL import Image
import struct
from BinaryReader import BinaryReader as Reader


def decodeImage(data: bytes, height: int):
    output = bytearray()

    # i feel like this is unnecessary? a thing with this compression is that
    # you can concat it - but I guess this was meant to reduce memory usage
    # if only a part of the image was needed?
    # could this be a "failsafe"? or maybe for memory allocation?
    lengths = []
    for n in range(200):
        lengths.append(struct.unpack(">H", data[n * 2:n * 2 + 2])[0])

    n = 2 * height

    # lengths can probably be safely ignored?
    # the algo from GIMP is technically equivalent, except that it uses
    # the lengths array - as far as I can tell, unless there's badly compressed data,
    # it should be equivalent?
    while n < len(data):
        byte = data[n]

        if byte == 128:
            n += 1  # skip

        elif byte > 128:
            output.extend(bytes(data[n + 1] for _ in range(257 - byte)))
            n += 2

        else:
            output.extend(data[n + 1:n + 2 + byte])
            n += 2 + byte

    return bytes(output)


def readFile(reader: Reader):
    signature = reader.read(4)
    version = reader.unpack(">H")[0]
    assert version == 1

    nbPatterns = reader.unpack(">I")[0]

    print("signature:", signature)
    print("version:", version)
    print("nbPatterns:", nbPatterns)

    patternImages = []

    for _ in range(nbPatterns):
        patternImages.append(readPattern(reader))
    return patternImages


def readPattern(reader: Reader):
    version = reader.unpack(">I")[0]
    assert version == 1

    imageType = reader.unpack(">I")[0]
    height, width = reader.unpack(">HH")
    patternName = reader.read(2 * reader.unpack(">I")[0])
    patternId = reader.read(reader.unpack(">B")[0])  # apparently always 37 bytes?

    if imageType == 2:
        palette = reader.read(256 * 3)
        paletteSize = reader.unpack(">H")[0]
        unk = reader.read(2)  # FF FF?

    colorModel = reader.unpack(">I")[0]
    # apparently 3 is RGB, 2 is indexed, 1 is grayscale

    # not performant but safer lol
    patternSize = reader.unpack(">I")[0]
    patternData = reader.read(patternSize)
    pattern = Reader(patternData)

    top, left, bottom, right = pattern.unpack(">IIII")
    depth = pattern.unpack(">I")[0]  # most likely 24 (8*3 channels -- ?)
    assert depth == 24, "fixme"

    if colorModel == 3:  # RGB
        redChannel = readChannel(pattern)
        greenChannel = readChannel(pattern)
        blueChannel = readChannel(pattern)
        image = Image.merge("RGB", (redChannel, greenChannel, blueChannel))

    elif colorModel == 2:  # indexed
        indexChannel = readChannel(pattern)
        raise Exception("todo")  # pillow supports paletted images!

    elif colorModel == 1:  # grayscale
        image = readChannel(pattern)

    patternName = patternName.decode('utf-8').replace('\0', '')

    # Currently just a bunch of junk / unoccupied space
    pattern.read(88)
    if len(pattern.remaining()) >= 88 + 31:
        alpha_channel = readChannel(pattern)
        image.putalpha(alpha_channel)
    # image.save(f"pattern_{patternName}.png")
    return image


def readChannel(reader: Reader) -> Image.Image | None:
    version = reader.unpack(">I")[0]
    print("version", version)
    assert version == 1

    channelSize = reader.unpack(">I")[0]
    channelData = reader.read(channelSize)
    channel = Reader(channelData)

    channel.unpack(">I")[0]  # depth (ignore)
    top, left, bottom, right = channel.unpack(">IIII")

    depth = channel.unpack(">H")[0]
    assert depth == 8, "expected depth of 8 (for now?)"

    compression = channel.unpack(">B")[0]

    width = right - left
    height = bottom - top

    print("height", height)

    imageData = channel.remaining()
    if compression == 1:
        imageData = decodeImage(imageData, height)

    print("length", len(imageData))

    im = Image.frombytes("L", (width, height), imageData)
    return im


if __name__ == "__main__":

    with open("PatternGroupRGBA.pat", "rb") as f:
        data = f.read()

    reader = Reader(data)
    readFile(reader)
    print("remaining:", reader.remaining())
