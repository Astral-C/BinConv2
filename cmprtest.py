from bStream import *
from PIL import Image
import squish

def CompressBlock(image, imageData, tile_x, tile_y, block_x, block_y):
    rgba = [0 for x in range(64)]
    mask = 0
    for y in range(4):
        if(tile_y + block_y + y < image.height):    
            for x in range(4):
                if(tile_x + block_x + x < image.width):
                    index = (y * 4) + x
                    mask |= (1 << index)
                    localIndex = 4 * index
                    pixel = imageData[(tile_x + block_x + x), (tile_y + block_y + y)]
                    rgba[localIndex + 0] = pixel[0]
                    rgba[localIndex + 1] = pixel[1]
                    rgba[localIndex + 2] = pixel[2]
                    rgba[localIndex + 3] = (pixel[3] if len(pixel) == 4 else 0xFF) #just in case alpha is not enabled

    return squish.compressMasked(bytes(rgba), mask, squish.DXT1)


def ConvertTexture(tex_path):
    img = Image.open(tex_path)
    img_data = img.load()

    img_out = bStream()

    img_out.writeUInt8(0x0E)
    img_out.writeUInt8(0x01)
    img_out.writeUInt16(img.width)
    img_out.writeUInt16(img.height)
    img_out.writeUInt8(0x00)
    img_out.writeUInt8(0x00)
    img_out.writeUInt16(0x0000)
    img_out.writeUInt16(0x0000)
    img_out.writeUInt32(0x00000000)
    img_out.writeUInt32(0x00000000)
    img_out.writeUInt8(0x00)
    img_out.writeUInt8(0x00)
    img_out.writeUInt16(0x0000)
    img_out.writeUInt8(0x01)
    img_out.writeUInt8(0x00)
    img_out.writeUInt16(0x0000)
    img_out.writeUInt32(0x00000020)

    for ty in range(0, img.height, 8):
        for tx in range(0, img.width, 8):
            for by in range(0, 8, 4):
                for bx in range(0, 8, 4):
                    img_out.write(CompressBlock(img, img_data, tx, ty, bx, by))

    img_out.seek(0)
    return img_out.read()


test = bStream(path="twiggy.bti")
test.write(ConvertTexture("./Models/smugmode.png"))