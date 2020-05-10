from curses import wrapper
import curses

import sys
import asyncio
import pyatv

LOOP = asyncio.get_event_loop()

async def start_ui(stdscr, atv, device):
    # Clear screen
    stdscr.clear()
    stdscr.refresh()
    curses.noecho()

    # Don't require enter to be pressed for inputs
    curses.cbreak()

    # Needed to enable mouse
    curses.mousemask(1)
    stdscr.keypad(1)
    curses.mouseinterval(0)

    # Get window dimensions
    max_y, max_x = stdscr.getmaxyx()

    # Draw columns
    row_1 = max_y // 4
    row_2 = max_y - row_1
    col_1 = max_x // 4
    col_2 = max_x - col_1
    for col in range(0, max_x):
        stdscr.addstr(row_1, col, '-')
        stdscr.addstr(row_2, col, '-')
    for row in range(0, max_y):
        stdscr.addstr(row, col_1, '|')
        stdscr.addstr(row, col_2, '|')
    # Add labels
    stdscr.addstr(0, 0, 'Menu')
    stdscr.addstr(0, col_2 + 1, 'Top Menu (TV)')
    stdscr.addstr(row_1 + 1, col_1 + 1, 'Select')
    stdscr.addstr(row_1 + 1, 0, 'Left')
    stdscr.addstr(row_1 + 1, col_2 + 1, 'Right')
    stdscr.addstr(0, col_1 + 1, 'Up')
    stdscr.addstr(row_2 + 1, col_1 + 1, 'Down')
    stdscr.addstr(row_2 + 1, 0, 'Suspend')
    stdscr.addstr(row_2 + 1, col_2 + 1, 'Play/Pause')
    # Info
    stdscr.addstr(row_1 + 3, col_1 + 1, '{}'.format(device.name))
    stdscr.addstr(row_1 + 4, col_1 + 1, '{}'.format(device.address))
    stdscr.addstr(row_1 + 5, col_1 + 1, '{}'.format(atv.device_info.mac))
    stdscr.addstr(row_1 + 6, col_1 + 1, '{}'.format(atv.device_info.model))
    stdscr.addstr(row_1 + 7, col_1 + 1, '{}'.format(atv.device_info.version))

    while True:
        c = stdscr.getch()
        if c == curses.KEY_MOUSE:
            _, x, y, _, _ = curses.getmouse()

            # Get mouse position
            left = x < col_1
            right = x > col_2
            up = y < row_1
            down = y > row_2
            center = not up and not down
            middle = not left and not right

            # Click areas.
            if left and center:
                await atv.remote_control.left()
            elif right and center:
                await atv.remote_control.right()
            elif up and middle:
                await atv.remote_control.up()
            elif down and middle:
                await atv.remote_control.down()
            elif center and middle:
                await atv.remote_control.select()
            elif left and up:
                await atv.remote_control.menu()
            elif right and up:
                await atv.remote_control.top_menu()
            elif left and down:
                await atv.remote_control.suspend()
                break
            elif right and down:
                await atv.remote_control.play_pause()

        elif c == ord('w'):
            await atv.remote_control.wakeup()
            stdscr.addstr(0, 0, 'wakeup')
        elif c == ord('s'):
            await atv.remote_control.suspend()
            stdscr.addstr(0, 0, 'suspend')
            break
        elif c == ord('h'):
            await atv.remote_control.left()
            stdscr.addstr(0, 0, 'left')
        elif c == ord('j'):
            await atv.remote_control.down()
            stdscr.addstr(0, 0, 'down')
        elif c == ord('k'):
            await atv.remote_control.up()
            stdscr.addstr(0, 0, 'up')
        elif c == ord('l'):
            await atv.remote_control.right()
            stdscr.addstr(0, 0, 'right')
        elif c == ord('u'):
            await atv.remote_control.top_menu()
            stdscr.addstr(0,0,'top_menu')
        elif c == ord('i'):
            await atv.remote_control.menu()
            stdscr.addstr(0, 0, 'menu')
        elif c == ord('o'):
            await atv.remote_control.select()
            stdscr.addstr(0, 0, 'select')
        elif c == ord('p'):
            await atv.remote_control.play_pause()
            stdscr.addstr(0,0,'play_pause')
        elif c == ord('q'):
            break  # Exit the while loop

# Method that is dispatched by the asyncio event loop
async def scan_atvs(loop):
    """Find a device and print what is playing."""
    print('Discovering devices on network...')
    devices = await pyatv.scan(loop, timeout=5)

    if not devices:
        print('No device found', file=sys.stderr)
        return
    
    # TODO: support multiple
    device = devices[0]
    print('Connecting to {} {}...'.format(device.address, device.name))
    atv = await pyatv.connect(device, loop)

    try:
        await wrapper(start_ui, atv, device)
    finally:
        # Do not forget to close
        atv.close()


if __name__ == '__main__':
    # Setup event loop and connect
    LOOP.run_until_complete(scan_atvs(LOOP))

