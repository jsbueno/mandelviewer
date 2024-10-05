import math

import pygame

W, H = SIZE = 800, 600

class Mandelbrot:
    def __init__(self, screen, palette):
        self.sc = screen
        self.palette = palette

    def iter_corners(self, size, c1, c2, update=True):
        sc = self.sc
        palette = self.palette
        mandel = self.mandel

        w, h = size

        x0, y0 = c1
        x1, y1 = c2
        cw = x1 - x0
        ch = y1 - y0

        for y in range(h):
            for x in range(w):
                cx = cw / w * x + x0
                cy = ch / h * y + y0
                value = mandel(cx, cy)
                sc.set_at((x,y), palette[value % len(palette)])
            if update and y % 50 == 0:
                pygame.display.flip()
        if update:
            pygame.display.flip()

    def mandel(self, x, y):
        c = x + y * 1j
        z = 0
        for i in range(max_iter):
            z = z ** 2 + c
            if abs(z) > 2:
                return i
        return max_iter

    def handle(self, event):
        print(event.pos)


def init():
    global sc, max_iter, pal2
    max_iter = 100
    sc = pygame.display.set_mode((W, H))
    pal2  = {i: (i,  int(255 * math.sin(i/255 * math.pi)) , 255 - i) for i in range(255)}


def main():
    mandel = Mandelbrot(sc, palette=pal2)
    mandel.iter_corners((W, H), (0.25, 0.5 ), (0.5,0.25))
    while True:
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.unicode == "\x1b":  #  <ESC>
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mandel.handle(event)

        pygame.time.delay(100)
        pygame.display.flip()

if __name__ == "__main__":
    init()
    try:
        main()
    finally:
        pygame.quit()

