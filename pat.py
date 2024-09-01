import struct
from PIL import Image
import io
import numpy as np

# https://www.selapa.net/swatches/patterns/fileformats.php

# https://pillow.readthedocs.io/en/stable/handbook/tutorial.html
def roll(im, delta):
    """Roll an image sideways."""
    xsize, ysize = im.size

    delta = delta % xsize
    if delta == 0:
        return im

    part1 = im.crop((0, 0, delta, ysize))
    part2 = im.crop((delta, 0, xsize, ysize))
    im.paste(part1, (xsize - delta, 0, xsize, ysize))
    im.paste(part2, (0, 0, xsize - delta, ysize))

    return im


def create_rgb_image_from_stream(byte_stream, width, height):
    # Calculate the number of pixels
    num_pixels = width * height

    expected_length = num_pixels * 3  # 3 bytes per pixel for RGB

    print(f"len(byte_stream) - {len(byte_stream)}")
    print(f"s {len(byte_stream) / 24}")
    print(f"num_pixels -> {num_pixels} and * 3 = {num_pixels * 3}")

    ## DANGEROUS
    trimmed_stream = byte_stream[:expected_length]
    byte_stream = trimmed_stream

    # Ensure the byte stream length is correct
    if len(byte_stream) != num_pixels * 3:
        raise ValueError("Byte stream length does not match expected size for the given dimensions.")

    # Split the byte stream into red, green, and blue channels
    red_channel = byte_stream[:num_pixels]
    # print(red_channel)
    green_channel = byte_stream[num_pixels:2 * num_pixels]
    blue_channel = byte_stream[2 * num_pixels:]
    # red_arr = np.frombuffer(red_channel, dtype = np.uint8)
    # np.roll(red_arr, 100)

    # Combine the channels into an RGB array
    rgb_array = np.zeros((height, width, 3), dtype = np.uint8)
    rgb_array[..., 0] = np.frombuffer(red_channel, dtype = np.uint8).reshape(height, width)
    rgb_array[..., 1] = np.frombuffer(green_channel, dtype = np.uint8).reshape(height, width)
    rgb_array[..., 2] = np.frombuffer(blue_channel, dtype = np.uint8).reshape(height, width)
    # blue_color_arr = rgb_array[..., 2]
    # np.roll(rgb_array[..., 2], 50)

    # Create an Image object from the array
    image = Image.fromarray(rgb_array, 'RGB')
    return image


def read_image_data(file, pattern_size, pattern_channel_compression):
    # Read the raw image data
    print(pattern_size)
    data = file.read(pattern_size)
    # print(data)

    print(f"pattern_channel_compression - {pattern_channel_compression}")
    print(data)
    print("xxxxxx")
    guh = decode_packbits(data)
    # print(decode_packbits(data))

    if pattern_channel_compression == 0:
        # Uncompressed data
        return data
    elif pattern_channel_compression == 1:
        # RLE (PackBits) compression
        return decode_packbits(data)
    else:
        raise ValueError(f"Unsupported compression type: {pattern_channel_compression}")


def decode_packbits(data):
    # Decode PackBits RLE compression
    unpacked_data = io.BytesIO()
    i = 0
    while i < len(data):
        byte = data[i]
        # Lazy workaround: Convert byte from unsigned to signed
        if byte >= 128:
            byte = byte - 256
        i += 1
        if byte >= 0:
            unpacked_data.write(data[i:i + byte + 1])
            i += byte + 1
        else:
            count = -byte + 1
            byte_value = data[i]
            i += 1
            unpacked_data.write(byte_value.to_bytes(1, byteorder = 'big') * count)
    return unpacked_data.getvalue()


def read_pat_file(filename):
    with open(filename, 'rb') as f:
        # Read the initial header (8BPT + Version + Number of patterns)
        header = f.read(6)  # '8BPT' (4 bytes) + Version (2 bytes)

        # We need to interpret this in big endian format
        # < is little endian, > is big endian
        signature, version = struct.unpack(">I H", header)
        print(f"signature = {signature}")

        # header is 38 42 50 54 [ 4*char (8BPT) ]
        # version is 00 01 [ 1*int16 (1) ]
        # number patterns is 1*int32

        # we have 11 patterns in our sample
        print(header)

        # 0x38425054 is 8BPT in little endian
        # 0x943870036 is 8BPT in big endian

        print(hex(1414545976))

        # hex of 1414545976 is 0x54504238

        # we w
        if signature != 0x38425054:  # Check for '8BPT' signature
            raise ValueError("File signature does not match '8BPT'")

        # if version != 2:
        #     raise ValueError(f"Unsupported version: {version}")

        # Read the number of patterns
        # correct
        num_patterns = struct.unpack(">I", f.read(4))[0]

        patterns = []
        print(f"num_patterns = {num_patterns}")

        for _ in range(num_patterns):
            # Read the length of the pattern block
            # word = f.read(4)
            # b'\x00\x00\x00\x01'
            pattern_data_version = struct.unpack(">I", f.read(4))[0]
            pattern_color_model = struct.unpack(">I", f.read(4))[0]
            pattern_width = struct.unpack(">H", f.read(2))[0]
            pattern_height = struct.unpack(">H", f.read(2))[0]
            pattern_name_length = struct.unpack(">I", f.read(4))[0]
            # Handle 0-termination
            pattern_name = f.read(2 * pattern_name_length).decode('utf-16be').split('\x00', 1)[0]
            # https://stackoverflow.com/questions/2051070/using-python-struct-unpack-with-1-byte-variables
            pattern_id_length = struct.unpack(">H", b'\x00' + f.read(1))[0]
            # print(f.read(pattern_id_length))

            # b'81ddd28c-afab-884f-95ac-7437af8ffb22'
            #  Pascal string
            # ascii or utf8
            pattern_id = f.read(pattern_id_length).decode('utf-8').split('\x00', 1)[0]

            if pattern_color_model == 2:
                # If model is 2 (indexed), here come palette informations (256*3 bytes) + 4 unknown bytes
                pass

            # 48 + 24 + 48 + 48 + 48 + 32 + 2

            # 32 + 16  -> 48

            # 250 ?

            # 32 x 3 --> 96

            pattern_version = struct.unpack(">I", f.read(4))[0]  # 3 (good)
            # example has: 00 00 23 8C which is 9100
            pattern_size = struct.unpack(">I", f.read(4))[0]  # 00 00 A8 8B | 43147
            print(hex(pattern_size))
            rectangle_top = struct.unpack(">I", f.read(4))[0]  # 0
            rectangle_left = struct.unpack(">I", f.read(4))[0]  # 0
            rectangle_bottom = struct.unpack(">I", f.read(4))[0]  # 200 { 00 00 C8 00 }
            rectangle_right = struct.unpack(">I", f.read(4))[0]  # 200 { 00 00 C8 00 }
            number_channels = struct.unpack(">I", f.read(4))[0]  # 24 { 00 00 18 00 }
            # general: 24 * 8 = 192
            print(number_channels)

            # Read pattern header
            # pattern_header = f.read(16)
            # print(pattern_header)
            # pattern_id, width, height, depth = struct.unpack(">IIII", pattern_header)
            # print(pattern_id)
            # pattern id?

            # print(f"depth = {depth}")

            # if depth != 8:
            #     raise ValueError("Only 8-bit depth patterns are supported")

            # Read pattern name (Pascal string)
            # name_length = struct.unpack(">B", f.read(1))[0]
            # name = f.read(name_length).decode('ascii')
            # f.seek((4 - (name_length + 1) % 4) % 4, 1)  # Align to the next 4-byte boundary
            # 122
            # pattern channels
            pattern_channel_used = struct.unpack(">I", f.read(4))[0]
            pattern_channel_size = struct.unpack(">I", f.read(4))[0]
            pattern_channel_depth32 = struct.unpack(">I", f.read(4))[0]
            pattern_channel_rectangle_top = struct.unpack(">I", f.read(4))[0]
            pattern_channel_rectangle_left = struct.unpack(">I", f.read(4))[0]
            pattern_channel_rectangle_bottom = struct.unpack(">I", f.read(4))[0]
            pattern_channel_rectangle_right = struct.unpack(">I", f.read(4))[0]
            pattern_channel_depth16 = struct.unpack(">H", f.read(2))[0]  # 8
            # 1*int8 (0: data is uncompressed, 1: RLE (PackBits) compression, 2: ZIP without prediction,
            # 3: ZIP with prediction) — however, I've only seen 0 and 1
            pattern_channel_compression = struct.unpack(">H", b'\x00' + f.read(1))[0]
            # pattern_channel_compression = f.read(pattern_id_length).decode('utf-8').split('\x00', 1)[0]

            # Read image data
            # pattern_size = 43147
            image_data = read_image_data(f, pattern_size, pattern_channel_compression)

            pattern_null = struct.unpack(">I", f.read(4))[0]  # 0

            # Align to the next 2-byte boundary
            alignment_padding = (2 - len(image_data) % 2) % 2
            # if alignment_padding > 0:
            #     f.seek(alignment_padding, 1)

            pattern_alpha_channel = f.read(alignment_padding)
            print("pattern_alpha_channel")
            print(pattern_alpha_channel)

            # Read remaining data if needed
            # remaining_data = f.read()  # Or handle according to the file format

            newImg = Image.new(mode = "L", size = (pattern_width, pattern_height))

            print(image_data)

            new_image = create_rgb_image_from_stream(image_data, pattern_width, pattern_height)

            # Create a Pillow image from the image data
            # Example assumes grayscale image; adjust mode if needed
            # stream = io.BytesIO(image_data)
            # image = Image.frombytes('RGB', (pattern_width, pattern_height), stream.getvalue())
            # image = image.convert('RGB')
            # print(image)
            # new_image.show()
            r, g, b = new_image.split()
            width, height = new_image.size
            # print(width // 2)
            g = roll(g, (width // 4) - 5)
            b = roll(b, (- width // 4) - 8)

            new_image = Image.merge("RGB", (r, g, b))

            # new_image.show()

            # a = new_image.getchannel('B')
            # print(a.get_channel_values())
            # a.show()
            # 188 as-is
            # pattern_image_data = f.read((2 - (number_channels + 1) % 2) % 2)

            # pattern_image_data = f.read((2 - (number_channels + 1) % 2) % 2)  # Handle 0-termination

            # pattern_image_data = f.seek((2 - (number_channels + 1) % 2) % 2, 1)  # Align to the next 2-byte boundary
            # pattern_null = struct.unpack(">I", f.read(4))[0] # 0
            # pattern_alpha_channel =  f.seek((2 - (number_channels + 1) % 2) % 2, 1)
            # print(f"pattern_image_data")
            # print(pattern_image_data)

            # print(f.seek((2 - (number_channels + 1) % 2) % 2, 1) )

            # 70 offset (beginning)
            # 3100 - 3110 offset

            # alpha channel is

            # 22 + 32 + 32 + 32 +32 --> 150
            # Read image data (Indexed color data)
            # values are all Uint8
            # image_data = list(f.read(pattern_width * pattern_height))
            # print(image_data)

            # Create a Pillow image from the data
            # image = Image.new('P', (pattern_width, pattern_height))
            # image.putdata(pattern_image_data)
            # a = image.convert('RGB')
            # print(a)
            # a.show()

            patterns.append((pattern_name, new_image))

        return patterns


patterns = read_pat_file("PatternTest.pat")

for name, image in patterns:
    print(f"Pattern Name: {name}")
    image.show()
