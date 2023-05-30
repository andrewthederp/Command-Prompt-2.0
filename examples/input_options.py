from command_prompt import Window, TextInput, CursorShape

window = Window()

def input_options(options, *, prefix='', selected_option_prefix=''):

	def inp_func(key, user_text, text_input, *, y):
		current_option = 0 if type(user_text) == str else user_text
		if key['unicode'] == '\r':
			text_input.getting_input = False
		elif key['key'] == 1073741906:
			current_option = (current_option - 1) % len(options)
		elif key['key'] == 1073741905:
			current_option = (current_option + 1) % len(options)

		for i, option in enumerate(options):
			window.move_cursor_to(0, y+i)
			if i == current_option:
				window.print(selected_option_prefix+option+'\n')
			else:
				window.print(prefix+option+'\n')
		return current_option

	y, _ = window.cursor_pos

	for i, option in enumerate(options):
		window.move_cursor_to(0, y+i)
		if i == 0:
			window.print(selected_option_prefix+option+'\n')
		else:
			window.print(prefix+option+'\n')

	text_input = TextInput(inp_func, func_args={'y':y})

	window.change_cursor(CursorShape.INVISIBLE)
	while text_input.getting_input and window.running:
		pass

	window.change_cursor(CursorShape.BAR)
	return text_input.user_text


def main():
	animals = ['cat', 'dog', 'duck', 'rat', 'horse']
	window.print("What is your favourite animal:\n")
	option = input_options(animals, prefix='[ ] ', selected_option_prefix='[*] ')
	window.print('\n'+"Wow, my favourite animal is "+animals[option]+' too!')

window.run(main)
