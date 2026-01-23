'''
Standalone program for detecting if the local filesystem is Fat or LittleFS.
LittleFS is preferred as it provides wear levelling.
'''
import rp2

bdev = rp2.Flash()

buf = bytearray(16)

bdev.readblocks(0, buf)

if buf[8:16] == b'littlefs':
    print("LittleFS")
elif buf[3:11] == b'MSDOS5.0':
    print("FAT")
else:
    print("Unknown:", buf)
