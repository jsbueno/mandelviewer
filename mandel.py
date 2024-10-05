import math

import pygame
from pygame import Vector2 as V2

class RenderCancel(Exception):
    pass

class ExitApp(Exception):
    pass

W, H = SIZE = V2(800, 600)

class Mandelbrot:
    def __init__(self, screen, palette, max_iter, c1=V2(-2,1), c2=V2(1,-1)):
        self.sc = screen
        self.palette = palette
        self.c1 = c1
        self.c2 = c2
        self.size = V2(screen.get_size())
        self.max_iter = max_iter

        self.prev_click = None
        self.rendering = False


    def screen_to_graph(self, pos, return_complex=True) -> complex | V2:
        cw = self.c2.x - self.c1.x
        ch = self.c2.y - self.c1.y
        cx = cw / self.size.x * pos[0] + self.c1.x
        cy = ch / self.size.y * pos[1] + self.c1.y
        if return_complex:
            return cx + cy * 1j
        return V2(cx, cy)

    def graph_to_screen(self, pos: complex | V2) -> V2:
        # (?? untested for now)
        if isinstance(pos, complex):
            pos = V2(pos.real, pos.imag)
        cw = self.c2.x - self.c1.x
        ch = self.c2.y - self.c1.y
        cx = int(self.size.x / cw * pos[0]) - self.c1.x
        cy = int(self.size.y / ch * pos[1]) - self.c1.y
        return V2(cx, cy)

    def iter_corners(self, update=True):
        sc = self.sc
        size = self.size
        palette = self.palette
        mandel = self.mandel

        w, h = map(int, size)
        c1 = self.c1
        c2 = self.c2

        x0, y0 = c1
        x1, y1 = c2
        cw = x1 - x0
        ch = y1 - y0
        self.rendering = True
        try:
            for y in range(h):
                for x in range(w):
                    target = self.screen_to_graph((x, y))
                    value = mandel(target)
                    sc.set_at((x,y), palette[value % len(palette)])
                if y % 50 == 0:
                    if update:
                        pygame.display.flip()
                    self.handle()
            if update:
                pygame.display.flip()
        except RenderCancel:
            return
        finally:
            self.rendering = False

    def inline_iter_corners(self, update=True):
        # function kept so it can be (cythonized/Czised/rustificated/zigfied later on)
        sc = self.sc
        size = self.size
        palette = self.palette
        mandel = self.mandel


        w, h = map(int, size)
        c1 = self.c1
        c2 = self.c2

        x0, y0 = c1
        x1, y1 = c2
        cw = x1 - x0
        ch = y1 - y0
        try:
            for y in range(h):
                for x in range(w):
                    cx = cw / w * x + x0
                    cy = ch / h * y + y0
                    value = mandel(cx, cy)
                    sc.set_at((x,y), palette[value % len(palette)])
                if y % 50 == 0:
                    if update:
                        pygame.display.flip()
                    self.handle()
            if update:
                pygame.display.flip()
        except RenderCancel:
            return

    def mandel(self, c: complex) -> int:
        #c = x + y * 1j
        z = 0
        for i in range(self.max_iter):
            z = z ** 2 + c
            if abs(z) > 2:
                return i
        return self.max_iter

    def handle(self):
        for event in pygame.event.get():
            if event.type==pygame.KEYDOWN:
                if event.unicode in ("\x1b", "q"):  #  <ESC>
                    raise RenderCancel()
            elif event.type==pygame.WINDOWCLOSE:
                raise ExitApp
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event)
                print(event.pos)
            elif event.type == RE_RENDER:
                if self.rendering:
                    pygame.event.post(event)
                    raise RenderCancel()
                self.iter_corners()

    def handle_click(self, event):
        pos = event.pos
        if not self.prev_click:
            self.prev_click = pos
            return
        # second click - change rendering window:

        # TBD: maybe use a lock - these two have to change at once, and any rendering must be cancelled
        self.c1 = self.screen_to_graph(self.prev_click, False)
        self.c2 = self.screen_to_graph(pos, False)
        self.prev_click = None
        print(f"new corners: {self.c1} - {self.c2}")
        pygame.event.post(pygame.Event(RE_RENDER))
        if self.rendering:
            raise RenderCancel()


def init():
    global sc, max_iter, pal2, RE_RENDER
    pygame.init()
    max_iter = 100
    sc = pygame.display.set_mode(SIZE)
    pal2  = {i: (i,  int(255 * math.sin(i/255 * math.pi)) , 255 - i) for i in range(255)}
    RE_RENDER  = pygame.event.custom_type()


def main():
    mandel = Mandelbrot(sc, max_iter=max_iter, palette=pal2)
    mandel.iter_corners()
    while True:
        mandel.handle()

        pygame.time.delay(100)
        pygame.display.flip()

if __name__ == "__main__":
    init()
    try:
        main()
    except (RenderCancel, ExitApp):
        pass
    finally:
        pygame.quit()

