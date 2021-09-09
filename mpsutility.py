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
# Files:       mpsutility.py (utility handlers & main loop), mpsutility.json (utility configuration)
# Instructions:(1) Modify mpsutility.json, (2) Run mpsutility.py in same folder with mpsutility.json
#              (3) Alternatively, command line driven execution can be accomplished with...             
#               mpsutility build_id region repeatCount[1:100000] pauseCount[1:600] debug[1|0]
# Interactive: The utility can be used interactively at the command line after running mpsutility.py
#
#                    1 - List Build Settings
#                    2 - List Virtual Machines
#                    3 - List Multiplayer Servers      
#                    4 - Get Multiplayer Server Details
#                    5 - Request Multiplayer Server    
#                    6 - Shutdown Multiplayer Server   
#                    7 - Update Build Regions
#                    8 - List Headers
#                    9 - Exit
#                    Chose a utility option:

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
import sys
import time
import uuid

#############################################################################
# MPS Utility Global Variables
#############################################################################

#global dictionary settings
mps = {}
appchoice = {}
config = 'mpsutility.json'

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
    resp = MPSAPIHandler(method, headers, data, debug)
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
            regLength = len(regionslist)
            build['RegionsLength']=regLength
            buildlist.append(build)
            mps['builds']=buildlist
        return True
    else:
        return False

# Lists MPS VM settings; calls MultiplayerServer/ListVirtualMachineSummaries
def ListVirtualMachines(appchoice, debug=0):

    method = "MultiplayerServer/ListVirtualMachineSummaries"
    data = {'BuildId': appchoice['BuildId'], 'Region': appchoice['Region'], 'PageSize': '10'}
    resp = MPSAPIHandler(method, headers, data, debug)

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
    data = {'BuildId': appchoice['BuildId'], 'Region': appchoice['Region'] ,'PageSize': 100}
    resp = MPSAPIHandler(method, headers, data, debug)

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
    status = GetServerSelection(appchoice)
    if status == False:
        return False

    if 'SessionId' not in appchoice:
        return False
        
    method = "MultiplayerServer/GetMultiplayerServerDetails"
    data = {'BuildId': appchoice['BuildId'], 'SessionId': appchoice['SessionId'], 'Region':  appchoice['Region']  }
    resp = MPSAPIHandler(method, headers, data, debug)

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

    #Manual check for mps['Bulk'] == True:
    if GetBulkConfirm()=='Y':        
        print("shutting down servers for all regions")
        shutdownStatus = ShutdownMultiplayerServerBulkRegion(appchoice)
    else:
        shutdownStatus  =  ShutdownMultiplayerServerSingle(appchoice)
    return shutdownStatus

def ShutdownMultiplayerServerBulkRegion( appchoice ):
    #Loop 1 - Fetch all servers to capture session IDs
    method = "MultiplayerServer/ListMultiplayerServers"
    data = {'BuildId': appchoice['BuildId'], 'Region': appchoice['Region'], 'PageSize': 120}
    resp = MPSAPIHandler(method, headers, data, 0)

    if resp['code'] == 200:
        sessionList=[]
        #Loop 2 - Fetch all sessions
        for x in resp['data']['MultiplayerServerSummaries']:
            if 'SessionId' in x:
                sessionList.append(x['SessionId'])
    else:
        print(json.dumps(resp, sort_keys=False, indent=4))
        return False

    sessionListLength = len(sessionList)
    appchoice['SessionIds'] = sessionList
    if sessionListLength > 0:

        #Loop 3 - Iterate each session
        for y in range(sessionListLength):
            if 'BuildName' in appchoice:
                print("Shutting down Build {} ID = {} in {} where session = {}".format(appchoice['BuildName'],
                    appchoice['BuildId'], appchoice['Region'], appchoice['SessionIds'][y] ) )
            else:
                print("Shutting down session {} in Region {} for Build ID {}".format(appchoice['SessionIds'][y], 
                    appchoice['Region'], appchoice['BuildId'] ) )
            
            #Shutdown server with bldDictionary key values
            method = "MultiplayerServer/ShutdownMultiplayerServer"
            data = {'BuildId': appchoice['BuildId'], 'SessionId': appchoice['SessionIds'][y], 'Region':  appchoice['Region'] }
            resp = MPSAPIHandler(method, headers, data, 0)

            if resp['code'] != 200:
                print(json.dumps(resp, sort_keys=False, indent=4))
                return False
    return True

def ShutdownMultiplayerServerSingle(appchoice, debug=0):
    #Get Multiplayer Server Details of a given Session ID
    GetServerSelection(appchoice)
    
    if 'SessionId' not in appchoice:    #Fail if SessionID not populated
        return False

    method = "MultiplayerServer/ShutdownMultiplayerServer"
    data = {'BuildId': appchoice['BuildId'], 'SessionId': appchoice['SessionId'], 'Region':  appchoice['Region'] }
    resp = MPSAPIHandler(method, headers, data, debug)

    if resp['code'] == 200:
        print(json.dumps(resp, sort_keys=False, indent=4))
        return True
    else:
        return False


def GetBulkConfirm():

    #Confirm bulk operation
    confirm = input("Begin bulk operation?  Y for Yes or N for No: ")
    if confirm.isalpha()==True:
        confirm = confirm.upper()
        
    while (confirm != 'Y' and confirm != 'N'):
        confirm = input("Begin bulk operation?  Y for Yes or N for No: ")
        if confirm.isalpha():
            confirm = confirm.upper()

    return confirm


def GetAllocateConfirm(repeat, pause):
    
    #Confirm start of allocations
    print("Scheduling {} server allocations spaced {} seconds apart".format(repeat, pause))
    confirm = input("Begin Allocating Servers?  Y for Yes or N for No: ")
    if confirm.isalpha()==True:
        confirm = confirm.upper()
        
    while (confirm != 'Y' and confirm != 'N'):
        confirm = input("Begin Allocating Servers?  Y for Yes or N for No: ")
        if confirm.isalpha():
            confirm = confirm.upper()

    return confirm

def GetAllocateRepeatAndPause():

    #Determine quantity of request server allocations
    maxrepeat = 100000

    repeat = input("Chose from 1 to 100,000 allocations: ")
    if repeat.isnumeric():
        repeat = int(repeat)
        
    while repeat not in range( 1, maxrepeat + 1 ):
        repeat = input("Chose from 1 to 100,000 allocations: ")
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

    return repeat, pause


# Allocates MPS servers; calls MultiplayerServer/RequestMultiplayerServer
# Calls API to quanity entered by user and spaced by seconds length also entered by user
def AllocateHandler(appchoice, repeat=1, pause=1, debug=0):

    count = 0
    for count in range(repeat):
        sessionId = getRandomGUID()

        method = "MultiplayerServer/RequestMultiplayerServer"
        data = {'BuildId': appchoice['BuildId'], 'SessionId': sessionId, 'PreferredRegions':  [ appchoice['Region'] ] }
        resp = MPSAPIHandler(method, headers, data, debug)

        if resp['code'] != 200:
            print(json.dumps(resp, sort_keys=False, indent=4))
        else:
            #Print API response per iteration
            print("Server allocation {} of {} - Waiting {} seconds......".format( count+1, repeat, pause ) )

        time.sleep(pause)

    return True

# Allocates MPS servers; calls MultiplayerServer/RequestMultiplayerServer
# Calls API to quanity entered by user and spaced by seconds length also entered by user
def RequestMultiplayerServer(appchoice, debug=0):

    #Confirm repeat and puase
    repeat, pause = GetAllocateRepeatAndPause()

    #Confirm start of allocations
    confirm = GetAllocateConfirm(repeat, pause)    

    if confirm == 'N':
        return False
    elif confirm == 'Y':

        allocateStatus = AllocateHandler(appchoice, repeat, pause, debug)

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
    resp = MPSAPIHandler(method, headers, data, debug)

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
def MPSAPIHandler(method, headers, data, debug = 0):
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
    quitIndex = 0
    sessionIndex = 0
    for session in mps["servers"]:
        if 'SessionId' in session:
            print("[{}] - Session ID: {} ".format(sessionIndex, session['SessionId'] ) )
        else:
            print("[{}] - {} ".format(sessionIndex, "Standby Server (Do Not Select)" ) )
        sessionIndex += 1
        quitIndex = sessionIndex
    print("[{}] - Cancel ".format(quitIndex) )

    if sessionIndex == 0:       # check if there are no active servers
        return
    else:
        sessionChoice = input("Chose a session: ")
        if sessionChoice.isnumeric():
            sessionChoice = int(sessionChoice)

        while sessionChoice not in range(sessionIndex+1):
            sessionChoice = input("Chose a session: ")
            if sessionChoice.isnumeric():
                sessionChoice = int(sessionChoice)

    sessionNum = int(sessionChoice)

    #Handle cancel selection
    if sessionNum == quitIndex:
        appSelection['SessionId']=False
        print("Cancel selected...")
        return appSelection['SessionId']

    if sessionNum in range(sessionIndex):
        print( "Session ", mps["servers"][sessionNum]['SessionId'], " Selected")
        appSelection['SessionId'] = mps["servers"][sessionNum]['SessionId']

    return appSelection['SessionId']

# Initializes utility as server side app; calls Authentication/GetEntityToken
def authUtility():

    method = "Authentication/GetEntityToken"
    data = {}
    resp = MPSAPIHandler(method, headers, data)
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

def initCommandLineOptions():

    operation = ""
    bldChoice = {}
    status = 0
    argumentLength = len(sys.argv)

    #Print command line statements
    if argumentLength == 2:
        print("mpsutility allocate build_id region repeatCount[1:100000] pauseCount[1:600] debug[1|0]")
        print("mpsutility shutdown build_id region debug[1|0]")
        exit()
    
    #Assign command line variables
    if argumentLength > 1:
        if sys.argv[1].isalpha():
            operation = sys.argv[1]

    if argumentLength > 4:          #Assign build choice object
        if sys.argv[2].isprintable():
            bldChoice['BuildId'] = sys.argv[2]
        if sys.argv[3].isalpha():
            bldChoice['Region'] = sys.argv[3]

    if argumentLength == 5: # if shutdown, handle elements 5
        if sys.argv[4].isnumeric():
            debug = int(sys.argv[4])
        else:
            debug = 1
    
    if argumentLength == 7: # if allocate, handle elements 6-8
        if sys.argv[4].isnumeric():
            repeat = int(sys.argv[4])
        else:
            repeat = 1
        if sys.argv[5].isnumeric():
            pause = int(sys.argv[5])
        else:
            pause = 1
        if sys.argv[6].isnumeric():
            debug = int(sys.argv[6])
        else:
            debug = 1

    # Handle operaiton request
    if operation == 'allocate':
        status = AllocateHandler(bldChoice, repeat, pause, debug)
    elif operation == 'shutdown':
        status = ShutdownMultiplayerServerBulkRegion( bldChoice )
            
    # Return operation status
    if argumentLength > 1:
        if status == True:
            print(str(sys.argv), "successfully executed")
            exit()
        else:
            print(str(sys.argv), "failed")
            exit()
    
# Initializes utility configuration; dependency on mpsutility.cfg file
# Populates secrete key and title id
def initConfig(debug=0):

    global config 
    mpsutilityconfig = {}

    try:
        fhand=open(config, "r")
    except:
        print("Required file {} not found".format(config))
        exit()

    count = 0

    jsonContent = fhand.read()
    mpsutilityconfig = json.loads(jsonContent)
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
    print("....................................")
    print("MPS Utilit can be run interactively with the following command line options")
    print("     mpsutility allocate build_id region repeatCount[1:100000] pauseCount[1:600] debug[1|0]")
    print("     mpsutility shutdown build_id region debug[1|0]")
    print()

    return

#Defines main console loop and processes user input
def MainLoop():

    global title_id

    cfgResult = initConfig()
    title_id = cfgResult['title_id']                    #change title id to titles title id
    headers['X-SecretKey'] = cfgResult['secret_key']    #change X-SecretKey to titles secret key

    authResult = authUtility()
    
    initUtility()

    initCommandLineOptions()

    firstRun = True

    while authResult == True:
        
        while firstRun == False:
            choice = input("Enter C to continue...")
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

        if choice == 0 :     #List Command Line Arugments
            print("mpsutility build_id region repeatCount[1:100000] pauseCount[1:600] debug[1|0]")

        elif choice == 1:     #List Build Settings
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
            ShutdownMultiplayerServer(appchoice)

        elif choice == 7:   #Update Build Region
            UpdateBuildRegion(appchoice, 1)

        elif choice == 8:   #List headers
            print(json.dumps(headers, indent=3))
        
        elif choice == 9:   #Exit application
            print("Exiting application")
            quit()

        firstRun = False

# This is the start of the MPS utility
os.system('cls')

MainLoop()
