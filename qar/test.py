import os
from airbus import A320

#a = A320("E:/airbus_.inf", "E:/airbus_.tmp", 768, 192, progress_bar=None)

#print(range(0,256204784,8192))
'''
f = file(r"\\.\L:", "rb+")
source = open("E:/a.par", "rb")
#f.seek(10000, 0)
while True:
    by = source.read(1)
    if not by:
        break
    else:
        f.write(by)'''
'''
f = file(r"\\.\L:", "rb")
f.seek(1, 0)


for each in f.read(10):
    print(ord(each))'''
print([0]*48)