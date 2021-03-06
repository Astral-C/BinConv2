from bStream import *
from PIL import Image
import struct
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
                    if(type(pixel) != int):
                        rgba[localIndex + 0] = pixel[0]
                        rgba[localIndex + 1] = pixel[1]
                        rgba[localIndex + 2] = pixel[2]
                        rgba[localIndex + 3] = (pixel[3] if len(pixel) == 4 else 0xFF) #just in case alpha is not enabled

    return squish.compressMasked(bytes(rgba), mask, squish.DXT1)

def ConvertTexture(tex_path):
    img = Image.open(tex_path)
    img_data = img.load()

    img_out = bStream()

    for ty in range(0, img.height, 8):
        for tx in range(0, img.width, 8):
            for by in range(0, 8, 4):
                for bx in range(0, 8, 4):
                    img_out.write(CompressBlock(img, img_data, tx, ty, bx, by))

    img_out.seek(0)
    return (img.width, img.height, img_out.read())

class Material():
    def __init__(self, index):
        self.texture_index = index
        # These should be something user can set
        # for now, though, no.
        self.u = 1
        self.v = 1

    def write(self, stream):
        stream.writeInt16(self.texture_index)
        stream.writeInt16(-1)
        stream.writeUInt8(self.u)
        stream.writeUInt8(self.v)
        stream.writeUInt16(0)
        stream.pad(12)

class Shader():
    def __init__(self, material, textures):
        # Generate tint color from the diffuse color if it exists
        
        self.bump_index = -1
        self.diffuse_index = -1
        self.tint = 0xFFFFFFFF
        
        if(material.diffuse):
            self.tint = (int(material.diffuse[0]*255) << 24 | int(material.diffuse[1]*255) << 16 | int(material.diffuse[2]*255) << 8 | 0xFF)
        
        if(material.bump_texname):
            self.bump_index = textures.material_indices[material.bump_texname]
        
        if(material.diffuse_texname):
            self.diffuse_index = textures.material_indices[material.diffuse_texname]
        
        print("Bump Map {0}, Diffuse Map {1}, Tint {2}".format(self.bump_index, self.diffuse_index, hex(self.tint)))

    def write(self, stream):
        stream.writeUInt8(1)
        stream.writeUInt8(1)
        stream.writeUInt8(1)
        stream.writeUInt32(self.tint)
        stream.pad(1)
        stream.writeInt16(self.diffuse_index)
        stream.writeInt16(self.bump_index)

        #demolisher support
        for x in range(6):
            stream.writeInt16(-1)

        stream.writeInt16(0)
        for x in range(7):
            stream.writeInt16(-1)

class ShaderManager():
    def __init__(self, materials, textures):
        self.shaders = [Shader(material, textures) for material in materials]

    def writeShaders(self, stream):
        for shader in self.shaders:
            shader.write(stream)

class TextureManager():
    def __init__(self, materials):
        self.textures = []
        self.materials = []
        self.material_indices = {}
        texindex = 0

        for material in materials:
            if(material.diffuse_texname):
                self.textures.append(ConvertTexture(material.diffuse_texname))
                self.material_indices[material.diffuse_texname] = texindex
                self.materials.append(Material(texindex))
                texindex += 1
            else:
                self.materials.append(Material(texindex))
                texindex += 1   

            if(material.bump_texname):
                self.textures.append(ConvertTexture(material.bump_texname))
                self.material_indices[material.bump_texname] = texindex
                self.materials.append(Material(texindex))
                texindex += 1


    def writeMaterials(self, stream):
        for material in self.materials:
            material.write(stream)
            
    def writeTextures(self, stream):
        header_section = bStream()
        data_section = bStream()
        header_size = bStream.padTo32Delta(0xC*len(self.textures)) + (0xC*len(self.textures))
        
        texture_offsets = []
        for texture in self.textures:
            texture_offsets.append(data_section.tell())
            data_section.write(texture[2])

        for x in range(0, len(texture_offsets)):
            header_section.write(struct.pack(">HHBBHI", self.textures[x][0], self.textures[x][1], 0x0E, 0, 0, texture_offsets[x] + header_size))
        
        header_section.padTo32(header_section.tell())
        header_section.seek(0)
        data_section.seek(0)
        stream.write(header_section.read())
        stream.write(data_section.read())
        header_section.close()
        data_section.close()
