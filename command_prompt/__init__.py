import threading
import pyperclip
import pygame
import copy
import os

from .COLORS import *

pygame.init()

class CursorShape:
    VINTAGE           = 0
    BAR               = 1
    UNDERSCORE        = 2
    DOUBLE_UNDERSCORE = 3
    FILLED            = 4
    EMPTY             = 5
    INVISIBLE         = 6

class Char:
    def __init__(self, char, ansi):
        self.text = char
        self.ansi = copy.deepcopy(ansi)
        self.color = DEFAULT_FOREGROUND

        for ansi_code in self.ansi:
            if ansi_code == '30':
                self.color = BLACK
            elif ansi_code == '31':
                self.color = RED
            elif ansi_code == '32':
                self.color = GREEN
            elif ansi_code == '33':
                self.color = YELLOW
            elif ansi_code == '34':
                self.color = BLUE
            elif ansi_code == '35':
                self.color = PURPLE
            elif ansi_code == '36':
                self.color = CYAN
            elif ansi_code == '37':
                self.color = WHITE

            if ansi_code == '90':
                self.color = LIGHT_BLACK
            elif ansi_code == '91':
                self.color = LIGHT_RED
            elif ansi_code == '92':
                self.color = LIGHT_GREEN
            elif ansi_code == '93':
                self.color = LIGHT_YELLOW
            elif ansi_code == '94':
                self.color = LIGHT_BLUE
            elif ansi_code == '95':
                self.color = LIGHT_PURPLE
            elif ansi_code == '96':
                self.color = LIGHT_CYAN
            elif ansi_code == '97':
                self.color = LIGHT_WHITE

            elif ansi_code.startswith('38;2;'):
                try:
                    _, _, r, g, b = ansi_code.split(';')
                except ValueError:
                    pass
                else:
                    self.color = (int(r), int(g), int(b))

    def __repr__(self):
        return f'<char="{self.text}", color={self.color}>'

class Window:
    def __init__(self, *, caption="Command prompt 2.0"):
        # fps limiter
        self.clock = pygame.time.Clock()
        self.FPS = 60

        # initialising the font. TODO: allow the user to load custom fonts
        self.default_font = pygame.font.Font('./fonts/CascadiaCode.ttf', 20)
        self.cell_size = self.default_font.size('H')

        # window settings
        self.window_columns = 120
        self.window_rows = 30
        self.screen_dimensions = (self.window_columns * self.cell_size[0] + 10, self.window_rows * self.cell_size[1])
        self.screen = pygame.display.set_mode(self.screen_dimensions)

        # .
        self.running = True
        pygame.display.set_caption(caption)

        self.array = [[]]

        self.events = []

        self.row_offset = 0

        self.word_delimiters = " /\()\"'-.,:;<>~!@#$%^&*|+=[]{}~?│ "

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


    def create_cursors(self):
        """Not meant to be used by the user"""
        w, h = self.cell_size

        vintage_cursor_surface = pygame.Surface((w, h))
        vintage_cursor_surface.fill(DEFAULT_BACKGROUND)
        vintage_cursor = pygame.Rect((0, h-(h/4)), (w, h/4))
        pygame.draw.rect(vintage_cursor_surface, DEFAULT_CURSOR, vintage_cursor)

        bar_cursor_surface = pygame.Surface((w, h))
        bar_cursor_surface.fill(DEFAULT_BACKGROUND)
        bar_cursor = pygame.Rect((0, 0), (1, h))
        pygame.draw.rect(bar_cursor_surface, DEFAULT_CURSOR, bar_cursor)

        underscore_cursor_surface = pygame.Surface((w, h))
        underscore_cursor_surface.fill(DEFAULT_BACKGROUND)
        underscore_cursor = pygame.Rect((0, h-1), (w, 1))
        pygame.draw.rect(underscore_cursor_surface, DEFAULT_CURSOR, underscore_cursor)

        double_underscore_cursor_surface = pygame.Surface((w, h))
        double_underscore_cursor_surface.fill(DEFAULT_BACKGROUND)
        double_underscore_cursor1 = pygame.Rect((0, h-1), (w, 1))
        double_underscore_cursor2 = pygame.Rect((0, h-3), (w, 1))
        pygame.draw.rect(double_underscore_cursor_surface, DEFAULT_CURSOR, double_underscore_cursor1)
        pygame.draw.rect(double_underscore_cursor_surface, DEFAULT_CURSOR, double_underscore_cursor2)

        filled_cursor_surface = pygame.Surface((w, h))
        filled_cursor_surface.fill(DEFAULT_BACKGROUND)
        filled_cursor = pygame.Rect((0, 0), (w, h))
        pygame.draw.rect(filled_cursor_surface, DEFAULT_CURSOR, filled_cursor)

        empty_cursor_surface = pygame.Surface((w, h))
        empty_cursor_surface.fill(DEFAULT_BACKGROUND)
        empty_cursor = pygame.Rect((0, 0), (w, h))
        pygame.draw.rect(empty_cursor_surface, DEFAULT_CURSOR, empty_cursor, 2)

        invis_cursor_surface = pygame.Surface((w, h))
        invis_cursor_surface.fill(DEFAULT_BACKGROUND)
        invis_cursor = pygame.Rect((0, 0), (0, 0))
        pygame.draw.rect(invis_cursor_surface, DEFAULT_CURSOR, invis_cursor)

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

    # def get_ansi_code_positions(self, text):
    #     ansi_codes = re.findall(r'\x1b\[(.*?m)', text)
    #     ansi_code_positions = []
    #     offset = 0
    #     for code in ansi_codes:
    #         start_pos = text.find('\x1b[' + code) - offset
    #         ansi_code_positions.append((start_pos, code[:-1]))
    #         offset += len('\x1b[' + code)
    #     return ansi_code_positions

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
                    if escape_sequence != '0':
                        self.current_ansi.append(escape_sequence)
                    else:
                        self.current_ansi = []
                    in_escape_sequence = False
                elif char.isdigit() or char == ';':
                    escape_sequence += char
                continue

            if y >= len(self.array):
                for _ in range((y-len(self.array))+1):
                    self.array.append([])
                    if len(self.array) > self.window_rows:
                        self.row_offset += 1
            while x >= len(self.array[y])+1:
                self.array[y].append(Char("", self.current_ansi))

            try:
                self.array[y].insert(x, Char(char, self.current_ansi))
            except IndexError:
                print(f"{x=}, {y=}, {self.array}")
            x += 1

        self.cursor_pos[0], self.cursor_pos[1] = x, y

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


    def delete_row(self):
        """Removes everything on the same row as the cursor
        Warning: if the line is being text-wrapped. This function will remove more than the visual row"""
        _, y = self.cursor_pos
        try:
            self.array[y] = []
            self.cursor_pos[0] = 0
        except IndexError: # just a pre-caution. Should never be executed
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
                self.array[y].append(Char('', self.current_ansi))

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
                    if user_text:
                        if self.current_button['mod'] == 4160: # shift-backspace
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
                        self.move_cursor_to(x+1, y)

                elif self.current_button['key'] == 1073741904:
                    self.cursor_blinker = 60
                    if x-1 >= starting_x:
                        self.move_cursor_to(x-1, y)

                elif self.current_button['unicode'] == '\x16':
                    for char in pyperclip.paste():
                        if char == '\n': # plan to add a preview like in command prompt
                            break
                        self.print(char, add=True)
                        user_text = list(user_text)
                        user_text.insert(x, char)
                        user_text = ''.join(user_text)

                elif self.current_button['unicode'] == '\r':
                    return user_text

                elif self.current_button['unicode'] == '\t': # plans to add an actual tab instead of 4 spaces
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

    def update_screen(self):
        """Not meant to be used by the user"""

        font = self.default_font

        y_offset = 0
        self.screen.fill(DEFAULT_BACKGROUND)


        cursor_pos_copy = copy.deepcopy(self.cursor_pos)
        try:
            cursor_pos_copy[0] -= 1 if self.array[-1][0].text == '\n' else 0
        except IndexError:
            pass

        array_copy = []
        for x, row in enumerate(self.array):
            if len(row) >= self.window_columns-1:
                wrapped = list(self.wrap(row, self.window_columns-2))
                array_copy.extend(wrapped)
                if cursor_pos_copy[1] == x and cursor_pos_copy[0] >= self.window_columns-1:
                    cursor_pos_copy[1] += len(wrapped)-1
                    cursor_pos_copy[0] = len(wrapped[-1])-(len(row)-cursor_pos_copy[0])
            else:
                array_copy.append(row)

        self.cursor_blinker -= 1

        if self.cursor_blinker >= 0:
            cursor_surface = self.cursors[self.cursor]
            x = self.cell_size[0] * cursor_pos_copy[0]
            y = self.cell_size[1] * cursor_pos_copy[1]
            self.screen.blit(cursor_surface, (x, y))

        elif self.cursor_blinker <= -60:
            self.cursor_blinker = 60

        for x in range(self.window_rows):
            x_offset = 0
            for y in range(self.window_columns):
                try:
                    char = array_copy[x+self.row_offset][y]
                    if char.text == '\n':
                        continue
                    char_surface = font.render(char.text, True, char.color)
                    topleft = (x_offset, self.cell_size[1]*x)
                    background_rect = char_surface.get_rect(topleft=topleft)
                    # pygame.draw.rect(self.screen, (), background_rect)
                    self.screen.blit(char_surface, topleft)

                    x_offset += self.cell_size[0]
                except IndexError:
                    pass

        
        rect = pygame.Rect((self.screen_dimensions[0]-(self.cell_size[0]*2), 0), ((self.cell_size[0]*2), self.screen_dimensions[1]))
        pygame.draw.rect(self.screen, (37, 37, 37), rect)

        if len(array_copy) > self.window_rows:
            perc = self.window_rows/len(array_copy)
            length = self.screen_dimensions[1]*perc

            pos = self.row_offset/len(array_copy)
            pos = pos*self.screen_dimensions[1]

            rect = pygame.Rect((self.screen_dimensions[0]-(self.cell_size[0]*2), pos), (self.cell_size[0]*2, length))
            pygame.draw.rect(self.screen, (120, 120, 120), rect)

        pygame.display.flip()

    def run(self, func):
        bg_thread = threading.Thread(target=func)
        bg_thread.start()

        while self.running:
            self.loop()

    def loop(self):
        while self.running:
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEWHEEL and len(self.array) >= self.window_rows:
                    self.row_offset = min(max(0, self.row_offset+(-2*event.y)), len(self.array)-self.window_rows)

            self.update_screen()
            self.clock.tick(self.FPS)
        pygame.quit()
