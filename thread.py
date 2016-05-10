#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     18/02/2014
# Copyright:   (c) makihara 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import threading
import time

def DoSomething():
    for i in range(10):
        print "[%s]%d\n" % (threading.currentThread().getName(),i)
        time.sleep(1)


def main():
    pass
    t1 = threading.Thread(target=DoSomething,name="thr1")
    t2 = threading.Thread(target=DoSomething,name="thr2")
    t3 = threading.Thread(target=DoSomething,name="thr3")
    t1.setDaemon(True)
    t2.setDaemon(True)
    t3.setDaemon(True)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()
#    main_thread = threading.currentThread()
#    while True:
#        tlist = threading.enumerate()
#        if len(tlist) &lt; 2: break
#        for t in tlist:
#            if t is main_thread: continue
#            print t
#        time.sleep(1)

if __name__ == '__main__':
    main()
