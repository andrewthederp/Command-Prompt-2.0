import threading
import pyperclip
import pygame
import copy
import os

from colors import *

pygame.init()

class CursorShape:
    VINTAGE           = 0
    BAR               = 1
    UNDERSCORE        = 2
    DOUBLE_UNDERSCORE = 3
    FILLED            = 4
    EMPTY             = 5
    INVISIBLE         = 6

class ScrollBar:
    def __init__(self, *, collide_rect, slider_rect):
        self.collide_rect = collide_rect
        self.offset = 0

        self.slider_rect = slider_rect
        self.scrollbar_rect = pygame.Rect((0, 0), (0, 0))
        self.scrollbar_rect.width = self.slider_rect.width-(self.slider_rect.width/4)
        self.scrollbar_rect.centerx = self.slider_rect.centerx

    def update(self, *, events, total_length, offset_num, min_rows, should_scroll):
        for event in events:
            if event.type == pygame.MOUSEWHEEL and should_scroll and self.collide_rect.collidepoint(pygame.mouse.get_pos()):
                self.offset = min(max(0, self.offset+(-offset_num*event.y)), total_length)

        if total_length:
            perc = min_rows/(total_length+min_rows)
            self.scrollbar_rect.h = self.slider_rect.h*perc

            pos = self.offset/(total_length+min_rows)
            self.scrollbar_rect.y = self.slider_rect.h*pos

    def draw(self, screen, *, draw_scrollbar=True, draw_slider=True):
        if draw_slider:
            pygame.draw.rect(screen, (40, 40, 40), self.slider_rect)

        if draw_scrollbar:
            pygame.draw.rect(screen, (135, 135, 135), self.scrollbar_rect, border_radius=3)

class Char:
    def __init__(self, char, ansi, theme):
        self.text = char
        self.ansi = copy.deepcopy(ansi)
        self.text_formattings = {
            'bold':          False,
            'dim':           False,
            'italic':        False,
            'underline':     False,
            'blinking':      False,
            'invis':         False,
            'strikethrough': False
        }

        self.apply_ansi(theme)


    def apply_ansi(self, theme):

        self.foreground_color = themes[theme.lower()]['foreground']
        self.background_color = themes[theme.lower()]['background']

        for ansi_code in self.ansi:
            if ansi_code.startswith('38;2;'):
                try:
                    _, _, r, g, b = ansi_code.split(';')
                except ValueError:
                    pass
                else:
                    self.foreground_color = (int(r), int(g), int(b))
            if ansi_code.startswith('48;2;'):
                try:
                    _, _, r, g, b = ansi_code.split(';')
                except ValueError:
                    pass
                else:
                    self.background_color = (int(r), int(g), int(b))
            elif ansi_code.startswith('38;5;'):
                try:
                    self.foreground_color = bit256_color_converter(int(ansi_code.split(';')[-1]))
                except ValueError:
                    pass
            elif ansi_code.startswith('48;5;'):
                try:
                    self.background_color = bit256_color_converter(int(ansi_code.split(';')[-1]))
                except ValueError:
                    pass
            elif ansi_code == '1':
                self.text_formattings['bold'] = True
            elif ansi_code == '2':
                self.text_formattings['dim'] = True
            elif ansi_code == '3':
                self.text_formattings['italic'] = True
            elif ansi_code == '4':
                self.text_formattings['underline'] = True
            elif ansi_code == '5':
                self.text_formattings['blinking'] = True
            elif ansi_code == '6':
                self.text_formattings['blinking'] = True
            elif ansi_code == '7':
                fg = copy.deepcopy(self.foreground_color)
                bg = copy.deepcopy(self.background_color)
                self.background_color = fg
                self.foreground_color = bg
            elif ansi_code == '8':
                self.text_formattings['invis'] = True
            elif ansi_code == '9':
                self.text_formattings['strikethrough'] = True
            else:
                try:
                    ansi_code = int(ansi_code)
                except ValueError:
                    continue

                if ansi_code in range(30, 38):
                    self.foreground_color = themes[theme.lower()]["8bitcolors"][str(int(ansi_code)-30)]
                elif ansi_code in range(90, 98):
                    self.foreground_color = themes[theme.lower()]["16bitcolors"][str(int(ansi_code)-82)]
                elif ansi_code in range(40, 48):
                    self.background_color = themes[theme.lower()]["8bitcolors"][str(int(ansi_code)-40)]
                elif ansi_code in range(100, 108):
                    self.background_color = themes[theme.lower()]["16bitcolors"][str(int(ansi_code)-92)]

    def __repr__(self):
        return f'<char="{self.text}", foreground_color={self.foreground_color}>, background_color={self.background_color}'

    def change_theme(self, theme):
        self.apply_ansi(theme)


class Window:
    def __init__(self, *, caption="Command prompt 2.0", theme='Campbell'):
        # fps limiter
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # initialising the font. TODO: allow the user to load custom fonts
        self.default_font = pygame.font.Font('./fonts/CascadiaCode.ttf', 20)
        self.bold_default_font = pygame.font.Font('./fonts/CascadiaCode-Bold.ttf', 20)
        self.italic_default_font = pygame.font.Font('./fonts/CascadiaCodeItalic.ttf', 20)
        self.bold_italic_default_font = pygame.font.Font('./fonts/CascadiaCode-BoldItalic.ttf', 20)
        self.cell_size = self.default_font.size('H')


        # window settings
        self.window_columns = 120
        self.window_rows = 30
        self.screen_dimensions = (self.window_columns * self.cell_size[0] + 10, self.window_rows * self.cell_size[1])
        self.screen = pygame.display.set_mode(self.screen_dimensions)
        self.theme = theme

        # .
        self.running = True
        pygame.display.set_caption(caption)

        self.array = [[]]

        self.events = []

        self.word_delimiters = " /\()\"'-.,:;<>~!@#$%^&*|+=[]{}~?│ "

        self.scrollbar = ScrollBar(
            collide_rect=pygame.Rect((0, 0), self.screen_dimensions),
            slider_rect=pygame.Rect((self.screen_dimensions[0]-(self.cell_size[0]*1.8), 0), ((self.cell_size[0]*1.9), self.screen_dimensions[1]))
        )

        # controlling the cursor
        self.cursor_pos = [0, 0]
        self.cursors = self.create_cursors()
        self.cursor = 1
        self.cursor_blinker = 60

        # ansi
        self.current_ansi = []

        # Controlling key input
        self.current_button = None
        self.cooldown = 500
        self.repeat_rate = 25
        self.key_detected = False

        # Selecting
        self.current_select = {'coor':None, 'row_offset':self.scrollbar.offset}
        self.pressing_down = False
        self.smaller, self.bigger = {'coor': [-1, -1], 'row_offset':0}, {'coor': [-1, -1], 'row_offset':0}
        self.shift_direction = -1

    def set_theme(self, theme):
        self.theme = theme
        for row in self.array:
            for char in row:
                char.change_theme(theme)

    def create_cursors(self):
        """Not meant to be used by the user"""
        w, h = self.cell_size

        vintage_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        vintage_cursor_surface.fill((0,0,0,0))
        vintage_cursor = pygame.Rect((0, h-(h/4)), (w, h/4))
        pygame.draw.rect(vintage_cursor_surface, themes[self.theme.lower()]['cursor_col'], vintage_cursor)

        bar_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        bar_cursor_surface.fill((0,0,0,0))
        bar_cursor = pygame.Rect((0, 0), (1, h))
        pygame.draw.rect(bar_cursor_surface, themes[self.theme.lower()]['cursor_col'], bar_cursor)

        underscore_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        underscore_cursor_surface.fill((0,0,0,0))
        underscore_cursor = pygame.Rect((0, h-1), (w, 1))
        pygame.draw.rect(underscore_cursor_surface, themes[self.theme.lower()]['cursor_col'], underscore_cursor)

        double_underscore_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        double_underscore_cursor_surface.fill((0,0,0,0))
        double_underscore_cursor1 = pygame.Rect((0, h-1), (w, 1))
        double_underscore_cursor2 = pygame.Rect((0, h-3), (w, 1))
        pygame.draw.rect(double_underscore_cursor_surface, themes[self.theme.lower()]['cursor_col'], double_underscore_cursor1)
        pygame.draw.rect(double_underscore_cursor_surface, themes[self.theme.lower()]['cursor_col'], double_underscore_cursor2)

        filled_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        filled_cursor_surface.fill((0,0,0,0))
        filled_cursor = pygame.Rect((0, 0), (w, h))
        pygame.draw.rect(filled_cursor_surface, themes[self.theme.lower()]['cursor_col'], filled_cursor)

        empty_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        empty_cursor_surface.fill((0,0,0,0))
        empty_cursor = pygame.Rect((0, 0), (w, h))
        pygame.draw.rect(empty_cursor_surface, themes[self.theme.lower()]['cursor_col'], empty_cursor, 2)

        invis_cursor_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        invis_cursor_surface.fill((0,0,0,0))
        invis_cursor = pygame.Rect((0, 0), (0, 0))
        pygame.draw.rect(invis_cursor_surface, themes[self.theme.lower()]['cursor_col'], invis_cursor)

        return [
            vintage_cursor_surface,
            bar_cursor_surface,
            underscore_cursor_surface,
            double_underscore_cursor_surface,
            filled_cursor_surface,
            empty_cursor_surface,
            invis_cursor_surface
        ]

    def change_cursor(self, cursor):
        self.cursor = cursor

    def print(self, string, *, add=False):
        """Print text to the console"""        
        string = str(string)
        self.cursor_blinker = 60
        x, y = self.cursor_pos

        in_escape_sequence = False
        escape_sequence = ''
        escape_sequence_start = 0

        for coor, char in enumerate(string):
            if char == '\n':
                x = 0
                y += 1
            elif char == "\x1b":
                in_escape_sequence = True
                escape_sequence = ''
                escape_sequence_start = coor
                continue
            elif in_escape_sequence:
                if char in "mK":
                    if escape_sequence != '0' and escape_sequence not in self.current_ansi:
                        self.current_ansi.append(escape_sequence)
                    else:
                        self.current_ansi = []
                    in_escape_sequence = False
                elif char.isdigit() or char == ';':
                    escape_sequence += char
                continue

            if y >= len(self.array):
                num = (y-len(self.array))+1
                for _ in range(num):
                    self.array.append([])
            num = x-len(self.array[y])+1
            for _ in range(num):
                self.array[y].append(Char("", self.current_ansi, self.theme))

            try:
                if add:
                    self.array[y].insert(x, Char(char, self.current_ansi, self.theme))
                else:
                    self.array[y][x] = Char(char, self.current_ansi, self.theme)
            except IndexError:
                print(f"{x=}, {y=}, {self.array}")
            x += 1

        self.cursor_pos[0], self.cursor_pos[1] = x, y
        if y not in range(self.scrollbar.offset, self.scrollbar.offset+self.window_rows):
            if self.scrollbar.offset > y:
                self.scrollbar.offset = y
            else:
                self.scrollbar.offset = (y-self.window_rows)+1

            self.scrollbar.offset += x//self.window_columns

    def delete_text(self, amount=1):
        """Delete `amount` text from the console."""
        self.cursor_blinker = 60
        original_x, original_y = copy.copy(self.cursor_pos)
        x, y = self.cursor_pos
        text_before = self.array[original_y][x:]

        for row in (self.array[:y+1])[::-1]:
            if len(row)-len(text_before) > amount:
                x -= amount
                break
            else:
                y -= 1

                x = len(self.array[y])
                amount -= len(row)
                if y == -1:
                    y = 0
                    break

        if original_y != y:
            for num in range(y+1, original_y+1): # Would have preferred to not use a for loop here but `del` wouldn't work here.
                self.array.pop(num)
            del self.array[y][x:len(self.array[y])-1]
            self.array[y].extend(text_before)
        else:
            del self.array[y][x:original_x]

        self.cursor_pos = [x, y]

    def delete_right(self):
        x, y = self.cursor_pos
        self.array[y] = self.array[y][:x]

    def delete_left(self):
        x, y = self.cursor_pos
        self.array[y] = self.array[y][x:]
        self.cursor_pos[0] = 0

    def delete_row(self):
        """Removes everything on the same row as the cursor"""
        _, y = self.cursor_pos
        try:
            self.array[y] = []
            self.cursor_pos[0] = 0
        except IndexError: # IndexError will never be raised
            pass

    def move_cursor_to(self, x, y):
        """Move the cursor to a certain `x`, `y`"""
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Cursor position values must be integers")
        if x < 0 or y < 0:
            raise ValueError("Cursor position values must be positive")

        if len(self.array) <= y:
            for _ in range(len(self.array), y+1):
                self.array.append([])

        if len(self.array[y]) <= x:
            for _ in range(len(self.array[y]), x+1):
                self.array[y].append(Char('', self.current_ansi, self.theme))

        self.cursor_pos[0], self.cursor_pos[1] = x, y

    def get_pressed_key(self):
        self.key_detected = False
        for event in self.events:
            if event.type == pygame.KEYDOWN and not self.key_detected:
                self.key_detected = True
                if (not self.current_button) or (self.current_button['key'] != event.dict['key']):
                    dct = event.dict
                    dct['next_press'] = pygame.time.get_ticks() + self.cooldown
                    self.current_button = dct
                    return True
            if event.type == pygame.KEYUP:
                if (self.current_button) and self.current_button['key'] == event.dict['key']:
                    self.current_button = None

        if self.current_button:
            if pygame.time.get_ticks() >= self.current_button['next_press']:
                self.current_button['next_press'] = pygame.time.get_ticks() + self.repeat_rate

        # as of right now, without these prints. The program jitters. I cannot explain it
        print()
        print('\x1b[1A\x1b[1K', end='')

    def input(self, prompt=''):
        """The default input function, feel free to make your own"""
        self.print(prompt)

        user_text = ''
        starting_x = copy.copy(self.cursor_pos[0])
        starting_y = copy.copy(self.cursor_pos[1])

        while self.running:
            first_press = self.get_pressed_key()

            if self.current_button and (first_press or pygame.time.get_ticks() >= self.current_button['next_press']):
                x, y = self.cursor_pos

                if self.current_button['key'] == 8:
                    if user_text[:x-starting_x]:
                        if self.current_button['mod'] == 4160:
                            try:
                                if user_text[(x-starting_x)-1] in self.word_delimiters:
                                    while user_text[(x-starting_x)-1] in self.word_delimiters:
                                        self.delete_text()
                                        user_text = user_text[:x-starting_x-1] + user_text[x-starting_x-1+1:]
                                        x, y = self.cursor_pos
                                else:
                                    while user_text[(x-starting_x)-1] not in self.word_delimiters:
                                        self.delete_text()
                                        user_text = user_text[:x-starting_x-1] + user_text[x-starting_x-1+1:]
                                        x, y = self.cursor_pos
                            except IndexError:
                                pass
                        else:
                            user_text = user_text[:y] + user_text[y+1:]
                            self.delete_text()

                elif self.current_button['key'] == 1073741903:
                    self.cursor_blinker = 60
                    if x+1 <= len(user_text)+starting_x:
                        # self.move_cursor_to(x+1, y)
                        self.cursor_pos = [x+1, y]

                elif self.current_button['key'] == 1073741904:
                    self.cursor_blinker = 60
                    if x-1 >= starting_x:
                        # self.move_cursor_to(x-1, y)
                        self.cursor_pos = [x-1, y]

                elif self.current_button['unicode'] == '\x16':
                    for char in pyperclip.paste():
                        if char == '\n':
                            break
                        self.print(char, add=True)
                        user_text = list(user_text)
                        user_text.insert(x, char)
                        user_text = ''.join(user_text)

                elif self.current_button['unicode'] == '\r':
                    return user_text

                elif self.current_button['unicode'] == '\t':
                    self.print('    ', add=True)
                    user_text = list(user_text)
                    user_text.insert(x, '    ')
                    user_text = ''.join(user_text)

                else:
                    if self.current_button['unicode'] not in ['\b', '\x16', '']:
                        char = self.current_button['unicode']
                        self.print(char, add=True)
                        user_text = list(user_text)
                        user_text.insert(x, char)
                        user_text = ''.join(user_text)

    def wrap(self, iterable, num):
        for current_num in range(0, len(iterable), num):
            yield iterable[current_num:current_num+num]

    def make_array_copy(self, cursor=None):
        array_copy = []
        for x, row in enumerate(self.array):
            if len(row) >= self.window_columns-1:
                wrapped = list(self.wrap(row, self.window_columns-1))
                array_copy.extend(wrapped)
                if cursor and cursor[1] == x and cursor[0] >= self.window_columns-1:
                    cursor[1] += len(wrapped)-1
                    cursor[0] = len(wrapped[-1])-(len(row)-cursor[0])
            else:
                array_copy.append(row)
        return array_copy

    def update_screen(self):
        """Not meant to be used by the user"""

        y_offset = 0
        self.screen.fill(themes[self.theme.lower()]['background'])


        cursor_pos_copy = copy.deepcopy(self.cursor_pos)

        array_copy = self.make_array_copy(cursor_pos_copy)
        try:
            cursor_pos_copy[0] -= 1 if array_copy[cursor_pos_copy[1]][0].text == '\n' else 0
        except IndexError:
            pass

        mouse_pos = pygame.mouse.get_pos()

        if self.pressing_down and mouse_pos != self.current_select['coor']: # change this to use the event instead
            x, y = self.current_select['coor']
            x = x//self.cell_size[0]
            y = y//self.cell_size[1]

            x_, y_ = mouse_pos
            x_ = x_//self.cell_size[0]
            y_ = y_//self.cell_size[1]

            if y > y_:
                self.bigger = {'coor': [y, x], 'row_offset': self.current_select['row_offset']}
                self.smaller = {'coor': [y_, x_], 'row_offset':self.scrollbar.offset}
            elif y < y_:
                self.bigger = {'coor': [y_, x_], 'row_offset':self.scrollbar.offset}
                self.smaller = {'coor': [y, x], 'row_offset': self.current_select['row_offset']}
            else:
                if x > x_:
                    self.bigger = {'coor': [y, x], 'row_offset': self.current_select['row_offset']}
                    self.smaller = {'coor': [y_, x_], 'row_offset':self.scrollbar.offset}
                elif x < x_:
                    self.bigger = {'coor': [y_, x_], 'row_offset':self.scrollbar.offset}
                    self.smaller = {'coor': [y, x], 'row_offset': self.current_select['row_offset']}
                else:
                    self.bigger = {'coor': [y, x], 'row_offset':self.scrollbar.offset}
                    self.smaller = {'coor': [y, x], 'row_offset':self.scrollbar.offset}

            if self.smaller['coor'][0] <= -1:
                self.scrollbar.offset = max(self.scrollbar.offset+self.smaller['coor'][0], 0)
            elif self.bigger['coor'][0] >= self.window_rows+1:
                self.scrollbar.offset = min(self.scrollbar.offset+self.bigger['coor'][0], len(self.array)-self.window_rows)

        for x in range(self.window_rows):
            x_offset = 0
            for y in range(self.window_columns):
                try:
                    char = array_copy[x+self.scrollbar.offset][y]
                    if char.text == '\n':
                        continue
                    if char.text_formattings['bold'] and char.text_formattings['italic']:
                        font = self.bold_italic_default_font
                    elif char.text_formattings['bold']:
                        font = self.bold_default_font
                    elif char.text_formattings['italic']:
                        font = self.italic_default_font
                    else:
                        font = self.default_font

                    # if char.text_formattings['dim']: # idk how dim works
                    #     r, g, b = char.foreground_color
                    #     char.foreground_color = (r//2, g//2, b//2)

                    char_surface = font.render(char.text, True, char.foreground_color)
                    topleft = (x_offset, self.cell_size[1]*x)

                    if char.text_formattings['underline']:
                        font.set_underline(True)
                    else:
                        font.set_underline(False)

                    if char.text_formattings['strikethrough']:
                        font.set_strikethrough(True)
                    else:
                        font.set_strikethrough(False)

                    background_rect = char_surface.get_rect(topleft=topleft)
                    pygame.draw.rect(self.screen, char.background_color, background_rect)
                    if not char.text_formattings['invis']:
                        self.screen.blit(char_surface, topleft)

                    x_offset += self.cell_size[0]
                except IndexError:
                    pass

        self.cursor_blinker -= 1

        if self.cursor_blinker >= 0:
            cursor_surface = self.cursors[self.cursor]
            x = self.cell_size[0] * cursor_pos_copy[0]
            y = self.cell_size[1] * (cursor_pos_copy[1]-self.scrollbar.offset)
            self.screen.blit(cursor_surface, (x, y))

        elif self.cursor_blinker <= -60:
            self.cursor_blinker = 60

        for x_pos in range(self.window_columns-2):
            for y_pos in range(self.window_rows):
                x = x_pos*self.cell_size[0]
                y = y_pos*self.cell_size[1]
                topleft = (x, y)
                temp_surf = pygame.Surface(self.cell_size, pygame.SRCALPHA)
                rect = pygame.Rect((0, 0), self.cell_size)
                pygame.draw.rect(temp_surf, (255, 255, 255, 130), rect)


                if self.smaller['coor'][0] == self.bigger['coor'][0]:
                    if x_pos >= self.smaller['coor'][1] and x_pos <= self.bigger['coor'][1] and y_pos == (self.smaller['coor'][0]+self.smaller['row_offset'])-self.scrollbar.offset:
                        self.screen.blit(temp_surf, topleft)
                elif y_pos >= (self.smaller['coor'][0]+self.smaller['row_offset'])-self.scrollbar.offset and y_pos <= (self.bigger['coor'][0]+self.bigger['row_offset'])-self.scrollbar.offset:
                    if y_pos == (self.smaller['coor'][0]+self.smaller['row_offset'])-self.scrollbar.offset:
                        if x_pos >= self.smaller['coor'][1]:
                            self.screen.blit(temp_surf, topleft)
                    elif y_pos == (self.bigger['coor'][0]+self.bigger['row_offset'])-self.scrollbar.offset:
                        if x_pos <= self.bigger['coor'][1]:
                            self.screen.blit(temp_surf, topleft)
                    else:
                        self.screen.blit(temp_surf, topleft)


        self.scrollbar.draw(self.screen, draw_scrollbar=len(array_copy) > self.window_rows)

        pygame.display.flip()

    def run(self, func):
        bg_thread = threading.Thread(target=func)
        bg_thread.start()

        while self.running:
            self.loop()

    def loop(self):
        while self.running:
            self.events = pygame.event.get()

            total_length = 0
            for row in self.array:
                total_length += (len(row)//(self.window_columns-1))+1
            total_length -= self.window_rows

            self.scrollbar.update(events=self.events, total_length=total_length, offset_num=2, min_rows=self.window_rows, should_scroll=total_length > 0)

            for event in self.events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.smaller, self.bigger = {'coor': [-1, -1], 'row_offset':0}, {'coor': [-1, -1], 'row_offset':0}
                    self.current_select = {'coor':event.pos, 'row_offset':self.scrollbar.offset}
                    self.pressing_down = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.pressing_down = False
                if event.type == pygame.KEYDOWN:
                    if not self.pressing_down and event.mod % pygame.K_LSHIFT:
                        if event.key == pygame.K_LEFT and self.shift_direction == -1:
                            self.shift_direction = 0
                        elif event.key == pygame.K_RIGHT and self.shift_direction == -1:
                            self.shift_direction = 1

                        dct = [self.smaller, self.bigger][self.shift_direction]

                        if event.key == pygame.K_LEFT:
                            dct['coor'][1] -= 1
                            if dct['coor'][1] == -1:
                                dct['coor'][0] -= 1
                                dct['coor'][1] = self.window_columns-3
                        elif event.key == pygame.K_RIGHT:
                            dct['coor'][1] += 1
                            if dct['coor'][1] == self.window_columns-2:
                                dct['coor'][0] += 1
                                dct['coor'][1] = 0

                        if self.smaller['coor'][0] == self.bigger['coor'][0]:
                            if self.smaller['coor'][1] > self.bigger['coor'][1]:
                                smaller = copy.deepcopy(self.smaller)
                                bigger = copy.deepcopy(self.bigger)
                                self.bigger = smaller
                                self.smaller = bigger
                                self.shift_direction = 0 if self.shift_direction == 1 else 1
                    if event.key == pygame.K_c and event.mod % pygame.K_LCTRL: # TODO: if you try to copy the the first character in a line that does not have '\n' as the first character. It won't copy
                        text = ''
                        array_copy = self.make_array_copy()
                        if self.smaller['coor'][0] == self.bigger['coor'][0]:
                            x = self.smaller['coor'][0]+self.smaller['row_offset']
                            text = ''.join(i.text for i in array_copy[x][self.smaller['coor'][1]+1:self.bigger['coor'][1]+(2 if (array_copy[x][0].text == '\n') else 1)]).replace('\n', '')
                        else:
                            try:
                                x = self.smaller['coor'][0]+self.smaller['row_offset']
                                text += ''.join(i.text for i in array_copy[x][self.smaller['coor'][1]+1:self.window_columns]).replace('\n', '')
                                text += '\n'
                                for row in range(self.smaller['coor'][0]+1, self.bigger['coor'][0]):
                                    text += ''.join(i.text for i in array_copy[row]).replace('\n', '')
                                    text += '\n'
                                x = self.bigger['coor'][0]+self.bigger['row_offset']
                                text += ''.join(i.text for i in array_copy[x][0:self.bigger['coor'][1]+(2 if (array_copy[x][0].text == '\n' or x == 0) else 1)]).replace('\n', '')
                            except IndexError:
                                pass
                        pyperclip.copy(text)

                    if event.unicode:
                        self.smaller, self.bigger = {'coor': [-1, -1], 'row_offset':0}, {'coor': [-1, -1], 'row_offset':0}

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LSHIFT:
                        self.shift_direction = -1

            self.update_screen()
            self.clock.tick(self.FPS)
        pygame.quit()

def add_theme(theme_data):
    """Adds a custom made theme, format is fixed 
    {
        "theme name": {  # theme name must be lowercase
            "foreground": rgb,
            "background": rgb,
            "cursor_col": rgb,
            "8bitcolors": {
                "0": rgb,
                "1": rgb,
                "2": rgb,
                "3": rgb,
                "4": rgb,
                "5": rgb,
                "6": rgb,
                "7": rgb]
            },
            "16bitcolors": {
                "8": rgb,
                "9": rgb,
                "10": rgb,
                "11": rgb,
                "12": rgb,
                "13": rgb,
                "14": rgb,
                "15": rgb]
            }
        }
    } # all the keys need to have the same value, no support for custom 256 bit colors
    """

    themes.update(theme_data)
