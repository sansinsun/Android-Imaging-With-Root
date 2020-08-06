from tkinter import *
import os
import time
from datetime import datetime
import pyadb3
import hashlib
import logging
import sys
import signal
import tkinter as tk
import subprocess
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox as mbox
from ppadb.client import Client as AdbClient
from pprint import pprint
import adbutils
from multiprocessing import Process
import dill

root = tk.Tk()

class App(Frame):
    outputfolder =""
    return_code = 9
    global root
    
    def __init__(self, parent):
        self.window = parent
        self.initUI()
        self.mainMenu()
        self.outputText(self.window, 5, row = 6)
        self.checkButton()
        self.scanButton()
        self.connectButton()
        self.nextButton(DISABLED)
        self.killServerButton()
        self.rootButton()
        self.busyboxButton()
        self.choosenDir = ""
        self.startTime = datetime.now()
        
    def initUI(self):
        self.window.title("Disk Imaging Applications on Android Phone")
        self.window.resizable(False, False)
        self.window.geometry("540x400") 

    def newWindow(self):
        nw = Toplevel()
        nw.wm_title("Disk Imaging Applications on Android Phone")
        nw.geometry("520x600")
        nw.attributes('-topmost', 'false')
        self.secondMenu(nw)
        self.officerName(nw)
        self.FileName(nw)
        self.buttonFolder(nw)
        self.CheckBox(nw)
        self.outputText(nw, 2, row= 5)
        self.startdumpButton(nw)
        self.progressBarInt(nw)
        self.progressBarExt(nw)
       
    def progressBarInt(self, window):
        progrssbarint_lbl = Label(window, text="Internal : ")
        progrssbarint_lbl.grid(column=0, row=6, pady=4, padx=4, sticky="w")
        self.progressInt = ttk.Progressbar(window, orient=HORIZONTAL, length=100, mode='determinate')
        self.progressInt.grid(column=0, columnspan=2, row=7, padx=6, pady=2, sticky="ew")

    def progressBarExt(self, window):
        progrssbarExt_lbl = Label(window, text="External : ")
        progrssbarExt_lbl.grid(column=0, row=8, pady=4, padx=4, sticky="w")
        self.progressExt = ttk.Progressbar(window, orient=HORIZONTAL, length=100, mode='determinate')
        self.progressExt.grid(column=0, columnspan=2, row=9, padx=7, pady=2, sticky="ew")


    def startdumpShell(self, window):
        command = "su -c 'dd if=/dev/block/{} | busybox nc -l -p 8888'".format(self.choosenDir)
        print("Dumping process started")
        dev = adbutils.adb.device()
        dev.shell(command)
    
    def outputDumpShell(self, window):
        padb = pyadb3.ADB()
        partitionList = padb.run_shell_cmd("cat /proc/partitions | grep {}".format(self.choosenDir))
        partitionResult = 0
        
        if len(partitionList) > 0:
            partitionSplit = partitionList.split()[2]
            partitionSize = "{partitionSplit}".format(partitionSplit = partitionSplit).replace("b", "").replace("'", "")
            partitionResult = int(partitionSize)/ (1024 * 1024)


        print("{} GB".format(partitionResult))
        return partitionResult


    def startProcess(self, window):
        self.startTime = datetime.now()
        self.sizeoutputInt = 0
        self.sizeoutputExt = 0

        if (self.CheckVar1.get() == 1 and self.CheckVar2.get() == 1):
            self.outText.delete("1.0", END)
            self.outText.insert(END, "Storage \t\t\t : Internal" + "\n")
            self.outText.insert(END, "Source Directory \t\t\t : /dev/block/mmcblk0" + "\n")
            self.outText.insert(END, "Storage \t\t\t : External" + "\n")
            self.outText.insert(END,"Source Directory \t\t\t : /dev/block/mmcblk1"+"\n")
            self.outText.insert(END,"----------------------------------------------------" +"\n"+"\n")
            self.choosenDir = "mmcblk0"
            self.sizeoutputInt = self.outputDumpShell(window)            

            p = Process(target= lambda: self.startdumpShell(window))
            q = Process(target= lambda: self.startOuputDumpInt(window))
            
            if self.return_code !=0:
                p.start()
                time.sleep(6)
                q.start()
            else:
                p.terminate()
                time.sleep(2)
                q.terminate()
            
            time.sleep(3)

            
            alldirect = "{}/_Int{}.dd".format(self.outputfolder, self.txtFileName.get())
            currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            self.progressInt['maximum'] = self.sizeoutputInt

            state = True
            while state:
                state = self.progressIntBar(window, currentOutputSize, self.sizeoutputInt)
                root.update_idletasks()
                currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            
            self.hashmd5(window)
            self.createLogInt()


            p = Process(target= lambda: self.startdumpShell(window))
            q = Process(target= lambda: self.startOuputDumpExt(window))
            self.choosenDir = "mmcblk1"
            self.sizeoutputExt = self.outputDumpShell(window)

            if self.return_code !=0:
                p.start()
                time.sleep(6)
                q.start()
            else:
                p.terminate()
                time.sleep(2)
                q.terminate()
            
            time.sleep(3)
            
            alldirect = "{}/_Ext{}.dd".format(self.outputfolder, self.txtFileName.get())
            currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            self.progressExt['maximum'] = self.sizeoutputExt

            state = True
            while state:
                state = self.progressExtBar(window, currentOutputSize, self.sizeoutputExt)
                root.update_idletasks()
                currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            
            self.hashmd5(window)
            self.createLogExt()
            self.FinishedTextInt(window)
            self.FinishedTextExt(window)
            mbox.showinfo("Finished", "Aqusition Finished")
            self.endTime = datetime.now()
            


        elif self.CheckVar1.get() == 1:
            self.outText.delete("1.0", END)
            self.outText.insert(END, "Storage \t\t\t : Internal" + "\n")
            self.outText.insert(END,"Source Directory \t\t\t : /dev/block/mmcblk0"+"\n")
            self.outText.insert(END,"----------------------------------------------------" +"\n"+"\n")
            p = Process(target= lambda: self.startdumpShell(window))
            q = Process(target= lambda: self.startOuputDumpInt(window))
            self.choosenDir = "mmcblk0"
            self.sizeoutputInt = self.outputDumpShell(window)

            if self.return_code !=0:
                p.start()
                time.sleep(6)
                q.start()
            else:
                p.terminate()
                time.sleep(2)
                q.terminate()
            
            time.sleep(3)

            alldirect = "{}/_Int{}.dd".format(self.outputfolder, self.txtFileName.get())
            currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            self.progressInt['maximum'] = self.sizeoutputInt

            state = True
            while state:
                state = self.progressIntBar(window, currentOutputSize, self.sizeoutputInt)
                root.update_idletasks()
                currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            
            self.hashmd5(window)
            self.createLogInt()
            self.FinishedTextInt(window)

            mbox.showinfo("Finished", "Aqusition Finished")

        
        elif self.CheckVar2.get() == 1:
            self.outText.delete("1.0", END)
            self.outText.insert(END, "Storage \t\t\t : External" + "\n")
            self.outText.insert(END,"Source Directory \t\t\t : /dev/block/mmcblk1"+"\n")
            self.outText.insert(END,"----------------------------------------------------" +"\n"+"\n")   
            self.choosenDir = "mmcblk1"
            p = Process(target= lambda: self.startdumpShell(window))
            q = Process(target= lambda: self.startOuputDumpExt(window))
            self.outputDumpShell(window)
            self.sizeoutputExt = self.outputDumpShell(window)

            if self.return_code !=0:
                p.start()
                time.sleep(6)
                q.start()
            else:
                p.terminate()
                time.sleep(2)
                q.terminate()
            
            time.sleep(3)

            alldirect = "{}/_Ext{}.dd".format(self.outputfolder, self.txtFileName.get())
            currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)
            self.progressExt['maximum'] = self.sizeoutputExt

            state = True
            while state:
                state = self.progressExtBar(window, currentOutputSize, self.sizeoutputExt)
                root.update_idletasks()
                currentOutputSize = os.stat(alldirect).st_size / (1024 * 1024 * 1024)

            self.hashmd5(window)
            self.createLogExt()
            self.FinishedTextExt(window)

            mbox.showinfo("Finished", "Aqusition Finished")

    
    def progressIntBar(self, window, currentOutputSize, outputSize):
        if currentOutputSize < outputSize:
            self.progressInt['value'] = currentOutputSize
            print("Progress : {} / {}".format(currentOutputSize, outputSize))
            return True

        return False
    
    def progressExtBar(self, window, currentOutputSize, outputSize):
        if currentOutputSize < outputSize:
            self.progressExt['value'] = currentOutputSize
            print("Progress : {} / {}".format(currentOutputSize, outputSize))
            return True

        return False

    def hashmd5(self, window):
        time.sleep(5)
        fDirect = self.outputfolder
        nDirect = "/_Ext" + self.txtFileName.get() +".dd"
        alldirect = fDirect + nDirect
        block_size = 2 ** 20
        md5a = hashlib.md5()
        
        if( os.path.exists(alldirect) ) :
            with open(alldirect, 'rb') as fileCloning:
                while True:
                    readCloning = fileCloning.read(block_size)
                    if not readCloning:
                        break
                    md5a.update(readCloning)

        self.hasilCloning = md5a.hexdigest()

        adbHash = pyadb3.ADB()
        coHash = adbHash.run_shell_cmd("su -c md5sum /dev/block/{}".format(self.choosenDir))
        splitHash = "{coHash}".format(coHash=coHash)
        self.hasilHash = splitHash[2:34]
        self.isHashMatched = ""
        
        if self.hasilHash == self.hasilCloning:
            self.isHashMatched = "MD5 Hash Matched"
        else:
            self.isHashMatched = "MD5 Hash Not Matched"

    def startOuputDumpInt(self, window):
        content = self.txtFileName.get()
        print("capturing dump and save as "+content)
        process = subprocess.run(['cd '+self.outputfolder + '&&' + 'nc -v 127.0.0.1 8888 >'+ "_Int" + str(content) + ".dd"], shell=True)

    def startOuputDumpExt(self, window):
        content = self.txtFileName.get()
        print("capturing dump and save as "+content)
        process = subprocess.run(['cd '+self.outputfolder + '&&' + 'nc -v 127.0.0.1 8888 >'+"_Ext"+ str(content) + ".dd"], shell=True)

    def secondMenu(self,window):
        menubar = Menu(window)
        window.config(menu=menubar)
        fileMenu = Menu(menubar)
        fileMenu.add_checkbutton(label="Exit", command=self.exitProgram)
        menubar.add_cascade(label="File", menu = fileMenu)
        aboutMenu = Menu(menubar)
        aboutMenu.add_checkbutton(label="About")
        menubar.add_cascade(label="About", menu =aboutMenu, command=self.clk_about)

    def mainMenu(self):
        menubar = Menu(self.window)
        self.window.config(menu=menubar)
        fileMenu = Menu(menubar)
        fileMenu.add_checkbutton(label="Exit", command=self.exitProgram)
        fileMenu.add_checkbutton(label="Scan", command = self.clk_scn)
        menubar.add_cascade(label="File", menu = fileMenu)
        aboutMenu = Menu(menubar)
        aboutMenu.add_checkbutton(label="About", command=self.clk_about)
        menubar.add_cascade(label="About", menu =aboutMenu)

    # List of widgets in Main Window
    def scanButton(self):
        scn_button = Button(self.window, text = "Scan", command = self.clk_scn, width=8)
        scn_button.grid(column=0 , row=3, padx=4, pady=6, sticky="w")
    
    def rootButton(self):
        rt_button = Button(self.window, text = "Install Root", command = self.clk_root, width=8)
        rt_button.grid(column=0 , row=4, padx=4, pady=6, sticky="w")

    def busyboxButton(self):
        bsybx_button = Button(self.window, text = "Busybox", command = self.clk_BusyBox, width=8)
        bsybx_button.grid(column=1 , row=4, padx=4, pady=6, sticky="w")
    
    def checkButton(self):
        chk_button = Button(self.window, text= "Check", command = self.clk_check, width=8)
        chk_button.grid(column=1, row=3, padx=4, pady=6, sticky="w")

    def connectButton(self):
        cnc_button = Button(self.window, text = "Connect", command = self.clk_connect, width=8)
        cnc_button.grid(column=2, row=3, padx=4, pady=6, sticky="w")

    def nextButton(self,state):
        next_button = Button(self.window, text="Next", state = state, command=self.newWindow, width=8)
        next_button.grid(column=3 , row=3, padx=4, pady=6, sticky="w")

    def killServerButton(self):
        kill_svr_button = Button(self.window, text="Kill Adb Server" , command=self.clk_kill_svr, width=12)
        kill_svr_button.grid(column=4, row=3, padx=4, pady=6, sticky="e")
    
  
    
    # End list of widgets Main Window

    # List of Widgets Second Window
    def selectOutput(self, window):
        folder_selected = filedialog.askdirectory(title="Select output Folder")
        self.outText.insert(END, "Output folder is "+folder_selected +"\n")
        self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")

        self.outputfolder = folder_selected
        
    
    def buttonFolder(self,window):
        lbl_open = Label(window, text="Select Output Directory")
        lbl_open.grid(column=0 , row=0, pady=4, padx=4, sticky="w")
        open_btn = Button(window, width=15, text ="Select Folder Here", command = lambda: self.selectOutput(window))
        open_btn.grid(column=1, row=0, pady=4, padx=4, sticky="w")

    def FileName(self, window):
        Name = tk.Label(window, text="File Name :")
        Name.grid(column=0, row=1, pady=4, padx=4, sticky="w")
        self.txtFileName = tk.Entry(window,textvariable="", width=40)
        self.txtFileName.grid(column=1 , row=1, pady=4, padx=4, sticky="w")
    
    def CheckBox(self, window):
        self.CheckVar1 = IntVar()
        self.CheckVar2 = IntVar()
        l_box = tk.Label(window, text="Storage :")
        l_box.grid(column=0, row=2, padx=4, pady=4, sticky="w")
        self.C1 = Checkbutton(window, text = "Internal", variable = self.CheckVar1)
        self.C2 = Checkbutton(window, text = "Eksternal", variable = self.CheckVar2)
        self.C1.grid(column=1, columnspan=2, row=2, pady=4, sticky="w")
        self.C2.grid(column=1, columnspan=2, row=2, padx=110, pady=4, sticky="w")
    

    def officerName(self, window):
        lbl_file = Label(window, text="Officer Name : ")
        lbl_file.grid(column=0, row=3, padx=4, pady=4, sticky="w")
        self.txtOfficerName = tk.Entry(window, textvariable="", width=40)
        self.txtOfficerName.grid(column=1, row=3, padx=4, pady=4, sticky="w")

    def startdumpButton(self, window):
        self.srtr_btn = Button(window, text = "Start Shell ", width=34, command = lambda: self.butttonclick(window))
        self.srtr_btn.grid(column=1, row=4, padx=3, pady=4, sticky="w")
        
        
        
    def butttonclick(self, window):
        if self.txtOfficerName.get() == "":
            mbox.showerror("form validation","Officer Name is required")
        elif self.txtFileName.get() == "":
            mbox.showerror("form validation","Filename is required")
        elif self.CheckVar1.get() == 0 and self.CheckVar2.get() == 0:
            mbox.showerror("form validation","Checkbox is required")
        elif self.outputfolder == "":
            mbox.showerror("form validation","Output Folder is required")
        elif os.path.exists("{}/_Int{}.dd".format(self.outputfolder, self.txtFileName.get())):
            mbox.showerror("form validation","Filename is Exist")
        elif os.path.exists("{}/_Ext{}.dd".format(self.outputfolder, self.txtFileName.get())):
            mbox.showerror("form validation","Filename is Exist")
        else:
           command = self.startProcess(window)
   
    # End list of widgets Second Window

    def outputText(self, window, span = 0, row = 0):
        self.outText = scrolledtext.ScrolledText(window, width = 5, height = 17)
        self.outText.grid(column=0, columnspan=span, row=row, padx=7, pady=10, sticky="we")
        self.outText.insert(END,"output here"+"\n")

    def exitProgram(self):
        msgbox = mbox.askquestion("Exit Application",'Are you sure you want to exit the application ?')
        if msgbox == 'yes':
            self.window.quit()
        else:
            mbox.showinfo('return', 'you will now return to application screen')

    def dumpButton(self, window):
        dmp_btn = Button(window, text = "Start Imaging ", command = lambda : self.testDump(window))
        dmp_btn.grid(column = 3, row = 3)

    def clk_kill_svr(self):
        var = subprocess.getoutput("adb kill-server")
        mbox.showinfo("Info", "Adb Server Has Been Killed")
        self.outText.insert(END, var)
        self.outText.insert(END, "Adb Server Has Been Killed" +"\n")
        self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")


    def clk_connect(self):
        var2 = subprocess.getoutput("adb get-state")
        var4 = subprocess.getoutput("adb shell su -c ls /data")
        var5 = subprocess.getoutput("adb shell pm list packages -u stericson.busybox ")
        output = "/system/bin/sh: su: not found"
        output1 = "error: no devices/emulators found"
        output2 = "package:stericson.busybox"
        if var2 == 'device':
            if var4 == output:
                mbox.showerror("Validation", "Devices has not installed Root, Please Install")
            elif var5 == "":
                mbox.showerror("Validation","Devices has not installed BusyBox, Please Install")
            elif var5 == output2:
                if var4 == var4:
                    var = subprocess.getoutput("adb forward tcp:8888 tcp:8888")
                    text = "{var}".format(var=var)
                    if text == "":
                        
                        self.outText.insert(END, "Devices Has Root"+"\n")
                        self.outText.insert(END, "Device Connected" + "\n")
                        self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")

                        self.nextButton(NORMAL)
        elif var2 == output1:
            mbox.showerror("Validation","No Device Detected, Or Device Not Conected")

    def clk_scn(self):
        subprocess.getoutput('adb start-server')
        serial = subprocess.getoutput('adb devices -l')
        forSerial = subprocess.getoutput('adb get-serialno')
        forStatus = subprocess.getoutput('adb get-state')
        serialNo = forSerial
        status = forStatus
        model = serial[86:95]
        type = serial[57:120]

        if forSerial == 'unknown':
            self.outText.delete("1.0", END)
            self.outText.insert(END, "No device found"+"\n")
            self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")
            mbox.showerror("Caution", "No device found")

        else:
            self.outText.delete("1.0", END)
            self.outText.insert(END, "Device is Ready"+"\n")
            self.outText.insert(END, "Serial No : "+serialNo+"\n")
            self.outText.insert(END, "Status : " + status+"\n")
            self.outText.insert(END, "Type : " + str(type)+"\n")
            self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")

    def clk_about(self):
        mbox.showinfo("About", "This Application is built with the Python programing language \n \nthis Application is to acquire Android storage with Root based on Linux platform \n \nThe Application can be run if the Android phone in Root mode designed to maintain the integrity of a files that will be generated \n \nCopyright (C) 2020 - Insan Fadhilah")
    
    def clk_check(self):
        var = subprocess.getoutput('adb forward --list')
        text = "{var}".format(var=var)
        device = text[0:16]
        port = text[16:50]

        if text  == '':
            self.outText.insert(END, "No Connected Devices"+"\n")
            self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")
            mbox.showerror("Caution", "No device found")


        else:
            self.outText.insert(END, "Connected Device to : " + str(device) +"\n")
            self.outText.insert(END, "Port : " + str(port)+"\n")
            self.outText.insert(END,"-------------------------------------------------------" +"\n"+"\n")

    

        
    def clk_root(self):
        subprocess.getoutput('adb install KingoRoot.apk')
    
    def clk_BusyBox(self):
        subprocess.getoutput('adb install BusyBox.apk')
    
    
    def testDump(self, window):
        client = AdbClient(host="127.0.0.1", port=5037)
        dev = client.devices()
        dev2 = client.device("YT910815C7")
        self.outText.delete('1.0', END)
        self.outText.insert(END, dev2.shell("echo test2"))

    def dumpInt(self):
        choosenDir = "/dev/block/mmcblk0"
        print("Dumping from internal at {}".format(choosenDir))
     
        return choosenDir

    def dumpExt(self):
        choosenDir = "/dev/block/mmcblk1"
        print("Dumping from external at {}".format(choosenDir))

        return choosenDir
    

    # Function for create examining information
    def createLogInt(self):
        log = open("{}/_Int{}.txt".format(self.outputfolder, self.txtFileName.get()), "w+")
        self.endTime = datetime.now()
        logTextInt = """Examiner\t\t: {}
------------- The results of aquisition process -------------
Aquisition Start\t: {}
Aquisition End\t\t: {}
File Name\t\t: _Int{}
Directory\t\t: {}
-------------------------------------------------------------
Storage Type
Internal\t\t: {}
Size\t\t\t: {}
Eksternal\t\t: {}
Size\t\t\t: {}
-------------------------------------------------------------
Generated MD5 HASH\t: {}
-------------------------------------------------------------

        """.format(
            self.txtOfficerName.get(),
            self.startTime.strftime("%Y-%m-%d %H:%M:%S"),
            self.endTime.strftime("%Y-%m-%d %H:%M:%S"),
            self.txtFileName.get(),
            self.outputfolder,
            ("NO", "YES") [self.CheckVar1.get() == 1],
            self.sizeoutputInt,
            ("NO", "YES") [self.CheckVar2.get() == 1],
            self.sizeoutputExt,
            self.hasilCloning,
        )
        log.write(logTextInt)
        log.close()

    def createLogExt(self):
        log = open("{}/_Ext{}.txt".format(self.outputfolder, self.txtFileName.get()), "w+")
        self.endTime = datetime.now()
        logTextExt = """Examiner\t\t: {}
------------- The results of aquisition process -------------
Aquisition Start\t: {}
Aquisition End\t\t: {}
File Name\t\t: _Ext{}
Directory\t\t: {}
-------------------------------------------------------------
Storage Type
Internal\t\t: {}
Size\t\t\t: {}
Eksternal\t\t: {}
Size\t\t\t: {}
-------------------------------------------------------------
Source MD5 Hash\t\t: {}
Generated MD5 HASH\t: {}
-------------------------------------------------------------
{}
        """.format(
            self.txtOfficerName.get(),
            self.startTime.strftime("%Y-%m-%d %H:%M:%S"),
            self.endTime.strftime("%Y-%m-%d %H:%M:%S"),
            self.txtFileName.get(),
            self.outputfolder,
            ("NO", "YES") [self.CheckVar1.get() == 1],
            self.sizeoutputInt,
            ("NO", "YES") [self.CheckVar2.get() == 1],
            self.sizeoutputExt,
            self.hasilHash,
            self.hasilCloning,
            self.isHashMatched
        )
        log.write(logTextExt)
        log.close()
    
    def FinishedTextInt (self, window):
        self.endTime = datetime.now()
        self.startTime = datetime.now()
        self.sizeoutputInt = 0
        self.outText.insert(END,"------------------------------------------------------- \n")
        self.outText.insert(END, "Examiner\t\t: "+self.txtOfficerName.get()+"\n")
        self.outText.insert(END, "----------- The results of aquisition process ----------- \n")
        self.outText.insert(END," Aquisition Start\t: " +self.startTime.strftime("%Y-%m-%d %H:%M:%S")+"\n")
        self.outText.insert(END,"Aquisition End\t\t: "+self.endTime.strftime("%Y-%m-%d %H:%M:%S")+"\n")
        self.outText.insert(END,"File Name\t: _Int"+self.txtFileName.get()+"\n")
        self.outText.insert(END,"Directory\t\t: " +self.outputfolder +"\n")
        self.outText.insert(END,"------------------------------------------------------- \n")
        self.outText.insert(END,"Storage Type \n")
        self.outText.insert(END,"Internal\t\t: " +"YES"+"\n")
        self.outText.insert(END,"Source Directory\t: /dev/block/mmcblk0 \n")
        self.outText.insert(END,"-------------------------------------------------------\n")
        self.outText.insert(END,"Generated MD5 HASH\t: "+self.hasilCloning+"\n")
        self.outText.insert(END,"------------------------------------------------------- \n")

    def FinishedTextExt (self, window):
        self.endTime = datetime.now()
        self.outText.insert(END,"---------------------------------------------------------- \n")
        self.outText.insert(END, "Examiner\t\t: "+self.txtOfficerName.get()+"\n")
        self.outText.insert(END, "------- The results of aquisition process ---------- \n")
        self.outText.insert(END," Aquisition Start\t: " +self.startTime.strftime("%Y-%m-%d %H:%M:%S")+"\n")
        self.outText.insert(END,"Aquisition End\t\t: "+self.endTime.strftime("%Y-%m-%d %H:%M:%S")+"\n")
        self.outText.insert(END,"File Name\t\t: _Int"+self.txtFileName.get()+"\n")
        self.outText.insert(END,"Directory\t\t: " +self.outputfolder +"\n")
        self.outText.insert(END,"------------------------------------------------------- \n")
        self.outText.insert(END,"Storage Type \n")
        self.outText.insert(END,"Eksternal\t\t:"+ "YES"+"\n")
        self.outText.insert(END,"Source Directory \t\t: /dev/block/mmcblk1 \n")
        self.outText.insert(END,"------------------------------------------------------- \n")
        self.outText.insert(END,"Generated MD5 HASH\t: "+self.hasilCloning+"\n")
        self.outText.insert(END,"------------------------------------------------------- \n")




    

if __name__ =='__main__':
    app = App(root)
    var_chk = IntVar()
    root.mainloop()