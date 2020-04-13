#Imports
import config as cfg
import psutil
from os.path import isfile, join
from os import listdir
import os
import requests
import subprocess
import json
import time
import shutil

class Screenshare(object):
    def __init__(self):
        super(Screenshare, self).__init__()
        self.user_path = '/'.join(os.getcwd().split('\\', 3)[:3])
        self.drive_letter = os.getcwd().split('\\', 1)[0]+'/'
        self.winUsername = os.getlogin()

    #Finds minecraft process and gets info
    def mcProcess(self):
        mcprocess_info = {}

        #Get processes with the name "javaw"
        process = [p for p in psutil.process_iter(attrs=['pid', 'name']) if 'javaw' in p.info['name']]
        if process:
            process = process[0]
            pid = process.info['pid']
            print(f'{cfg.prefix} Minecraft found on PID: {pid}')
        else:
            input(f'Minecraft not found...\nPress enter to continue')
            quit()

        #Get all command line arguments of process
        process = process.cmdline()
        for argument in process:
            if "--" in argument:
                mcprocess_info[argument.split("--")[1]] = process[process.index(argument) + 1]

        self.javawPid = pid
        self.mcPath = mcprocess_info["version"]

        print(f'    Username: {mcprocess_info["username"]}')
        print(f'    Version: {mcprocess_info["version"]}')
        print(f'    Path: {mcprocess_info["gameDir"]}')

    #Downloads all necessary files
    def dependencies(self):
        path = f'{self.drive_letter}/Windows/Temp/Astro'
        if not os.path.exists(path):
            os.mkdir(path)
        with open(f'{path}/strings2.exe', 'wb') as f:
            f.write(requests.get(cfg.strings2Url).content)


    #Gets PID of a process from name
    def getPID(self, name, service=False):
        if service:
            response = str(subprocess.check_output(f'tasklist /svc /FI "Services eq {name}')).split('\\r\\n')
            for process in response:
                if name in process:
                    pid = process.split()[1]
                    return pid
        else:
            pid = [p.pid for p in psutil.process_iter(attrs=['pid', 'name']) if name == p.name()][0]
            return pid

    #Gets/Dumps strings via a PID
    def dump(self, pid):
        cmd = f'{self.drive_letter}/Windows/Temp/Astro/strings2.exe -pid {pid} -raw -nh'
        strings = str(subprocess.check_output(cmd)).replace("\\\\","/")
        strings = list(set(strings.split("\\r\\n")))

        return strings

    #Checking for recording software
    def recordingCheck(self):

        tasks = str(subprocess.check_output('tasklist')).lower()
        found = [x for x in cfg.recordingSoftwares if x in tasks]

        if found:
            for software in found:
                print(f'    {cfg.prefixWarning} {cfg.recordingSoftwares[software]} found')
        else:
            print(f'    {cfg.prefix} Nothing found')

    #Checks modification/run times
    def modificationTimes(self):
        SID = str(subprocess.check_output(f'wmic useraccount where name="{self.winUsername}" get sid')).split('\\r\\r\\n')[1]
        recycle_bin_path = self.drive_letter+"/$Recycle.Bin/"+SID

        #Recycle Bin Path
        modTime = os.path.getmtime(recycle_bin_path)
        modTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modTime))
        print(f'    Recycle Bin: {modTime}')

        #Explorer Start Time
        pid = self.getPID('explorer.exe')
        startTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.Process(pid).create_time()))
        print(f'    Explorer: {startTime}')

        #Javaw Start Time
        startTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.Process(self.javawPid).create_time()))
        print(f'    Minecraft: {startTime}')


    #In Instance Checks
    def inInstance(self):
        javawStrings = self.dump(self.javawPid)
        found = [f'{cfg.javawStrings[x]} found ({x})' for x in javawStrings if x in cfg.javawStrings]

        if found:
            for hack in found:
                print(f'    {cfg.prefixWarning} {hack}')
        else:
            print(f'    {cfg.prefix} Clean')

    #Out of instance checks
    def outOfInstance(self):
        dpsPid = self.getPID('DPS', service=True)
        strings = self.dump(dpsPid)
        strings = ['.exe!'+x.split('!')[3] for x in strings if '.exe!' in x and x.startswith('!!')]

        found = [x for x in cfg.dpsStrings if x in strings]

        if found:
            for string in found:
                print(f'    {cfg.prefixWarning} {cfg.dpsStrings[string]} ({string})')
        else:
            print(f'    {cfg.prefix} Clean')



    #Checks for JNativeHook based autoclicker
    def jnativehook(self):
        path = f'{self.user_path}/AppData/Local/Temp'

        found = [x for x in listdir(path) if isfile(f'{path}/{x}') if 'JNativeHook' in x and x.endswith('.dll')]

        if found:
            print(f'    {cfg.prefixWarning} JNativeHook autoclicker found ({found[0]})')
        else:
            print(f'    {cfg.prefix} Nothing Found')

    #Gets recently executed + deleted files
    def executedDeleted(self):
        pcasvcPid = self.getPID('PcaSvc', service=True)
        explorerPid = self.getPID('explorer.exe')
        pcasvcStrings = self.dump(pcasvcPid)
        explorerStrings = self.dump(explorerPid)

        deleted = {}

        for string in pcasvcStrings:
            string = string.lower()
            if string.startswith(self.drive_letter.lower()) and string.endswith('.exe'):
                if not os.path.isfile(string):
                    if string in explorerStrings:
                        filename = string.split('/')[-1]
                        deleted[string] = {'filename':filename, 'method':'01'}


        #Check 02 (Explorer PcaClient)
        if explorerStrings:
            for string in explorerStrings:
                string = string.lower()
                if 'trace' and 'pcaclient' in string:
                    path = [x for x in string.split(',') if '.exe' in x][0]
                    if not os.path.isfile(path):
                        filename = path.split('/')[-1]
                        deleted[path] = {'filename':filename, 'method':'02'}


        if deleted:
            print(f'    {cfg.prefixWarning} Recently executed + deleted files found:')
            for path in deleted:
                print(f'        {deleted[path]["filename"]} - {path} ({deleted[path]["method"]})')
        else:
            print(f'    {cfg.prefix} Nothing Found')





print(f'{cfg.prefix} Starting Scan with ID: {cfg.scanID}\n')
sshare = Screenshare()
sshare.mcProcess()
sshare.dependencies()

print(f'{cfg.prefix} Checking for recording software')
sshare.recordingCheck()

print(f'{cfg.prefix} Checking modification dates')
sshare.modificationTimes()

print(f'{cfg.prefix} Running in instance checks')
sshare.inInstance()

print(f'{cfg.prefix} Running out of instance checks')
sshare.outOfInstance()

print(f'{cfg.prefix} Checking for JNativeHooks')
sshare.jnativehook()

print(f'{cfg.prefix} Getting recently executed + deleted files')
sshare.executedDeleted()


input('\nScan finished\nPress enter to exit..')

temp = f'{sshare.drive_letter}/Windows/Temp/Astro'
if os.path.exists(temp):
    shutil.rmtree(temp)

















#
