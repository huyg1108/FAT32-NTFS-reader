import sys
import struct
from PySide2.QtGui import QImage, QColor

class BitmapHeader:
    def __init__(self, fileSignature, fileSize, PixelArrayByteOffset):
        self.fileSignature = fileSignature
        self.fileSize = fileSize
        self.PixelArrayByteOffset = PixelArrayByteOffset

class BitmapDIB:
    def __init__(self, DIBsize, imageWidth, imageHeight, colorPlanes, colorDepth, compressionAlgorithm, pixelArraySize, horizontalResolution, verticalResolution, numColor, numImportantColor):
        self.DIBsize = DIBsize
        self.imageWidth = imageWidth
        self.imageHeight = imageHeight
        self.colorPlanes = colorPlanes
        self.colorDepth = colorDepth
        self.compressionAlgorithm = compressionAlgorithm
        self.pixelArraySize = pixelArraySize
        self.horizontalResolution = horizontalResolution
        self.numColor = numColor
        self.numImportantColor = numImportantColor

class Color:
    def __init__(self, blue, red, green):
        self.blue = blue
        self.red = red
        self.green = green

class BMP:
    def __init__(self, header, dib, colors):
        self.header = header
        self.dib = dib
        self.colors = colors

def readHeader(header, is_file):
    is_file.seek(0)
    header_data = is_file.read(14)
    header.fileSignature, header.fileSize, _, _, header.PixelArrayByteOffset = struct.unpack('<h i h h i', header_data)

def readDIB(dib, is_file):
    is_file.seek(14)
    dib_data = is_file.read(40)
    dib.DIBsize, dib.imageWidth, dib.imageHeight, dib.colorPlanes, dib.colorDepth, dib.compressionAlgorithm, dib.pixelArraySize, dib.horizontalResolution, dib.verticalResolution, dib.numColor, dib.numImportantColor = struct.unpack('<I i i H H I I i i I I', dib_data)

def readColor(colors, numRow, numCol, numDepth, is_file):
    colors.clear()
    padding_size = (4 - (numCol * (numDepth // 8) % 4)) % 4
    for i in range(numRow):
        row_data = is_file.read(numCol * numDepth // 8)
        row = [Color(*struct.unpack('BBB', row_data[j*3:(j+1)*3])) for j in range(numCol)]
        colors.append(row)
        if padding_size > 0:
            is_file.read(padding_size)

def inputBitmapFile(fileName, bmp):
    with open(fileName, 'rb') as is_file:
        readHeader(bmp.header, is_file)
        readDIB(bmp.dib, is_file)
        readColor(bmp.colors, bmp.dib.imageHeight, bmp.dib.imageWidth, bmp.dib.colorDepth, is_file)

def draw_image_from_pixels(pixels):
    height = len(pixels)
    width = len(pixels[0])

    image = QImage(width, height, QImage.Format_RGB32)

    for y in range(height):
        # Kiểm tra độ dài của hàng trước khi truy cập
        if len(pixels[y]) != width:
            raise ValueError("Hàng {} không có độ dài phù hợp".format(y))
        
        for x in range(width):
            color = QColor(*pixels[y][x])
            # Sửa lại tọa độ y
            image.setPixelColor(x, height - y - 1, color)

    return image