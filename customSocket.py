import socket

class pyratSocket:

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
 
    def ratConnect(self, host, port):
        self.sock.connect((host, port))
 
    def ratSend(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:].encode())
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
 
    def ratReceive(self,msglen,pattern=''):

        msg = ''
        while len(msg) < msglen and (pattern == '' or pattern not in msg):
            chunk = self.sock.recv(msglen-len(msg))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            msg = msg + chunk.decode()
        return msg
    
    def ratDisconnect(self):
        self.sock.close()