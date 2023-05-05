from command_prompt import Window

window = Window()

def main():
    window.print("Foreground\n")
    window.print("\033[30mBlack      \033[90mBright Black\033[0m\n")
    window.print("\033[31mRed        \033[91mBright Red\033[0m\n")
    window.print("\033[32mGreen      \033[92mBright Green\033[0m\n")
    window.print("\033[33mYellow     \033[93mBright Yellow\033[0m\n")
    window.print("\033[34mBlue       \033[94mBright Blue\033[0m\n")
    window.print("\033[35mPurple     \033[95mBright Purple\033[0m\n")
    window.print("\033[36mCyan       \033[96mBright Cyan\033[0m\n")
    window.print("\033[37mWhite      \033[97mBright White\033[0m\n")

    
    window.print("\nBackground\n")
    window.print("\033[40mBlack      \033[100mBright Black\033[0m\n")
    window.print("\033[41mRed        \033[101mBright Red\033[0m\n")
    window.print("\033[42mGreen      \033[102mBright Green\033[0m\n")
    window.print("\033[43mYellow     \033[103mBright Yellow\033[0m\n")
    window.print("\033[44mBlue       \033[104mBright Blue\033[0m\n")
    window.print("\033[45mPurple     \033[105mBright Purple\033[0m\n")
    window.print("\033[46mCyan       \033[106mBright Cyan\033[0m\n")
    window.print("\033[47mWhite      \033[107mBright White\033[0m\n\n")
    
    for i in range(0, 16):
        for j in range(0, 16):
            code = str(i * 16 + j)
            window.print("\033[38;5;" + code + "m " + code.ljust(4) + "\033[0m")
        window.print("\n")

window.run(main)
