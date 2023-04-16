# Command-Prompt-2.0
This repository contains a command prompt clone that makes it easy to create CLI (Command Line Interface) applications. The clone is built using Python and provides a simple interface for developers to create and run CLI apps.

# Installation
To use command prompt 2.0, you will need to have Python 3.7+ installed on your system. You can download Python from the official website.

Once you have Python installed, you can install run the following command to install the package:

pip install git+https://github.com/andrewthederp/Command-Prompt-2.0

# Usage
To use command prompt 2.0, simply import `command_prompt`, then create an instance of `command_prompt.Window`. And to run the window run `command_prompt.Window.run`
Simple example: `py
from command_prompt import Window

window = Window()

def main():
	window.print("Hello, World!") # add text to the screen
	window.input() # wait for the user to press enter
	window.running = False # end the program

window.run(main)
`

# Contributing
We welcome contributions to this project, and we appreciate your help improving it! If you would like to contribute, please follow these steps:

* Fork the repository
* Create a new branch for your changes
* Make your changes and commit them
* Push your changes to your fork
* Submit a pull request
* We will review your changes and merge them if they are appropriate.

# TODO
- [] Add support for more ansi codes
- [] Add support for window re-sizing
- [] Allow for more customizability

# Credits
* AndreawTheDerp - Creator, maintainer
