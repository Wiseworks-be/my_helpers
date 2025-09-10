import sys

if sys.platform.startswith("win"):
    import msvcrt
else:
    import tty
    import termios


def wait_for_keypress(debug=False):
    if debug:
        print("DEBUG MODE: Waiting for keypress to continue...")
        if sys.platform.startswith("win"):
            msvcrt.getch()
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    else:
        print("Not in DEBUG mode, skipping keypress wait.")