import mmap
import os
import struct
import sys
from pathlib import Path


def clear_executable_stack(path: Path) -> None:
    if not path.exists():
        print(f"Skipping torch execstack patch; missing: {path}", flush=True)
        return

    with path.open("r+b") as handle:
        data = mmap.mmap(handle.fileno(), 0)
        try:
            if data[:4] != b"\x7fELF" or data[4] != 2:
                raise RuntimeError(f"{path} is not a 64-bit ELF file")

            endian = "<" if data[5] == 1 else ">"
            e_phoff = struct.unpack_from(endian + "Q", data, 32)[0]
            e_phentsize = struct.unpack_from(endian + "H", data, 54)[0]
            e_phnum = struct.unpack_from(endian + "H", data, 56)[0]

            for index in range(e_phnum):
                offset = e_phoff + index * e_phentsize
                p_type = struct.unpack_from(endian + "I", data, offset)[0]
                if p_type != 0x6474E551:  # PT_GNU_STACK
                    continue

                p_flags_offset = offset + 4
                p_flags = struct.unpack_from(endian + "I", data, p_flags_offset)[0]
                new_flags = p_flags & ~0x1  # clear PF_X
                if new_flags != p_flags:
                    struct.pack_into(endian + "I", data, p_flags_offset, new_flags)
                    data.flush()
                    print(f"Cleared executable stack flag for {path}: {p_flags} -> {new_flags}", flush=True)
                else:
                    print(f"Executable stack flag already clear for {path}", flush=True)
                return

            raise RuntimeError(f"{path} has no PT_GNU_STACK header")
        finally:
            data.close()


torch_cpu = Path("/app/env_sadtalker/lib/python3.10/site-packages/torch/lib/libtorch_cpu.so")
clear_executable_stack(torch_cpu)

os.execvp(sys.executable, [sys.executable, "app.py"])
