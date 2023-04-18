from command_prompt import Window
import pygame

window = Window()

def input_options(options, *, prefix='', selected_option_prefix=''):

    current_option = 0
    y, _ = window.cursor_pos

    while window.running:
        for i, option in enumerate(options):
            window.move_cursor_to(0, y+i)
            if i == current_option:
                window.print(selected_option_prefix+option+'\n')
            else:
                window.print(prefix+option+'\n')

        first_press = window.get_pressed_key()
        if window.current_button and (first_press or pygame.time.get_ticks() >= window.current_button['next_press']):
            if window.current_button['unicode'] == '\r':
                break
            elif window.current_button['key'] == 1073741906:
                current_option = (current_option - 1) % len(options)
            elif window.current_button['key'] == 1073741905:
                current_option = (current_option + 1) % len(options)

    return current_option


def main():
    animals = ['cat', 'dog', 'duck', 'rat', 'horse']
    window.print("What is your favourite animal:\n")
    option = input_options(animals, prefix='[ ] ', selected_option_prefix='[*] ')
    window.print('\n'+"Wow, my favourite animal is "+animals[option]+' too!')

window.run(main)
