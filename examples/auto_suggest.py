from command_prompt import Window
from command_prompt import CursorShape
import time, pyperclip, pygame, copy

window = Window()

def input_with_suggestions(window, prompt='', suggestions=[]):
    window.print(prompt)

    user_text = ''
    starting_x = copy.copy(window.cursor_pos[0])
    starting_y = copy.copy(window.cursor_pos[1])

    while window.running:
        first_press = window.get_pressed_key()

        suggested_word = ''
        for word in suggestions:
            if user_text and word.startswith(user_text) and word != user_text:
                suggested_word = word
                break

        window.delete_right()
        window.move_cursor_to(starting_x, starting_y)
        window.print('\033[90m'+suggested_word+'\033[0m')
        window.move_cursor_to(starting_x, starting_y)
        window.print(user_text)

        if window.current_button and (first_press or pygame.time.get_ticks() >= window.current_button['next_press']):
            if window.current_button['key'] == 8:
                if user_text:
                    if window.current_button['mod'] == 4160:
                        try:
                            if user_text[-1] in window.word_delimiters:
                                while user_text[-1] in window.word_delimiters:
                                    window.delete_text()
                                    user_text = user_text[:-1]
                            else:
                                while user_text[-1] not in window.word_delimiters:
                                    window.delete_text()
                                    user_text = user_text[:-1]
                        except IndexError:
                            pass
                    else:
                        user_text = user_text[:-1]
                        window.delete_text()

            elif window.current_button['unicode'] == '\x16':
                for char in pyperclip.paste():
                    if char == '\n':
                        break
                    user_text += char

            elif window.current_button['unicode'] == '\r':
                return user_text

            elif window.current_button['unicode'] == '\t':
                if suggested_word:
                    user_text = suggested_word

            else:
                if window.current_button['unicode'] not in ['\b', '\x16', '']:
                    char = window.current_button['unicode']
                    user_text += char

def main():
    animal = input_with_suggestions(window, "What is your favourite animal: ", suggestions=['cat', 'dog', 'mouse', 'cow', 'goat', 'sheep', 'horse', 'donkey', 'mule', 'wolf', 'fox', 'duck', 'goose'])
    window.print('\nMy favourite animal is '+animal+' too!\n')

window.run(main)
