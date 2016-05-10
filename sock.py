import socket


print 'AAA'

host='169.254.0.2'
port=44965
sk=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sk.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sk.bind((host,port))
sk.listen(1)

print 'accept...'
cl=sk.accept()
print 'accept done'

msg = cl.recv(100)

print 'Recv:%s' % (msg)
