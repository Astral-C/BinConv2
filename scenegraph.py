from bStream import *

class GraphObject():
	def __init__(self, shapes):
		self.parent_index = -1
		self.child_index = -1
		self.next_index = -1
		self.prev_index = -1
		self.render_flags = 0x00
		self.scale = [1.0, 1.0, 1.0]
		self.pos = [0.0, 0.0, 0.0]
		self.rot = [0.0, 0.0, 0.0]
		self.bbmin = [0.0, 0.0, 0.0]
		self.bbmax = [0.0, 0.0, 0.0]
		self.part_count = len(shapes)
		self.part_offset = 0x8C #only one graph object for now. will update this in the future for 4th wall support
		self.parts = []

	def write(self, stream, offset):
		stream.writeInt16(self.parent_index)
		stream.writeInt16(self.child_index)
		stream.writeInt16(self.next_index)
		stream.writeInt16(self.prev_index)
		stream.pad(1)
		stream.writeUInt8(self.render_flags)
		stream.pad(2)
		for flt in self.scale:
			stream.writeFloat(flt)
		for flt in self.rot:
			stream.writeFloat(flt)
		for flt in self.pos:
			stream.writeFloat(flt)
		for flt in self.bbmin:
			stream.writeFloat(flt)
		for flt in self.bbmax:
			stream.writeFloat(flt)
		stream.writeFloat(0)
		stream.writeUInt16(self.part_count)
		stream.pad(2)
		back = stream.tell()
		stream.writeUInt32(0x70)
		#print("Wrote Part Offset {0:X}".format((stream.tell()  + (4 * 7)) - offset))
		stream.writeUInt32List([0 for x in range(7)])
		stream.padTo32(stream.tell())
		
		offset = (stream.tell() - offset)
		for part in self.parts:
			stream.writeInt16(part[1])
			stream.writeInt16(part[0])
		stream.seek(back)
		stream.writeUInt32(offset)
		