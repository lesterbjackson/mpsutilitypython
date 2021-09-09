
Author:      Lester Jackson

GitHub:      https://github.com/lesterjackson

Title:       MPSUtilityPython

Published:   Inital September 6, 2021

Description: A menu driven console utility coded in Python for PlayFab Multiplayer Server developers.  
             The utility provides three functions: (1) Allocates game servers, (2) Configures game server limits
             and (3) Reports status for game server builds, virtual machines and sessions

Support:     Implemented wtih Python 3.9.5

Background:  The utility calls and returns PlayFab Multiplayer Server REST API responses

Files:       mpsutility.py (main loop & supporting functions), mpsutility.cfg (utility configuration)

Instructions:(1) Modify mpsutility.cfg, (2) Run mpsutility.py in same folder with mpsutility.cfg

Interactive: The utility can be used interactively at the command line after running mpsutility.py

                    1 - List Build Settings
                    2 - List Virtual Machines
                    3 - List Multiplayer Servers      
                    4 - Get Multiplayer Server Details
                    5 - Request Multiplayer Server    
                    6 - Shutdown Multiplayer Server   
                    7 - Update Build Regions
                    8 - List Headers
                    9 - Exit
                    Chose a utility option:

Examples:
             python mpsutility.py allocate a780dff0-4f11-4cb1-a449-75ac1207616d WestUS 20 4 0
             python mpsutility.py shutdown a780dff0-4f11-4cb1-a449-75ac1207616d WestUS 1

Tested:      Only tested in Windows, concievably should work in Linux and Mac OS X

Copyright:   Lester Jackson (aka Bingfoot)

License:     Apache License 2.0

Resources:   

- https://docs.microsoft.com/en-us/rest/api/playfab/multiplayer/multiplayer-server
- https://pynative.com/python-post-json-using-requests-library/
- https://www.scrapingbee.com/blog/how-to-send-post-python-requests/
- https://appdividend.com/2020/06/22/python-requests-post-method-example/

Credits:     Special thanks to friends, colleages and family...

- Dimitris Gkantsios https://github.com/dgkanatsios
- Ardon Bailey https://github.com/waystilos

