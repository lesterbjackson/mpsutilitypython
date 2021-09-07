#
# Author:      Lester Jackson
# GitHub:      https://github.com/lesterjackson
# Title:       MPSUtilityPython
# Published:   Inital September 6, 2021
# Description: A menu driven console utility coded in Python for PlayFab Multiplayer Server developers.  
#              The utility provides three functions: (1) Allocates game servers, (2) Configures game server limits
#              and (3) reports hosted status for game server builds, virtual machines and sessions
# Support:     Implemented wtih Python 3.9.5
# Background:  The utility calls and returns PlayFab Multiplayer Server REST API responses
# Files:       mpsutility.py (main loop & supporting functions), mpsutility.cfg (utility configuration)
# Instructions:(1) Modify mpsutility.cfg, (2) Run mpsutility.py in same folder with mpsutility.cfg
# Tested:      Only0 tested in Windows, concievably should work in Linux and Mac OS X
# Copyright:   Lester Jackson (aka Bingfoot)
# License:     Apache License 2.0
# Resources:   https://docs.microsoft.com/en-us/rest/api/playfab/multiplayer/multiplayer-server
#              https://pynative.com/python-post-json-using-requests-library/
#              https://www.scrapingbee.com/blog/how-to-send-post-python-requests/
#              https://appdividend.com/2020/06/22/python-requests-post-method-example/
# Credits:     Special thanks to friends, colleages and family...
#              - Dimitris Gkantsios https://github.com/dgkanatsios
#              - Ardon Bailey https://github.com/waystilos
#              - Professor Humaira Jackson for bearing with me in my first GitHub project during 2021 Labor Day weekend
#              - Coursera Python 3 Programming https://www.coursera.org/specializations/python-3-programming
#

#############################################################################
# MPS Utility Import Modules
#############################################################################

import requests
import json
import os
import time
import uuid

#############################################################################
# MPS Utility Global Variables
#############################################################################

#global dictionary settings
mps = {}
appchoice = {}

#change endpoint for testing or unique vertical
endpoint = "playfabapi.com/" 

#default headers
headers = {
    "X-PlayFabSDK": "PostmanCollection-0.125.210628",
    "Content-Type": "application/json"    
}

#title id configured in mpsutility.cfg and populated at start of main loop
title_id = ""

#############################################################################
# MPS Utility Handlers
#############################################################################

# Lists MPS build settings; calls MultiplayerServer/ListBuildSummariesV2
def ListBuildSettings(debug):

    method = "MultiplayerServer/ListBuildSummariesV2"
    data = {'PageSize': '10'}
    resp = callAPI(method, headers, data, debug)
    if resp['code'] == 200:
        buildlist=[]
        for x in resp['data']['BuildSummaries']:
            regionslist=[]
            build = {}

            build['BuildName'] = x['BuildName']
            build['BuildId'] = x['BuildId']

            for y in x['RegionConfigurations']:
                regionslist.append(y['Region'])
                
            build['Regions'] = regionslist
            buildlist.append(build)
            mps['builds']=buildlist
        return True
    else:
        return False

# Lists MPS VM settings; calls MultiplayerServer/ListVirtualMachineSummaries
def ListVirtualMachines(appchoice, debug=0):

    method = "MultiplayerServer/ListVirtualMachineSummaries"
    data = {'BuildId': appchoice['BuildId'], 'Region': appchoice['Region'], 'PageSize': '10'}
    resp = callAPI(method, headers, data, debug)

    if resp['code'] == 200:
        #print(method, " Success")
        vmlist=[]
        for x in resp['data']['VirtualMachines']:
            vm = {}

            vm['VmId'] = x['VmId']
            vm['State'] = x['State']
            vm['HealthStatus'] = x['HealthStatus']
                
            vmlist.append(vm)
            mps['vms']=vmlist
        return True
    else:
        return False

# Lists MPS servers (standby & active); calls MultiplayerServer/ListMultiplayerServers
def ListMultiplayerServers(appchoice, debug=0):

    method = "MultiplayerServer/ListMultiplayerServers"
    data = {'BuildId': appchoice['BuildId'], 'Region': appchoice['Region']}
    resp = callAPI(method, headers, data, debug)

    if resp['code'] == 200:
        serverlist=[]
        for x in resp['data']['MultiplayerServerSummaries']:
            server = {}

            server['ServerId'] = x['ServerId']
            server['VmId']     = x['VmId']
            server['Region']   = x['Region']
            server['State']    = x['State']
            server['ConnectedPlayers'] = x['ConnectedPlayers']
            server['LastStateTransitionTime'] = x['LastStateTransitionTime']
            server['ServerId'] = x['ServerId']

            if 'SessionId' in x:
                server['SessionId'] = x['SessionId']

            serverlist.append(server)
        mps['servers']=serverlist
        return True
    else:
        return False

# Lists MPS server connection details (FQDN, IP, Ports, etc.); calls MultiplayerServer/GetMultiplayerServerDetails
def GetMultiplayerServerDetails(appchoice, debug=0):

    #Cache Multiplayer Servers Results with Session IDs
    ListMultiplayerServers(appchoice, debug)

    #Get Multiplayer Server Details of a given Session ID
    GetServerSelection(appchoice)
    if 'SessionId' not in appchoice:
        return False
        
    method = "MultiplayerServer/GetMultiplayerServerDetails"
    data = {'BuildId': appchoice['BuildId'], 'SessionId': appchoice['SessionId'], 'Region':  appchoice['Region']  }
    resp = callAPI(method, headers, data, debug)

    if resp['code'] == 200:

        serverDetails={}

        serverDetails['SessionId']         = resp['data']['SessionId']
        serverDetails['ServerId']          = resp['data']['ServerId']
        serverDetails['IPV4Address']       = resp['data']['IPV4Address']
        serverDetails['VmId']              = resp['data']['VmId']
        serverDetails['FQDN']              = resp['data']['FQDN']
        serverDetails['Region']            = resp['data']['Region']
        serverDetails['State']             = resp['data']['State']
        serverDetails['BuildId']           = resp['data']['BuildId']
        serverDetails['Ports']             = resp['data']['Ports']
        serverDetails['ConnectedPlayers']  = resp['data']['ConnectedPlayers']
            
        mps['serverdetails'] = serverDetails
        
        print(json.dumps(mps['serverdetails'], sort_keys=False, indent=4))

        return True
    else:
        return False

# Shutsdown MPS server ; calls MultiplayerServer/ShutdownMultiplayerServer
def ShutdownMultiplayerServer(appchoice, debug=0):   

    #Cache Multiplayer Servers Results with Session IDs
    ListMultiplayerServers(appchoice, debug)

    #Get Multiplayer Server Details of a given Session ID
    GetServerSelection(appchoice)
    
    if 'SessionId' not in appchoice:    #Fail if SessionID not populated
        return False

    method = "MultiplayerServer/ShutdownMultiplayerServer"
    data = {'BuildId': appchoice['BuildId'], 'SessionId': appchoice['SessionId'], 'Region':  appchoice['Region'] }
    resp = callAPI(method, headers, data, debug)

    if resp['code'] == 200:
        print(json.dumps(resp, sort_keys=False, indent=4))
        return True
    else:
        return False

# Allocates MPS servers; calls MultiplayerServer/RequestMultiplayerServer
# Calls API to quanity entered by user and spaced by seconds length also entered by user
def RequestMultiplayerServer(appchoice, debug=0):

    #Determine quantity of request server allocations
    maxrepeat = 100

    repeat = input("Chose from 1 to 100 allocations: ")
    if repeat.isnumeric():
        repeat = int(repeat)
        
    while repeat not in range( 1, maxrepeat + 1 ):
        repeat = input("Chose from 1 to 100 allocations: ")
        if repeat.isnumeric():
            repeat = int(repeat)

    #Determine quantity of seconds between server allocations

    minpause = 1
    maxpause = 600

    pause = input("Chose from 1 to 600 seconds between allocations: ")
    if pause.isnumeric():
        pause = int(pause)
        
    while pause not in range( minpause, maxpause + 1 ):
        pause = input("Chose from 1 to 600 seconds between allocations: ")
        if pause.isnumeric():
            pause = int(pause)

    #Confirm start of allocations
    print("Scheduling {} server allocations spaced {} seconds apart".format(repeat, pause))
    confirm = input("Begin Allocating Servers?  Y for Yes or N for No: ")
    if confirm.isalpha()==True:
        confirm = confirm.upper()
        
    while (confirm != 'Y' and confirm != 'N'):
        confirm = input("Begin Allocating Servers?  Y for Yes or N for No: ")
        if confirm.isalpha():
            confirm = confirm.upper()

    if confirm == 'N':
        return False
    elif confirm == 'Y':
        count = 0
        for count in range(repeat):
            sessionId = getRandomGUID()

            method = "MultiplayerServer/RequestMultiplayerServer"
            data = {'BuildId': appchoice['BuildId'], 'SessionId': sessionId, 'PreferredRegions':  [ appchoice['Region'] ] }
            resp = callAPI(method, headers, data, debug)

            #Print API response per iteration
            print("Server allocation {} of {} - Waiting {} seconds......".format( count+1, repeat, pause ) )

            time.sleep(pause)
        return True    
    else:
        return False
        
# Updates MPS build server limits (max & standby); calls MultiplayerServer/UpdateBuildRegion
def UpdateBuildRegion(appchoice, debug=0):

    maxservers = int(input("Enter max servers value between 0 to 100: "))
    while maxservers not in range(0,100):
        maxservers = int(input("Enter max servers value between 0 to 100: "))

    standbyservers = int(input("Enter standby servers value between 0 to 100: "))
    while standbyservers not in range(0,100):
        standbyservers = int(input("Enter standby servers value between 0 to 100: "))

    method = "MultiplayerServer/UpdateBuildRegion"
    bldregion = { 'Region': appchoice['Region'], 'MaxServers': maxservers, 'StandbyServers': standbyservers }
    data = {'BuildId': appchoice['BuildId'], 'BuildRegion': bldregion }
    resp = callAPI(method, headers, data, debug)

    if resp['code'] == 200:
        print(json.dumps(resp, sort_keys=False, indent=4))
        return True
    else:
        return False

#############################################################################
# MPS Utility Helpers
#############################################################################

# Make a random UUID; used for session ID in MPS allocations
def getRandomGUID():
    randomSession =  uuid.uuid4()
    return str(randomSession)

#Function that issues HTTP Post to PlayFab REST API
#Optional debug param of 1 prints status code, URL and API response
def callAPI(method, headers, data, debug = 0):
    baseurl = "https://" + title_id + "." + endpoint + method
    responseAPI = requests.post(baseurl, headers = headers, json = data) 
    responseJSON = json.loads(responseAPI.text)
    if debug == 1:
        print("Status code: ", responseAPI.status_code)
        print(responseAPI.url)
        print(json.dumps(responseJSON, indent=2))
    
    return responseJSON
 
# Defines global MPS dictionary object
def GetAppSelection():

    appselection = {}

    bldIndex = 0
    for bld in mps["builds"]:
        print("[{}] - {} ({})".format(bldIndex, bld['BuildName'], bld['BuildId']))
        bldIndex += 1
    
    bldChoice = input("Chose a build: ")
    if bldChoice.isnumeric():
        bldChoice = int(bldChoice)
    
    while bldChoice not in range(bldIndex):
        bldChoice = input("Chose a build: ")
        if bldChoice.isnumeric():
            bldChoice = int(bldChoice)

    bldNum = int(bldChoice)
    if bldNum in range(bldIndex):
        print( "Build ", mps["builds"][bldNum]['BuildName'], " Selected")
        appselection['BuildName'] = mps["builds"][bldNum]['BuildName']
        appselection['BuildId'] = mps["builds"][bldNum]['BuildId']

    regIndex = 0          
    for reg in mps["builds"][bldNum]['Regions']:
        print("[{}] - {} ".format(regIndex, mps["builds"][bldNum]['Regions'][regIndex]))
        regIndex += 1
    
    regionChoice = input("Chose a region: ")
    if regionChoice.isnumeric():
        regionChoice = int(regionChoice)
    
    while regionChoice not in range(regIndex):
        regionChoice = input("Chose a region: ")
        if regionChoice.isnumeric():
            regionChoice = int(bldChoice)

    regNum = int(regionChoice)
    if regNum in range(regIndex):
        print( "Region ", mps["builds"][bldNum]['Regions'][regNum], " Selected")
        appselection['Region'] = mps["builds"][bldNum]['Regions'][regNum]

    return appselection

# Lists and captures session ID from user input
def GetServerSelection(appSelection):

    sessionIndex = 0
    for session in mps["servers"]:
        if 'SessionId' in session:
            print("[{}] - {} (Active) ".format(sessionIndex, session['SessionId'] ) )
        else:
            print("[{}] - {} (Standby)".format(sessionIndex, "N/A" ) )
        sessionIndex += 1
    
    if sessionIndex == 0:       # check if there are no active servers
        return
    else:
        sessionChoice = input("Chose a session: ")
        if sessionChoice.isnumeric():
            sessionChoice = int(sessionChoice)
        
        while sessionChoice not in range(sessionIndex):
            sessionChoice = input("Chose a session: ")
            if sessionChoice.isnumeric():
                sessionChoice = int(sessionChoice)

    sessionNum = int(sessionChoice)
    if sessionNum in range(sessionIndex):
        print( "Session ", mps["servers"][sessionNum]['SessionId'], " Selected")
        appSelection['SessionId'] = mps["servers"][sessionNum]['SessionId']

    return appSelection['SessionId']

# Initializes utility as server side app; calls Authentication/GetEntityToken
def authUtility():

    method = "Authentication/GetEntityToken"
    data = {}
    resp = callAPI(method, headers, data)
    if resp['code'] == 200:
        headers['X-EntityToken'] = resp['data']['EntityToken']
        return True
    else:
        print(method, " Fail")
        return False

# Initializes utility by populating MPS global object
def initUtility():

    ListBuildSettings(0)
    return

# Initializes utility configuration; dependency on mpsutility.cfg file
# Populates secrete key and title id
def initConfig(debug=0):

    CONFIG = 'mpsutility.cfg'
    mpsutilityconfig = {}

    try:
        fhand=open(CONFIG)
    except:
        print("Required file {} not found".format(CONFIG))
        exit()

    count = 0

    for line in fhand:

        if 'TITLE_ID' in line:
            if '#TITLE_ID' in line:
                continue
            mylist = line.split("=")
            mystring = mylist[1].strip()
            mpsutilityconfig['TITLE_ID'] = mystring
            if debug == 1:
                print(line)
                print("value = {} and len = {}".format(mystring, len(mystring) ) )
        elif 'SECRET_KEY' in line:
            if '#SECRET_KEY' in line:
                continue
            mylist = line.split("=")
            mystring = mylist[1].strip()
            mpsutilityconfig['SECRET_KEY'] = mystring
            if debug == 1:
                print(line)
                print("value = {} and len = {}".format(mystring, len(mystring) ) )
    
    fhand.close()

    return mpsutilityconfig

#############################################################################
# MPS Utility Main Loop
#############################################################################

# Menu driven user interface
def callMenu():
    os.system('cls')
    print("1 - List Build Settings")
    print("2 - List Virtual Machines")
    print("3 - List Multiplayer Servers")
    print("4 - Get Multiplayer Server Details")
    print("5 - Request Multiplayer Server")
    print("6 - Shutdown Multiplayer Server")
    print("7 - Update Build Regions")
    print("8 - List Headers")
    print("9 - Exit")
    return

#Defines main console loop and processes user input
def MainLoop():

    global title_id

    cfgResult = initConfig()
    title_id = cfgResult['TITLE_ID']                    #change title id to titles title id
    headers['X-SecretKey'] = cfgResult['SECRET_KEY']    #change X-SecretKey to titles secret key

    authResult = authUtility()
    
    initUtility()

    firstRun = True

    while authResult == True:
        
        while firstRun == False:
            choice = input("Enter C to Continue...")
            if choice == "c" or choice == "C":
                break

        callMenu()

        choice = 0
        while choice not in range(1,10):
            choice = input("Chose a utility option: ")
            if choice.isnumeric():
                choice = int(choice)

        if choice in range(2,8):
            appchoice = GetAppSelection()                

        if choice == 1:     #List Build Settings
            ListBuildSettings(1)

        elif choice == 2:   #List Virtual Machines
            ListVirtualMachines(appchoice, 1)
                
        elif choice == 3:   #List Multiplayer Servers
            ListMultiplayerServers(appchoice, 1)

        elif choice == 4:   #Get Multiplayer Server Details
            GetMultiplayerServerDetails(appchoice, 1)

        elif choice == 5:   #Request Multiplayer Server
            RequestMultiplayerServer(appchoice, 1)

        elif choice == 6:   #Shutdown Multiplayer Server
            ShutdownMultiplayerServer(appchoice, 1)

        elif choice == 7:   #Update Build Region
            UpdateBuildRegion(appchoice, 1)

        elif choice == 8:   #List headers
            print(json.dumps(headers, indent=3))
        
        elif choice == 9:   #Exit application
            print("Existing Application")
            quit()

        firstRun = False

# This is the start of the MPS utility
os.system('cls')

MainLoop()
