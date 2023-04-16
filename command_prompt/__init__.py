import pyperclip
import pathlib
import pygame
import random
import time
import copy
import os
import re

import random

from .COLORS import *

pygame.init()

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
        self.clock = pygame.time.Clock()
        self.FPS = 60

        file_path = os.path.join(os.path.dirname(__file__), r'fonts\CascadiaCode.ttf')
        self.default_font = pygame.font.Font(file_path, 20)
        self.cell_size = self.default_font.size('H')

        self.window_columns = 120
        self.window_rows = 30
        self.screen_dimensions = (self.window_columns * self.cell_size[0] + 10, self.window_rows * self.cell_size[1])
        self.screen = pygame.display.set_mode(self.screen_dimensions)

        self.running = True
        pygame.display.set_caption(caption)


        self.cursor_pos = [0, 0]
        self.array = [[]]

        self.events = []

        self.row_offset = 0

        self.cursors = self.create_cursors()
        self.cursor = 1
        self.cursor_blinker = 60

        self.current_ansi = []


    def create_cursors(self):
        w, h = self.cell_size

        vintage_cursor = pygame.Rect((0, (h/4)*3), (w, h/4))
        bar_cursor = pygame.Rect((0, 0), (1, h))
        underscore_cursor = pygame.Rect((0, 0), (w, 1))
        filled_cursor = pygame.Rect((0, 0), (w, h))
        invis_cursor = pygame.Rect((0, 0), (0, 0))
        return [vintage_cursor, bar_cursor, underscore_cursor, filled_cursor, invis_cursor]

    # def get_ansi_code_positions(self, text):
    #     ansi_codes = re.findall(r'\x1b\[(.*?m)', text)
    #     ansi_code_positions = []
    #     offset = 0
    #     for code in ansi_codes:
    #         start_pos = text.find('\x1b[' + code) - offset
    #         ansi_code_positions.append((start_pos, code[:-1]))
    #         offset += len('\x1b[' + code)
    #     return ansi_code_positions

    def print(self, string):
        # global cursor_pos, array, cursor_blinker, current_ansi, row_offset
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

            if x >= self.window_columns:
                y += 1
                x = 0

            if y >= len(self.array):
                for _ in range((y-len(self.array))+1):
                    self.array.append([])
                    if len(self.array) > self.window_rows:
                        self.row_offset += 1
            while x >= len(self.array[y]):
                self.array[y].append(Char(" ", self.current_ansi))

            try:
                self.array[y][x] = Char(char, self.current_ansi)
            except IndexError:
                print(f"{x=}, {y=}, {self.array}")
            x += 1

        self.cursor_pos[0], self.cursor_pos[1] = x, y

    def delete_text(self, amount=1):
        # global cursor_pos, cursor_blinker
        self.cursor_blinker = 60
        x, y = self.cursor_pos
        for _ in range(amount):
            x -= 1
            if x < 0:
                if y-1 < 0:
                    break
                else:
                    y -= 1
                    x = len(self.array[y])
            else:
                self.array[y].pop(x)
                if not len(self.array[y]):
                    y -= 1
                    x = len(self.array[y])
        self.cursor_pos = [x, y]

    def move_cursor_to(self, x, y):
        # global cursor_pos
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("Cursor position values must be integers")
        if x < 0 or y < 0:
            raise ValueError("Cursor position values must be positive")

        if len(self.array) <= y:
            for _ in range(len(self.array), y+1):
                self.array.append([])

        if len(self.array[y]) <= x:
            for _ in range(len(self.array[y]), x+1):
                self.array[y].append(Char(' '))

        self.cursor_pos[0], self.cursor_pos[1] = x, y

    def input(self, prompt=''):
        # global events
        self.print(prompt)

        current_button = None

        cooldown = 500
        repeat_rate = 25

        user_text = ''
        starting_x = copy.copy(self.cursor_pos[0])
        starting_y = copy.copy(self.cursor_pos[1])

        while self.running:
            key_detected = False
            for event in self.events:
                if event.type == pygame.KEYDOWN and not key_detected:
                    key_detected = True
                    if (not current_button) or (current_button['key'] != event.dict['key']):
                        dct = event.dict
                        dct['next_press'] = pygame.time.get_ticks() + cooldown
                        current_button = dct
                        if current_button['key'] == 8:
                            if user_text:
                                user_text = user_text[:-1]
                                self.delete_text()
                            # else:
                            #     user_text = user_text[:-1]
                            #     delete_text()
                        elif current_button['unicode'] == '\x16':
                            for char in pyperclip.paste():
                                if char == '\n':
                                    break
                                self.print(char)
                                user_text += char
                        elif current_button['unicode'] == '\r':
                            return user_text
                        elif current_button['unicode'] == '\t':
                            for _ in range(4):
                                self.print(' ')
                            user_text += '\t'
                        else:
                            if current_button['key'] not in [8, 118]:
                                char = current_button['unicode']
                                self.print(char)
                                user_text += char
                elif event.type == pygame.KEYUP:
                    if (current_button) and current_button['key'] == event.dict['key']:
                        current_button = None

            if current_button:
                if pygame.time.get_ticks() >= current_button['next_press']:
                    current_button['next_press'] = pygame.time.get_ticks() + repeat_rate
                    if current_button['key'] == 8:
                        if user_text:
                            user_text = user_text[:-1]
                            self.delete_text()
                        # else:
                        #     user_text = user_text[:-1]
                        #     delete_text()
                    elif current_button['unicode'] == '\x16':
                        for char in pyperclip.paste():
                            if char == '\n':
                                break
                            self.print(char)
                            user_text += char
                    if current_button['unicode'] == '\r':
                        return user_text
                    if current_button['unicode'] == '\t':
                        for _ in range(4):
                            self.print(' ')
                        user_text += '\t'
                    else:
                        if current_button['key'] not in [8, 118]:
                            char = current_button['unicode']
                            self.print(char)
                            user_text += char

    def update_screen(self):
        # global cursor_blinker, row_offset

        font = self.default_font

        y_offset = 0
        self. screen.fill(DEFAULT_BACKGROUND)

        cursor_pos_copy = copy.deepcopy(self.cursor_pos)
        try:
            cursor_pos_copy[0] -= 1 if self.array[-1][0].text == '\n' else 0
        except IndexError:
            pass

        for row_num, row in enumerate(self.array[self.row_offset:self.row_offset+self.window_rows]):
            x_offset = 0
            for char in row:
                if char.text == '\n':
                    continue
                char_surface = font.render(char.text, True, char.color)
                self. screen.blit(char_surface, (x_offset, y_offset))
                x_offset += font.size(str(char.text))[0]
            y_offset += font.size(str(row))[1]

        self.cursor_blinker -= 1

        if self.cursor_blinker >= 0:
            cursor_rect = self.cursors[self.cursor]
            cursor_rect.x = self.cell_size[0] * cursor_pos_copy[0]
            cursor_rect.y = self.cell_size[1] * cursor_pos_copy[1]
            pygame.draw.rect(self.screen, DEFAULT_CURSOR, cursor_rect)
        elif self.cursor_blinker <= -60:
            self.cursor_blinker = 60

        
        rect = pygame.Rect((self.screen_dimensions[0]-(self.cell_size[0]*2), 0), ((self.cell_size[0]*2), self.screen_dimensions[1]))
        pygame.draw.rect(self.screen, (37, 37, 37), rect)

        if len(self.array) > self.window_rows:
            perc = self.window_rows/len(self.array)
            length = self.screen_dimensions[1]*perc

            pos = self.row_offset/len(self.array)
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
