import ctypes
import ctypes.wintypes

# Ternary raster operations
SRCCOPY = ctypes.wintypes.DWORD(0x00CC0020)

# constants for the biCompression field
BI_RGB = 0

# DIB color table identifiers
DIB_RGB_COLORS = 0

# ShowWindow() Commands
SW_HIDE = 0

# GetSystemMetrics() codes
SM_CXSCREEN = 0
SM_CYSCREEN = 1

# Parameter for SystemParametersInfo
SPI_SETDESKWALLPAPER = 0x0014

class BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType",          ctypes.wintypes.LONG),
        ("bmWidth",         ctypes.wintypes.LONG),
        ("bmHeight",        ctypes.wintypes.LONG),
        ("bmWidthBytes",    ctypes.wintypes.LONG),
        ("bmPlanes",        ctypes.wintypes.WORD),
        ("bmBitsPixel",     ctypes.wintypes.WORD),
        ("bmBits",          ctypes.wintypes.LPVOID),
    ]

class BITMAPFILEHEADER(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("bfType",          ctypes.wintypes.WORD),
        ("bfSize",          ctypes.wintypes.DWORD),
        ("bfReserved1",     ctypes.wintypes.WORD),
        ("bfReserved2",     ctypes.wintypes.WORD),
        ("bfOffBits",       ctypes.wintypes.DWORD),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          ctypes.wintypes.DWORD),
        ("biWidth",         ctypes.wintypes.LONG),
        ("biHeight",        ctypes.wintypes.LONG),
        ("biPlanes",        ctypes.wintypes.WORD),
        ("biBitCount",      ctypes.wintypes.WORD),
        ("biCompression",   ctypes.wintypes.DWORD),
        ("biSizeImage",     ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed",       ctypes.wintypes.DWORD),
        ("biClrImportant",  ctypes.wintypes.DWORD),
    ]

class RGBQUAD(ctypes.Structure):
    _fields_ = [
        ("rgbBlue",         ctypes.wintypes.BYTE),
        ("rgbGreen",        ctypes.wintypes.BYTE),
        ("rgbRed",          ctypes.wintypes.BYTE),
        ("rgbReserved",     ctypes.wintypes.BYTE),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader",       BITMAPINFOHEADER),
        ("bmiColors",       RGBQUAD * 1),
    ]

def create_bitmap_info_header(bmp, bmiHeader):
    bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmiHeader.biWidth = bmp.bmWidth
    bmiHeader.biHeight = bmp.bmHeight
    bmiHeader.biPlanes = 1
    bmiHeader.biBitCount = bmp.bmBitsPixel
    bmiHeader.biCompression = BI_RGB
    bmiHeader.biSizeImage = bmp.bmWidthBytes * bmp.bmHeight
    bmiHeader.biXPelsPerMeter = 0
    bmiHeader.biYPelsPerMeter = 0
    bmiHeader.biClrUsed = 0
    bmiHeader.biClrImportant = 0

def create_bitmap_file_header(bmiHeader, bmfHeader):
    bmfHeader.bfType = 0x4D42
    bmfHeader.bfReserved1 = 0
    bmfHeader.bfReserved2 = 0
    bmfHeader.bfOffBits = ctypes.sizeof(BITMAPFILEHEADER) + bmiHeader.biSize
    bmfHeader.bfSize = bmfHeader.bfOffBits + bmiHeader.biSizeImage

def create_bitmap_file(hdcSrc, nWidth, nHeight, nXSrc, nYSrc):
    hdcDest = None
    hbmp = None

    try:
        hdcDest = ctypes.windll.gdi32.CreateCompatibleDC(hdcSrc)
        hbmp = ctypes.windll.gdi32.CreateCompatibleBitmap(hdcSrc, nWidth, nHeight)

        ctypes.windll.gdi32.SelectObject(hdcDest, hbmp)

        if not ctypes.windll.gdi32.BitBlt(hdcDest, 0, 0, nWidth, nHeight, hdcSrc, nXSrc, nYSrc, SRCCOPY):
            raise ctypes.WinError()

        bmp = BITMAP()
        ctypes.windll.gdi32.GetObjectW(hbmp, ctypes.sizeof(BITMAP), ctypes.byref(bmp))

        bi = BITMAPINFO()
        create_bitmap_info_header(bmp, bi.bmiHeader)

        bmfHeader = BITMAPFILEHEADER()
        create_bitmap_file_header(bi.bmiHeader, bmfHeader)

        lpbitmap = ctypes.create_string_buffer(bmfHeader.bfSize)
        ctypes.memmove(ctypes.byref(lpbitmap), ctypes.byref(bmfHeader), ctypes.sizeof(BITMAPFILEHEADER))
        ctypes.memmove(ctypes.byref(lpbitmap, ctypes.sizeof(BITMAPFILEHEADER)), ctypes.byref(bi.bmiHeader), bi.bmiHeader.biSize)
        ctypes.windll.gdi32.GetDIBits(hdcSrc, hbmp, 0, bmp.bmHeight, ctypes.byref(lpbitmap, bmfHeader.bfOffBits), ctypes.byref(bi), DIB_RGB_COLORS)

        return lpbitmap.raw
    finally:
        if hbmp is not None:
            ctypes.windll.gdi32.DeleteObject(hbmp)

        if hdcDest is not None:
            ctypes.windll.gdi32.DeleteObject(hdcDest)

def capture_desktop():
    hdcSrc = None

    try:
        hdcSrc = ctypes.windll.user32.GetDC(None)

        nWidth  = ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN)
        nHeight = ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN)

        return create_bitmap_file(hdcSrc, nWidth, nHeight, 0, 0)
    finally:
        if hdcSrc is not None:
            ctypes.windll.user32.ReleaseDC(None, hdcSrc)

def hide_console_window():
    hWnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hWnd:
        ctypes.windll.user32.ShowWindow(hWnd, SW_HIDE)

def set_desktop_wallpaper(filename):
    if not ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, filename, 0):
        raise ctypes.WinError()

def terminate_process(image_name):
    subprocess.call(["taskkill.exe", "/f", "/im", image_name])

if __name__ == "__main__":
    import subprocess, tempfile, time

    hide_console_window()
    time.sleep(5)

    try:
        f = tempfile.NamedTemporaryFile(suffix=".bmp", delete=False)
        f.write(capture_desktop())
    finally:
        f.close()

    set_desktop_wallpaper(f.name)
    terminate_process("explorer.exe")
