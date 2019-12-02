import math
from bStream import *

def GeneratePrimitives(mesh, buffer, start=0):
    for x in range(len(mesh.indices) // 3):
        buffer.writeUInt8(0x90)
        buffer.writeUInt16(3)
        for idx in range(3):
            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].vertex_index)
            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].normal_index)
            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].texcoord_index)

class BatchManager():
    def __init__(self, shapes):
        total = 0
        self.batches = []
        for shape in shapes:
            self.batches.append(Batch(shape, total))
            total += len(shape.mesh.indices)

    def write(self, stream):
        batch_headers = bStream()
        primitive_buffer = bStream()
        primitives_start = (0x18 * len(self.batches))

        for batch in self.batches:
            list_start = primitive_buffer.tell()
            primitive_buffer.write(batch.primitives.read())
            list_end = primitive_buffer.tell()
            batch.writeHeader(batch_headers, math.ceil((list_end - list_start)/32), list_start + primitives_start)

        batch_headers.seek(0)
        primitive_buffer.seek(0)
        stream.write(batch_headers.read())
        stream.write(primitive_buffer.read())
        batch_headers.close()
        primitive_buffer.close()

class Batch():
    def __init__(self, shape, start):
        # Model should be triangulated !
        if(len(shape.mesh.indices) % 3 != 0):
            raise ValueError("Model not triangles or trianglestrips!")

        self.face_count = math.ceil(len(shape.mesh.indices) / 3)
        self.attributes = (0 | 1 << 9 | 1 << 10 | 1 << 13)
        self.primitives = bStream()
        GeneratePrimitives(shape.mesh, self.primitives)#, start)
        self.primitives.padTo32(self.primitives.tell())
        self.primitives.seek(0)

    def writeHeader(self, stream, list_size, offset):
        stream.writeUInt16(self.face_count)
        stream.writeUInt16(list_size)
        stream.writeUInt32(self.attributes)
        stream.writeUInt8(1) # Use Normals
        stream.writeUInt8(1) # Use Positions
        stream.writeUInt8(1) # Uv Count
        stream.writeUInt8(0) # Use NBT
        stream.writeUInt32(offset)
        stream.pad(8)
        #stream.padTo32()

    def __del__(self):
        if(self.primitives is not None):
            self.primitives.close()

