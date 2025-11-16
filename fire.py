import curses
import random
import sys
import time

# --- Configuration ---
COOLING_FACTOR = 0.75
WIND_FACTOR = 0.1

# Intensity characters from hottest to coolest
FIRE_CHARS = ['#', 'O', 'o', '.', ' ']
FIRE_PALETTE_SIZE = len(FIRE_CHARS) - 1

def run_animation(stdscr, initial_text=""):
    """Main function to run the fire animation."""
    # --- Curses Setup ---
    curses.curs_set(0)  # Hide the cursor
    stdscr.timeout(100) # Make getch() wait 100ms for a key, then return -1

    # Set up colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)

    height, width = stdscr.getmaxyx()
    lines = initial_text.splitlines()

    # --- Initialize the grid ---
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    fire_buffer = [[0.0 for _ in range(width)] for _ in range(height)]

    # Place initial text onto the grid, left-justified
    if lines:
        start_row = max(0, (height - len(lines)) // 2 - 4)
        for i, line in enumerate(lines):
            if start_row + i < height:
                line_text = line[:width]
                start_col = 0  # Left-justify the text
                for j, char in enumerate(line_text):
                    if start_col + j < width:
                        grid[start_row + i][start_col + j] = char
    else:
        # If no stdin, create a default log to burn
        log_text = "=== GEMINI FIRE ==="
        log_row = height - 5
        start_col = max(0, (width - len(log_text)) // 2)
        if log_row >= 0:
            for i, char in enumerate(log_text):
                if start_col + i < width:
                    grid[log_row][start_col + i] = char

    # --- Animation Loop ---
    while True:
        if stdscr.getch() == ord('q'):
            break

        # --- Simulation Step ---
        for y in range(height - 1):
            for x in range(width):
                wind_dx = int((random.random() - 0.5) * 4)
                src_x = max(0, min(width - 1, x + wind_dx))
                heat = fire_buffer[y + 1][src_x]
                cooled_heat = max(0, heat - random.random() * 0.25)
                fire_buffer[y][x] = cooled_heat

        for y in range(height):
            for x in range(width):
                if grid[y][x] != ' ' and fire_buffer[y][x] > 0.6:
                    fire_buffer[y][x] = 1.0
                    grid[y][x] = ' '

        for x in range(width):
            fire_buffer[height - 1][x] *= 0.9
            if random.random() < 0.15:
                 fire_buffer[height - 1][x] = 1.0

        # --- Render Step ---
        stdscr.erase()
        for y in range(height):
            for x in range(width):
                intensity = fire_buffer[y][x]
                char = ' '
                color_pair = 0

                if grid[y][x] != ' ':
                    char = grid[y][x]
                    color_pair = 0
                elif intensity > 0.01:
                    char_index = min(FIRE_PALETTE_SIZE, int(intensity * FIRE_PALETTE_SIZE))
                    char = FIRE_CHARS[FIRE_PALETTE_SIZE - char_index]
                    if intensity > 0.8: color_pair = 1
                    elif intensity > 0.6: color_pair = 2
                    elif intensity > 0.4: color_pair = 3
                    else: color_pair = 4

                if y < height and x < width:
                    try:
                        stdscr.addch(y, x, char, curses.color_pair(color_pair))
                    except curses.error:
                        pass

        stdscr.refresh()
        time.sleep(0.08)

if __name__ == '__main__':
    # First, determine if input is being piped and read it.
    is_pipe = not sys.stdin.isatty()
    initial_text = sys.stdin.read() if is_pipe else ""

    # If input was piped, the script's stdin is no longer the terminal.
    # To capture keyboard input, we must reopen /dev/tty.
    if is_pipe:
        try:
            sys.stdin = open('/dev/tty')
        except Exception as e:
            # This will fail on non-Unix systems, but is necessary for
            # keyboard input to work in pipe mode on Linux/macOS.
            pass

    # Manually initialize and wrap the curses application to ensure
    # the above stdin handling happens *before* curses takes control.
    stdscr = None
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        run_animation(stdscr, initial_text)
    except curses.error as e:
        # It's good practice to end curses before printing the error
        curses.endwin()
        print(f"A curses error occurred: {e}")
        print("Your terminal might be too small to run the animation.")
    except KeyboardInterrupt:
        pass # Silently exit on Ctrl+C
    finally:
        # Ensure the terminal is restored to a sane state.
        if stdscr:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
