#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      makihara
#
# Created:     21/12/2015
# Copyright:   (c) makihara 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
data1=[
[(0,0),(1,0),(2,0)],
[(0,1),(1,1),(2,1)],
[(0,3),(1,3),(2,3)],
[(0,4),(1,4),(2,4)]
]

data2=[
[(0,0),(1,0),(2,0)],
[(0,1),(1,1),(2,1)],
[(0,3),(1,3),(2,3)],
[(0,4),(1,4),(2,4)]
]

def main():
    pass
    yL = len(data1)
    xL = len(data1[0])

    sub = [[(data1[b][a][0]+data2[b][a][0], data1[b][a][1]+data2[b][a][1]) for a in range(xL)] for b in range(yL)]
    print sub

    mm = map(lambda x,y:(x,y),data1,data2)
    print mm

if __name__ == '__main__':
    main()
