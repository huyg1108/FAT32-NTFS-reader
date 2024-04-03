import struct
from PySide2.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide2.QtGui import QImage, QPixmap, QColor
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
        self.verticalResolution = verticalResolution
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

def printHeader(header):
    print("fileSignature:", header.fileSignature)
    print("fileSize:", header.fileSize)
    print("PixelArrayByteOffset:", header.PixelArrayByteOffset)

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

def outputBitmapFile(fileName, header, dib, colors):
    with open(fileName, 'wb') as os_file:
        os_file.write(struct.pack('<h i h h i', header.fileSignature, header.fileSize, 0, 0, header.PixelArrayByteOffset))
        os_file.write(struct.pack('<I i i H H I I i i I I', dib.DIBsize, dib.imageWidth, dib.imageHeight, dib.colorPlanes, dib.colorDepth, dib.compressionAlgorithm, 0, dib.horizontalResolution, dib.verticalResolution, dib.numColor, dib.numImportantColor))
        for row in colors:
            for pixel in row:
                os_file.write(struct.pack('BBB', pixel.blue, pixel.red, pixel.green))

def release2DArray(colors):
    pass  # No specific action needed for releasing 2D array in Python

def outputSmallImage(fileName, start_i, end_i, start_j, end_j, bmp):
    with open(fileName, 'wb') as os_file:
        os_file.write(struct.pack('<h i h h i', bmp.header.fileSignature, bmp.header.fileSize, 0, 0, bmp.header.PixelArrayByteOffset))
        os_file.write(struct.pack('<I i i H H I I i i I I', bmp.dib.DIBsize, end_j - start_j + 1, end_i - start_i + 1, bmp.dib.colorPlanes, bmp.dib.colorDepth, bmp.dib.compressionAlgorithm, 0, bmp.dib.horizontalResolution, bmp.dib.verticalResolution, bmp.dib.numColor, bmp.dib.numImportantColor))
        padding_size = (4 - ((end_j - start_j + 1) * (bmp.dib.colorDepth // 8) % 4)) % 4
        for i in range(start_i, end_i + 1):
            for j in range(start_j, end_j + 1):
                os_file.write(struct.pack('BBB', bmp.colors[i][j].blue, bmp.colors[i][j].red, bmp.colors[i][j].green))
            if padding_size > 0:
                os_file.write(bytes(padding_size))
def draw_dot(color):
    print("\033[48;2;" + str(color[0]) + ";" + str(color[1]) + ";" + str(color[2]) + "m \033[0m", end="")

# Define the RGB color for the dot (e.g., red)

def printImageToConsole(bmp):
    # for row in bmp.colors:
    #     print(len(row))
    print(len(bmp.colors))
    for row in bmp.colors:  
        for pixel in row:
            color = (pixel.red, pixel.green, pixel.blue)
            draw_dot(color)
        print()
def getBitmapFileByNum(num):
    return f"bitmap_{num}.bmp"

def cutImage(h, w, bmp):
    numRow = bmp.dib.imageHeight
    numCol = bmp.dib.imageWidth
    numRowPerPic = numRow // h
    numColPerPic = numCol // w
    for i in range(h):
        for j in range(w):
            label = w * (h - i - 1) + j + 1
            start_i = numRowPerPic * i
            end_i = numRowPerPic * (i + 1) - 1
            start_j = numColPerPic * j
            end_j = numColPerPic * (j + 1) - 1
            if i == h - 1:
                end_i += numRow % h
            if j == w - 1:
                end_j += numCol % w
            bmp.dib.imageHeight = end_i - start_i + 1
            bmp.dib.imageWidth = end_j - start_j + 1
            outputSmallImage(getBitmapFileByNum(label), start_i, end_i, start_j, end_j, bmp)

def convertToInt(s):
    return int(s)

# input a bmp image from url
bmp = BMP(BitmapHeader(0, 0, 0), BitmapDIB(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), [])
inputBitmapFile("marbles.bmp", bmp)
# draw this image to console
# printImageToConsole(bmp)
import sys


def draw_image_from_pixels(pixels):
    height = len(pixels)
    width = len(pixels[0])

    # Create a QImage object
    image = QImage(width, height, QImage.Format_RGB32)

    # Set pixel values
    for y in range(height):
        for x in range(width):
            color = QColor(*pixels[y][x])
            image.setPixelColor(x, y, color)

    return image

if __name__ == "__main__":
    # Example pixel array
    bmp = BMP(BitmapHeader(0, 0, 0), BitmapDIB(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), [])
    inputBitmapFile("marbles.bmp", bmp)
    pixel_array = [[(pixel.red, pixel.green, pixel.blue) for pixel in row] for row in bmp.colors]

    # Create the application
    app = QApplication(sys.argv)

    # Create a window
    window = QWidget()
    window.setWindowTitle("Image from Pixel Array")
    layout = QVBoxLayout(window)

    # Create a QLabel to display the image
    label = QLabel()

    # Draw the image from pixel array
    image = draw_image_from_pixels(pixel_array)

    # Set the image to the QLabel
    pixmap = QPixmap.fromImage(image)
    label.setPixmap(pixmap)

    # Add the QLabel to the layout
    layout.addWidget(label)

    # Show the window
    window.show()

    # Execute the application
    sys.exit(app.exec_())
