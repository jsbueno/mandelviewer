import math

import pygame
from pygame import Vector2 as V2

class RenderCancel(Exception):
    pass

class ExitApp(Exception):
    pass

W, H = SIZE = V2(800, 600)

button_bg = (192, 192, 192)

def center_blit(bg, fg):
    pw, ph = bg.get_size()
    w, h = fg.get_size()
    corner_x = (pw - w) // 2
    corner_y = (ph - h) // 2
    bg.blit(fg, (corner_x, corner_y))
    return bg

def stamp_str(bg: pygame.Surface, text: str):
    text_img = font.render(text, True, (0,0,0))
    return center_blit(bg, text_img)

class Button(pygame.sprite.Sprite):
    def __init__(self, rect, character, action):
        super().__init__()
        self.rect = rect
        self.image = pygame.Surface(rect.size)
        self.image.fill(button_bg)
        self.image = stamp_str(self.image, character)
        self.action = action

    def render(self, canvas):
        canvas.blit(self.image, self.rect)

    def hit(self, pos):
        return self.rect.collidepoint(pos)



class Controls:

    button_data = {
        "undo": ("Z", "undo"),
        "square": ("R", "square"),
    }

    def __init__(self, parent):
        self.parent = parent
        self.size = V2(parent.screen.get_size())
        self.canvas = pygame.Surface(self.size).convert_alpha()
        self.buttons = pygame.sprite.Group()
        self.reset()

    def reset(self):
        self.buttons.empty()
        self.create_buttons()
        self.clear()

    def clear(self):
        self.canvas.fill((255,255,255, 0))
        self.render_buttons()

    def render_buttons(self):
        for button in self.buttons:
            self.canvas.blit(button.image, button.rect)

    def create_buttons(self):
        self.grid = dict()
        grid_spacing = self.size.x // 15
        button_size = 20  # Height in pixels
        current_x = self.size.x - grid_spacing
        current_y = self.size.y - grid_spacing
        for button_name, data in self.button_data.items():
            button = Button(
                pygame.Rect((current_x, current_y, button_size, button_size)),
                character = data[0],
                action = getattr(self.parent, data[1]),
            )
            self.buttons.add(button)
            current_y -= grid_spacing

    def rect(self,  rect):
        pygame.draw.rect(self.canvas, (255, 0, 0), tuple(map(int, rect)), 3)

    def handle(self, event):
        pos = event.pos
        for button in self.buttons:
            if button.hit(pos):
                button.action()
                return True

        return False

class Mandelbrot:
    def __init__(self, screen, palette, max_iter, c1=V2(-2,1), c2=V2(1,-1)):
        self.screen = screen
        self.canvas = pygame.Surface(screen.get_size()).convert_alpha()
        self.controls = Controls(self)

        self.palette = palette
        self.c1 = c1
        self.c2 = c2
        self.size = V2(screen.get_size())
        self.max_iter = max_iter

        self.prev_click = None
        self.rendering = False
        self.display_controls = True

        self.window_stack = []

    def update(self):
        self.screen.blit(self.canvas, (0, 0))
        if self.display_controls:
            self.screen.blit(self.controls.canvas, (0, 0))
        pygame.display.flip()


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
        sc = self.canvas
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
                        self.update()
                    self.handle()
            self.update()
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
                if event.unicode == "\x09":
                    self.display_controls = not self.display_controls
            elif event.type==pygame.WINDOWCLOSE:
                raise ExitApp
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.controls.handle(event):
                    self.handle_click(event)
                print(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_move(event)
            elif event.type == RE_RENDER:
                if self.rendering:
                    pygame.event.post(event)
                    raise RenderCancel()
                self.iter_corners()

    def handle_click(self, event):
        pos = event.pos
        if not self.prev_click:
            self.prev_click = V2(pos)
            return
        # second click - change rendering window:

        # TBD: maybe use a lock - these two have to change at once, and any rendering must be cancelled
        self.window_stack.append((self.c1, self.c2))
        self.c1 = self.screen_to_graph(self.prev_click, False)
        self.c2 = self.screen_to_graph(pos, False)
        self.prev_click = None
        self.controls.clear()
        print(f"new corners: {self.c1} - {self.c2}")
        self.re_render()

    def handle_move(self, event):
        pos = V2(event.pos)
        if not self.prev_click:
            return
        print(pos)
        self.controls.clear()
        #c1 = self.graph_to_screen(self.c1)
        #c2 = self.graph_to_screen(self.c2)
        w, h = int(pos.x - self.prev_click.x), int(pos.y - self.prev_click.y)
        self.controls.rect((*self.prev_click, w, h))
        self.update()

    def square(self):
        c2 = V2(self.c2.x, self.c1.y + (self.c2.x - self.c1.x) / 4 * 3)
        self.c2 = c2
        self.re_render()

    def re_render(self):
        pygame.event.post(pygame.Event(RE_RENDER))
        if self.rendering:
            raise RenderCancel()

    def undo(self):
        if self.window_stack:
            self.c1, self.c2 = self.window_stack.pop()
            self.re_render()
        print("undo")

def init():
    global sc, max_iter, pal2, RE_RENDER, font
    pygame.init()
    max_iter = 100
    sc = pygame.display.set_mode(SIZE)
    pal2  = {i: (i,  int(255 * math.sin(i/255 * math.pi)) , 255 - i) for i in range(255)}
    RE_RENDER  = pygame.event.custom_type()
    font = pygame.Font(pygame.font.get_default_font(), 12)


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

