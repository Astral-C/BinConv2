import math
import numpy as np
from bStream import *

def GeneratePrimitives(mesh, buffer, nbt, start=0):
    normal_offset = 0
    for x in range(len(mesh.indices) // 3):
        buffer.writeUInt8(0x90)
        buffer.writeUInt16(3)
        for idx in range(3):
            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].vertex_index)
            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].normal_index + normal_offset)
            
            if(nbt):
                buffer.writeUInt16(start + mesh.indices[(x*3) + idx].normal_index + normal_offset + 1)
                buffer.writeUInt16(start + mesh.indices[(x*3) + idx].normal_index + normal_offset + 2)
                normal_offset += 2

            buffer.writeUInt16(start + mesh.indices[(x*3) + idx].texcoord_index)

class BatchManager():
    def __init__(self, shapes, materials, use_bump):
        total = 0
        self.batches = []
        for shape in shapes:
            self.batches.append(Batch(shape, total, (materials[shape.mesh.material_ids[0]].bump_texname is not None) and use_bump))
            total += len(shape.mesh.indices)

    @staticmethod
    def CalculateTangentSpace(shapes, materials, attrib):
        nbt_data = []
        #Loop through all triangles of each shape
        tangents = [None for x in range(len(attrib.normals))]
        binormals = [None for x in range(len(attrib.normals))]
        for shape in shapes:
            mesh = shape.mesh
            if(materials[mesh.material_ids[0]].bump_texname is not None):
                for x in range(len(mesh.indices) // 3):
                    
                    #Disgusting
                    #Get triangle indices
                    tr0 = mesh.indices[(x*3)]
                    tr2 = mesh.indices[(x*3)+1]
                    tr1 = mesh.indices[(x*3)+2]

                    p0 = np.array(attrib.vertices[tr0.vertex_index : tr0.vertex_index + 3])
                    p1 = np.array(attrib.vertices[tr1.vertex_index : tr1.vertex_index + 3])
                    p2 = np.array(attrib.vertices[tr2.vertex_index : tr2.vertex_index + 3])
                    
                    n0 = np.array(attrib.normals[tr0.normal_index : tr0.normal_index + 3])
                    n1 = np.array(attrib.normals[tr1.normal_index : tr1.normal_index + 3])
                    n2 = np.array(attrib.normals[tr2.normal_index : tr2.normal_index + 3])

                    tx0 = np.array(attrib.texcoords[tr0.texcoord_index : tr0.texcoord_index + 2])
                    tx1 = np.array(attrib.texcoords[tr1.texcoord_index : tr1.texcoord_index + 2])
                    tx2 = np.array(attrib.texcoords[tr2.texcoord_index : tr2.texcoord_index + 2])

                    edge1 = p1 - p0
                    edge2 = p2 - p0

                    uv1 = tx1 - tx0
                    uv2 = tx2 - tx0

                    r = (-1.0 if (uv1[1] * uv2[0] - uv1[0] * uv2[1]) < 0.0 else 1.0)

                    if(uv1[0] * uv2[1] == uv1[1] * uv2[0]):
                        uv1[0] = 0.0
                        uv1[1] = 1.0
                        uv1[0] = 1.0
                        uv1[1] = 0.0

                    tangent = np.array([
                        ((edge2[0] * uv1[1]) - (edge1[0] * uv2[1])) * r,
                        ((edge2[1] * uv1[1]) - (edge1[1] * uv2[1])) * r,
                        ((edge2[2] * uv1[1]) - (edge1[2] * uv2[1])) * r
                    ])

                    print(tangent)

                    lt0 = tangent + n0 * (tangent * n0)
                    lt1 = tangent + n1 * (tangent * n1)
                    lt2 = tangent + n2 * (tangent * n2)

                    binorm0 = np.cross(n0, lt0) 
                    binorm1 = np.cross(n1, lt1)
                    binorm2 = np.cross(n2, lt2)

                    for x in range(3):
                        tangents[tr0.normal_index + x] = lt0[x]
                        tangents[tr1.normal_index + x] = lt1[x]
                        tangents[tr2.normal_index + x] = lt2[x]

                        binormals[tr0.normal_index + x] = binorm0[x]
                        binormals[tr1.normal_index + x] = binorm1[x]
                        binormals[tr2.normal_index + x] = binorm2[x]
        
        #Now that were done calculating tangents and binormals for each thing, we need to copy them to a vertex array
        #go though a second time for cleaness
        for shape in shapes:
            mesh = shape.mesh
            if(materials[mesh.material_ids[0]].bump_texname is not None):
                for idx in mesh.indices:
                    nbt_data.extend(attrib.normals[idx.normal_index : idx.normal_index + 3])
                    nbt_data.extend(binormals[idx.normal_index : idx.normal_index + 3])
                    nbt_data.extend(tangents[idx.normal_index : idx.normal_index + 3])
            else:
                nbt_data.extend(attrib.normals[idx.normal_index : idx.normal_index + 3])

        return nbt_data



    def write(self, stream):
        batch_headers = bStream()
        primitive_buffer = bStream()
        
        batch_headers.pad((0x18 * len(self.batches)))
        batch_headers.padTo32(batch_headers.tell())
        primitives_start = batch_headers.tell()
        batch_headers.seek(0)

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
    def __init__(self, shape, start, nbt):
        # Model should be triangulated !
        if(len(shape.mesh.indices) % 3 != 0):
            raise ValueError("Model not triangles or trianglestrips!")

        self.face_count = math.ceil(len(shape.mesh.indices) / 3)
        self.attributes = (0 | 1 << 9 | 1 << 10 | 1 << 13)
        self.primitives = bStream()
        #SpaceCats: I dont like this, nbt should only be on where its used.
        #TODO: Find a way to only enable nbt on only meshes that use it
        self.useNBT = nbt
        GeneratePrimitives(shape.mesh, self.primitives, self.useNBT)
        self.primitives.padTo32(self.primitives.tell())
        self.primitives.seek(0)

    def writeHeader(self, stream, list_size, offset):
        stream.writeUInt16(self.face_count)
        stream.writeUInt16(list_size)
        stream.writeUInt32(self.attributes)
        stream.writeUInt8(1) # Use Normals
        stream.writeUInt8(1) # Use Positions
        stream.writeUInt8(1) # Uv Count
        stream.writeUInt8(1 if self.useNBT else 0) # Use NBT
        stream.writeUInt32(offset)
        stream.pad(8)

    def __del__(self):
        if(self.primitives is not None):
            self.primitives.close()

