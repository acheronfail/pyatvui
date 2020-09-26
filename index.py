import asyncio
import curses
import pyatv
import sys

async def connect_to_atv(window, loop, i=0):
    window.addstr(i, 0, 'Scanning for devices...')
    window.refresh()
    devices = await pyatv.scan(loop, timeout=5)

    if not devices:
        return await connect_to_atv(window, loop, i=i+1)

    # TODO: support multiple
    device = devices[0]
    window.addstr(i + 1, 0, 'Connecting to {} {}...'.format(device.address, device.name))
    window.refresh()
    atv = await pyatv.connect(device, loop)

    return atv, device

def draw_ui(window, atv, device):
    # Get window dimensions
    window.clear()
    max_y, max_x = window.getmaxyx()

    # Get grid coords
    row_1 = max_y // 4
    row_2 = max_y - row_1
    col_1 = max_x // 4
    col_2 = max_x - col_1

    # Draw grid
    for col in range(0, max_x):
        window.addstr(row_1, col, '+' if col == col_1 or col == col_2 else '-')
        window.addstr(row_2, col, '+' if col == col_1 or col == col_2 else '-')
    for row in range(0, max_y):
        window.addstr(row, col_1, '+' if row == row_1 or row == row_2 else '|')
        window.addstr(row, col_2, '+' if row == row_1 or row == row_2 else '|')

    # Add labels
    window.addstr(0, 0, 'Menu')
    window.addstr(0, col_2 + 1, 'Top Menu (TV)')
    window.addstr(row_1 + 1, col_1 + 1, 'Select')
    window.addstr(row_1 + 1, 0, 'Left')
    window.addstr(row_1 + 1, col_2 + 1, 'Right')
    window.addstr(0, col_1 + 1, 'Up')
    window.addstr(row_2 + 1, col_1 + 1, 'Down')
    window.addstr(row_2 + 1, 0, 'Suspend')
    window.addstr(row_2 + 1, col_2 + 1, 'Play/Pause')

    # Device information
    window.addstr(row_1 + 3, col_1 + 1, '{}'.format(device.name))
    window.addstr(row_1 + 4, col_1 + 1, '{}'.format(device.address))
    window.addstr(row_1 + 5, col_1 + 1, '{}'.format(atv.device_info.mac))
    window.addstr(row_1 + 6, col_1 + 1, '{}'.format(atv.device_info.model))
    window.addstr(row_1 + 7, col_1 + 1, '{}'.format(atv.device_info.version))

    # Move cursor to top left and hide it
    window.move(0, 0)
    curses.curs_set(0)
    return col_1, col_2, row_1, row_2

async def start_ui(window, loop):
    # Clear screen
    window.clear()
    window.refresh()
    curses.noecho()

    # Don't require enter to be pressed for inputs
    curses.cbreak()

    # Needed to enable mouse
    curses.mousemask(1)
    window.keypad(1)
    curses.mouseinterval(0)

    # Connect to the AppleTV
    atv, device = await connect_to_atv(window, loop)

    col_1, col_2, row_1, row_2 = draw_ui(window, atv, device)
    while True:
        try:
            c = window.getch()
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
                    await atv.remote_control.home()
                elif left and down:
                    await atv.remote_control.suspend()
                    break
                elif right and down:
                    await atv.remote_control.play_pause()

            elif c == ord('w'):
                await atv.remote_control.wakeup()
            elif c == ord('s'):
                await atv.remote_control.suspend()
                break
            elif c == ord('r'):
                col_1, col_2, row_1, row_2 = draw_ui(window, atv, device)
            elif c == ord('h'):
                await atv.remote_control.left()
            elif c == ord('j'):
                await atv.remote_control.down()
            elif c == ord('k'):
                await atv.remote_control.up()
            elif c == ord('l'):
                await atv.remote_control.right()
            elif c == ord('u'):
                await atv.remote_control.top_menu()
            elif c == ord('i'):
                await atv.remote_control.menu()
            elif c == ord('o'):
                await atv.remote_control.select()
            elif c == ord('p'):
                await atv.remote_control.play_pause()
            elif c == ord('z'):
                await atv.remote_control.volume_down()
            elif c == ord('x'):
                await atv.remote_control.volume_up()
            elif c == ord('q'):
                break  # Exit the while loop
        except Exception as err:
            window.addstr(row_1 + 9, col_1 + 1, '{}'.format(err))

    # Unhide cursor
    curses.curs_set(1)
    window.refresh()
    # Close connection to device
    result = atv.close()
    if result is not None:
        await result

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(curses.wrapper(start_ui, loop))

