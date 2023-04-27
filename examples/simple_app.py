from command_prompt import Window

window = Window()

def main():
	window.print("Hello, World!") # add text to the screen
	window.input() # wait for the user to press enter
	window.running = False # end the program

window.run(main)
