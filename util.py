from ctypes import sizeof


def align(val: int, bits: int) -> int:
    return (val + (bits - 1)) & ~(bits - 1)


def read_struct(file, struct_type):
    struct_size = sizeof(struct_type)
    data = file.read(struct_size)
    return struct_type.from_buffer_copy(data)
