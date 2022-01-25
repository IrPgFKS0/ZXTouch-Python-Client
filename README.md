# ZXTouch-Python-Client
A generic zxtouch python client for Windows/Mac/Linux for keyboard gaming (CoDm, PUBG, etc...)<p></p>
If this helped you out, Buy me a coffee [here](https://buymeacoffee.com/modderan)

## Description
Linked and dependant on this project... https://github.com/xuan32546/IOS13-SimulateTouch<p></p>
This is a client that maps keyboard/mouse functionality for any game.  You will need to modify coordinates `config.json` file for your specific game, but out of the box this will support CoDm on iPhone11 with the attached layout.

## Features
* Functional resolution coordinate mapping and realtime plotting (via debug mode).
* Screen input locking (FPS).
* Importable screenshot of actual layout for button mapping (similar to ZXTouch.net site).
* No need to login to a website to run coordinate as you need to plot coordinates directing in script.
* Buttons are already mapped and working for iPhone XR/11 (828x1792) resolution (see screenshot for working mappings)
* Fully working on OSX Big Sur, should also work on windows, but have not tested.
* Will likely need to input device IP (127.0.0.1 did not work for me).

## How to use
1. Install python dependencies.
`pip install -r requirements.txt`
2. `cd /path/to/ZXtouch\ CoDm\ Client/`
3. A file browser box will pop up the first time you run the script asking for a screen shot of you game button layout (ensure this is a non compressed image), select the file and click "submit".
3. `python3 main.py <IP Address of device>` # Exclude the IP if connected via USB to Windows w/ Itunes installed (will use 127.0.0.1).

## How to set keys

### Map Keys
1. Press "k" to enter key programming mode.
2. Press the key you want to program, then click the left mouse button once on the location for the key.
3. Confirmation of the programmed key will be signified by a blue dot and the key next to it on the background image and shown in the console output.
4. Press another key you want to program and follow steps 2-3 again or press "k" again to exit key programming mode.

### Map Joystick Center
1. Press "j" to enter joystick programming mode.
2. The center of the joystick will already be selected so all you need to do is click the left mouse button in the center of your games joystick location.
3. Confirmation of joystick center will be signified by a blue dot and 'J_CENTER' on the background image and shown in the console output.
4. Press "j" again to exit key programming mode.