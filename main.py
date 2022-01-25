"""
Requirements:
    1. pygame (Used for input capture)
    2. uvloop (speedy C module for Asyncio) - Could also try to run with `Pypy3`

Kwown Issues:
    1. If you get a message about "ApplePersistenceIgnoreState" on OSX, use this command `defaults write org.python.python ApplePersistenceIgnoreState NO` to disable persistent state files.  Ref: https://stackoverflow.com/questions/18733965/annoying-message-when-opening-windows-from-python-on-os-x-10-8
    2. Still having issue with "WASD" movement lagging mouse movement, looking for feedback as I investigate further.
"""
from os import name, environ, path
import shutil
from sys import argv
from pathlib import Path
import logging
import socket
from time import sleep
import asyncio
import ujson
from filelock import FileLock
import PySimpleGUI as sg
from PIL import Image

# Supress SDL welcome prompt
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

__version__ = '0.1.3'

"""
This section will need to be customized to your device/preferences
"""
CWD = Path(__file__).parent.absolute()
LOC = '/'
DEVICE_IP = "127.0.0.1"
try:
    DEVICE_IP = argv[1]
except IndexError:
    pass

# Setup logging
log = logging.getLogger(f'ZXTouch CoDm Client v{__version__}')
log.setLevel(logging.INFO)
hdlr = logging.StreamHandler()
hdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
log.handlers = [hdlr]
# Uncomment to enable file logging.
# fhdlr = logging.FileHandler(f"{CWD}{LOC}logs{LOC}events.log", encoding="utf-8")
# fhdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
# log.handlers.append(fhdlr)

# Import or load image path
IMG = f"{CWD}{LOC}game_image.png"
if not path.isfile(IMG):
    layout = [[sg.T("")], [sg.Text("Choose Image (no compressed images): "), sg.Input(), sg.FileBrowse(key="-IN-")] ,[sg.Button("Submit", bind_return_key=True)]]

    ###Building Window
    window = sg.Window('ZTC File Browser', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            exit()
        # Import image file to CWD
        elif event == "Submit":
            shutil.copy(values["-IN-"], IMG)
            log.info('Image "game_image.png" imported to working directory.')
            window.close()
            break

SENSITIVITY = 1 # Leave CoDm sensitiity set to "low" for everything or adjust as necessary
MOVES = 4       # This is how many positions will be set when moving the joystick (min is 2)
# Touch ID(s)
TOUCH_TASK = '10'
# Touch Events
SINGLE_EVENT = '1'
DUAL_EVENT = '2'
# Finger mappings
RESERVED_FINGER = '00' # Not used
MOUSE_FINGER = '01'
# Touch Types
TOUCH_UP = '0'
TOUCH_DOWN = '1'
TOUCH_MOVE = '2'
# Set initial Coorinates and screen size for buttons and mouse operations.
img=Image.open(IMG)
SCREEN_SIZE = img.size
log.info(f'Image "{IMG}" loaded and screen size set to {SCREEN_SIZE}.')

# Read config file, file format is ['FINGER_IDX', 'X', 'Y'] (remember these are portrait coordinates)
COORDS = ujson.load(open(f'{CWD}{LOC}config.json'))

# Verify config file loads succesfully
if COORDS:
    log.info('Config file loaded successfully from "config.json".')
else:
    log.error('Config file not loaded corectly, please check that "config.json" exists.')
    exit(1)



async def input_monitor():
    """
    This is the main monitoring module used to map key presses and mouse movement to touch API events for the iDevice.
    """
    # Indicate starting/reset coordnates and thresholds by percentage for mouse movement
    x_init = SCREEN_SIZE[0] / 2 + SCREEN_SIZE[1] / 2 * .5
    x_perc = (.70, .20)
    x = x_init
    y_init = SCREEN_SIZE[1] / 2 + SCREEN_SIZE[1] / 2 * .5
    y_perc = (.93, .50)
    y = y_init
    active = []
    pm, clicked = 0, 1
    pk = None
    mapped = {1: 'LBTN', 3: 'RBTN'}

    # Set the specific events you want to process in the queue.
    pygame.event.set_allowed(pygame.MOUSEMOTION)
    pygame.event.set_allowed(pygame.MOUSEBUTTONUP)
    pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
    pygame.event.set_allowed(pygame.KEYUP)
    pygame.event.set_allowed(pygame.KEYDOWN)

    # creating a running loop
    while True:

        # creating a loop to check events that are occuring (only looping when an event is picked up by the user)
        # Much lower CPU usage than "for event in pygame.event.get():"
        event = pygame.event.wait()

        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # Called when the mouse moves
        if not pm and event.type == pygame.MOUSEMOTION:
            # Use relative motion (lower sensitivity)
            rotation_direction, movement_direction = pygame.mouse.get_rel()
            # log.debug(f"Mouse Rel Movement: {rotation_direction}, {movement_direction}")
            x += rotation_direction / SENSITIVITY
            y -= movement_direction / SENSITIVITY

            # It is required to flip "x" & "y" if viewing pygame display in landscape mode as the iPhone API always accepts coordinates in portrait.
            if float(x / SCREEN_SIZE[0]) >= x_perc[0] or float(x / SCREEN_SIZE[0]) <= x_perc[1]:
                await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{MOUSE_FINGER}", f"{'%04d' % y}0", f"{'%04d' % x}0")
                x = x_init
            if float(y / SCREEN_SIZE[1]) >= y_perc[0] or float(y / SCREEN_SIZE[1]) <= y_perc[1]:
                await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{MOUSE_FINGER}", f"{'%04d' % y}0", f"{'%04d' % x}0")
                y = y_init
            # if float(x / SCREEN_SIZE[0]) >= x_perc[0] or float(x / SCREEN_SIZE[0]) <= x_perc[1] or float(y / SCREEN_SIZE[1]) >= y_perc[0] or float(y / SCREEN_SIZE[1]) <= y_perc[1]:
            #     await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{MOUSE_FINGER}", f"{'%04d' % y}0", f"{'%04d' % x}0")

            # OR Direct coordinates (works with high sensitivity, but not recommended)
            # x = event.pos[0]
            # y = SCREEN_SIZE[1]-event.pos[1]

            await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_MOVE}{MOUSE_FINGER}", f"{'%04d' % y}0", f"{'%04d' % x}0")

        # Called when a mouse button is pressed
        if event.type == pygame.MOUSEBUTTONDOWN:
            # MOUSEBUTTONDOWN events have a pos and a button attribute
            # which you can use as well. This will be printed once per
            # event / mouse click.
            # print coordnates in portrait mode for troubleshooting
            key = event.button
            try:
                key = mapped[event.button]
            except KeyError:
                pass
            log.debug(f"Current Mouse Button Pressed: {event.button} ({key})")
            log.debug(f"Mouse Clicked Screen Position (Portrait Coordinates): {(SCREEN_SIZE[1]-event.pos[1], event.pos[0])}")

            # Program mouse buttons
            if pm and not pk:
                print(f"Left click mouse on location on image to program mouse button: {key}")
                pk = key
                if event.button == 1:
                    clicked = 0

            if pm and pk and event.button == 1 and clicked > 0:
                await draw(pk, (float(event.pos[0]), float(event.pos[1])), 10, (0, 0, 255))
                # Program the previously selected key
                await SetConfig(pk, f"{'%04d' % (SCREEN_SIZE[1]-event.pos[1])}0", f"{'%04d' % event.pos[0]}0")
                pk = None
                print('\nPress any key/mouse button to program it...')
            elif event.button == 1:
                await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS['LBTN'][0]}", COORDS['LBTN'][1], COORDS['LBTN'][2])
            elif event.button == 3:
                await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS['RBTN'][0]}", COORDS['RBTN'][1], COORDS['RBTN'][2])

            # LBTN click tracker
            if pm and pk and event.button == 1:
                clicked += 1

        # Called when a mouse button is released
        if not pm and event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{COORDS['LBTN'][0]}", COORDS['LBTN'][1], COORDS['LBTN'][2])
            elif event.button == 3:
                await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{COORDS['RBTN'][0]}", COORDS['RBTN'][1], COORDS['RBTN'][2])


        # Called when a keyboard key is pressed
        if event.type == pygame.KEYDOWN:
            key = pygame.key.name(event.key)

            log.debug(f"Current Key Pressed: {key}")

            if event.key == pygame.K_k:
                if pm:
                    log.info('Exiting key program mode...')
                    pm = 0
                else:
                    log.info('Entering key program mode (press "k" or "j" to exit)...')
                    print('\nPress any key/mouse button to program it...')
                    pm = 1
                    await erase()
                    for key in COORDS:
                        await draw(key, (float(COORDS[key][2])/10, SCREEN_SIZE[1]-float(COORDS[key][1])/10), 20, (0, 255, 0))
            elif event.key == pygame.K_j:
                if pm:
                    log.info('Exiting joystick program mode...')
                    pm = 0
                else:
                    log.info('Entering joystick program mode (press "j" or "k" to exit)...')
                    print("\nProgramming joystick center, left click mouse on joystick center position: J_CENTER")
                    pm = 1
                    pk = 'J_CENTER'
                    await erase()

            if pm and event.key not in {pygame.K_k, pygame.K_j, pygame.K_l, pygame.K_p, pygame.K_0, pygame.K_ESCAPE}:
                if event.key in {pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d}:
                    print(f"Left click mouse on joystick edge location for key: {key}")
                    pk = key
                else:
                    print(f"Left click mouse on location on image to program key: {key}")
                    pk = key
            else:
                # Exit due to input grab
                if event.key == pygame.K_0:
                    pygame.quit()
                    exit()

                if event.key == pygame.K_l:
                    if pygame.event.get_grab() is True:
                        log.info('Input lock removed!')
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        log.info('Input locked to pygame window, press "l" to unlock')
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                if event.key == pygame.K_p:
                    if log.getEffectiveLevel() == 10:
                        log.info('Debugging mode disabled!')
                        log.setLevel(logging.INFO)
                        await erase()
                    else:
                        log.info('Debugging mode enabled, press "p" to disable')
                        log.setLevel(logging.DEBUG)
                        await erase()
                if event.key == pygame.K_ESCAPE:
                    log.info('Resetting finger indices')
                    await reset_fingers()
                if event.key in {pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d}:
                    active.append(key)
                    # await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS['J_CENTER'][0]}", COORDS['J_CENTER'][1], COORDS['J_CENTER'][2])  # Worked better when only one touch down event was set on start/reset (ESCAPE).
                    await pressed_action(active)
                try:
                    if event.key not in {pygame.K_k, pygame.K_j, pygame.K_l, pygame.K_p, pygame.K_0, pygame.K_ESCAPE, pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d}:
                        await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS[key][0]}", COORDS[key][1], COORDS[key][2])
                except KeyError:
                    pass

        # Called when a keyboard key is released
        if not pm and event.type == pygame.KEYUP:
            key = pygame.key.name(event.key)
            try:
                if event.key not in {pygame.K_k, pygame.K_j, pygame.K_l, pygame.K_p, pygame.K_0, pygame.K_ESCAPE, pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d}:
                    await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{COORDS[key][0]}", COORDS[key][1], COORDS[key][2])
            except KeyError:
                pass
            if event.key in {pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d}:
                if key in active:
                    active.remove(key)
                if active:
                    await pressed_action(active)
                else:
                    # await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{COORDS[key][0]}", COORDS[key][1], COORDS[key][2]) # This will be the final coords of the pressed key
                    await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_MOVE}{COORDS['J_CENTER'][0]}", COORDS['J_CENTER'][1], COORDS['J_CENTER'][2])  # Seemed to work better for CoDm


async def pressed_action(active):
    """
    This is a helper module for looping through movement coordinates
    """
    if 'a' in active and 'd' in active:
        if active.index('a') > active.index('d'):
            active.remove('d')
        else:
            active.remove('a')
    if 'w' in active and 's' in active:
        if active.index('w') > active.index('s'):
            active.remove('s')
        else:
            active.remove('w')

    key = '_'.join(sorted(active))
    log.debug(f"Active Key(s) Pressed: {key}")

    try:
        # it = iter(COORDS[key])
        # for y in it:
        #     events = ''.join(f"{TOUCH_MOVE}{MOVE_FINGER}{x[0]}{x[1]}" for x in (y, next(it)))
        # s.send(f"{TOUCH_TASK}{DUAL_EVENT}{events}\r\n".encode())
        x = int(COORDS['J_CENTER'][1])
        y = int(COORDS['J_CENTER'][2])
        x_incr = (int(COORDS[key][1]) - x) / MOVES
        y_incr = (int(COORDS[key][2]) - y) / MOVES
        [await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_MOVE}{COORDS[key][0]}", f"0{'%04d' % (x+int(x_incr * m))}", f"0{'%04d' % (y+int(y_incr * m))}") for m in range(1, MOVES + 1)]
        # unused_list = [await sender(key, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_MOVE}{COORDS[key][0]}", coords[0], coords[1]) for coords in COORDS[key]]
    except KeyError:
        pass


async def sender(key, data, x, y):
    """
    This is a helper module responsible for actually sending the socket data to the iDevice.
    """
    # "x" and "y" coordinates always arive here for portrait mode.
    await asyncio.sleep(0.003)
    s.send(f"{data}{x}{y}\r\n".encode())

    # Print the dots to the screen in landscape mode
    if log.getEffectiveLevel() == 10:
        if key is not None:
            # print coordnates in portrait mode for troubleshooting
            log.debug(f"Sent to iDevice (Portrait Mode): {data}, {x}, {y}")
        await draw(key, (float(y)/10, SCREEN_SIZE[1]-float(x)/10), 5, (0, 255, 0))


async def draw(key, dst, size, color):
    pygame.draw.circle(screen, color,dst, size, size)
    if key is not None:
        text_surface = font.render(key, 0, (0, 0, 0))
        screen.blit(text_surface, dest=dst)
    pygame.display.update()


async def erase():
    screen.blit(background, (0,0))
    pygame.display.update()


async def reset_fingers():
    # Reset touch on finger range.
    for i in range(20):
        await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_UP}{'%02d' % i}", '1000', '01000')
    await asyncio.sleep(0.01)
    await sender('w', f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS['J_CENTER'][0]}", COORDS['J_CENTER'][1], COORDS['J_CENTER'][2])


async def run():
    """
    This module is used to initialize touch on the iDevice and call the rest of the modules asyncrounously.
    """
    # Initialze screen.
    s.send("252\r\n".encode())
    # Reset touch on finger range.
    await reset_fingers()

    s.send("252\r\n".encode())
    await sender(None, f"{TOUCH_TASK}{SINGLE_EVENT}{TOUCH_DOWN}{COORDS['FPS'][0]}", COORDS['FPS'][1], COORDS['FPS'][2])

    # Start scanning for input
    await input_monitor()


async def SetConfig(key, x, y):
    global COORDS
    finger = '19'

    # Change coord
    if key in COORDS:
        finger = COORDS[key][0]
        log.info(f"Key '{key}' coords changed from {COORDS[key]} to {finger, x, y}")
    # Set new coord.
    else:
        log.info(f"Key '{key}' coords added {finger, x, y}")
    COORDS[key] = [finger, x, y]

    log.debug(f"Coord changes: Finger: {finger}, Key: {key}, X:{x}, Y:{y}")

    # from pprint import pprint
    # pprint(COORDS)

    # Write changes back to file.
    write_json(COORDS, 'config')
    log.info('Successfully wrote changes to file.')


def gui_input():
    global DEVICE_IP
    layout = [[sg.T("")], [sg.Text("IP address: "), sg.Input(default_text=DEVICE_IP, key='-IN-')] ,[sg.Button("Start", bind_return_key=True)]]

    ###Building Window
    window = sg.Window('Enter/Verify IP Address for iDevice', layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            exit()
        # Import image file to CWD
        elif event == "Start":
            DEVICE_IP = values["-IN-"]
            log.info(f'Set device IP to {DEVICE_IP}.')
            window.close()
            break


def write_json(data, filename):
    with FileLock(f"{CWD}{LOC}{filename}.json.lock"):
        with open(f"{CWD}{LOC}{filename}.json", 'w') as file:
            ujson.dump(data, file, indent=4)


def create_aio_loop():
    """
    This main which will initialize the async event loop.
    """
    print(f'Welcome to the CoDm ZXTouch Python Client v{__version__} Alpha!\n')
    print('Press "l" to toggle input lock to window.')
    print('Press "p" to toggle printing debug information including green coordinate dots on window image.')
    print('Press "k" to change key mappings.')
    print('Press "j" to change joystick center position.')
    print('Press "esc" to reset all finger indices.')
    print('Press "0" quit.')

    asyncio.run(run())


if __name__ == '__main__':
    s = socket.socket()
    
    # Call user input
    gui_input()

    s.connect((DEVICE_IP, 6000))  # connect to the tweak
    sleep(0.2)  # please sleep after connection.

    # initialising pygame
    pygame.init()

    # Creating display window taken screenshot (no login required)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    font = pygame.font.Font(pygame.font.get_default_font(), 16)
    background = pygame.image.load(IMG).convert()
    background = pygame.transform.scale(background, SCREEN_SIZE)
    screen.blit(background, (0,0))
    pygame.display.update()
    pygame.mouse.set_visible(True)

    # Check for windows
    if name == 'nt':
        LOC = '\\'
        asyncio.set_event_loop(asyncio.ProactorEventLoop())
    else:
        import uvloop
        # Instantiate uvloop
        uvloop.install()

    # Initiate async modules
    create_aio_loop()

    s.close()
