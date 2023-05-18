import webbrowser, pygame

def open_website(_, link):
    webbrowser.open(link)

def underline(surf, *, color):
    w, h = surf.get_width(), surf.get_height()
    pygame.draw.line(surf, color, (0, h-4), (w, h-4))

def strikethrough(surf, *, color):
    w, h = surf.get_width(), surf.get_height()
    pygame.draw.line(surf, color, (0, (h//2)+1), (w, (h//2)+1))
