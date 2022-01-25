# ZXTouch-Python-Client
A generic zxtouch python client for Windows/Mac/Linux for keyboard gaming (CoDm, PUBG, etc...)<p></p>
If this helped you out, Buy me a coffee [here](https://buymeacoffee.com/modderan)

## Description
Linked and dependant on this project... https://github.com/xuan32546/IOS13-SimulateTouch
<p>This is a client that maps keyboard/mouse functionality for any game.  You will need to modify coordinates `config.json` file for your specific game, but out of the box this will support CoDm on iPhone11 with the attached layout.</p>

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
3. `python3 main.py <IP Address of device>` # Exclude the IP if connected via USB to Windows w/ Itunes installed (will use 127.0.0.1).  

