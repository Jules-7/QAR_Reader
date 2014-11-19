#-*-coding: utf-8-*-
import time
import datetime
'''
transformed_path = r"\\.\L:"
dat = file(transformed_path, "rb")
start = time.clock()
dat.read(32768)
copy = dat.read(10)
for each in copy:
    print(ord(each))
end = time.clock()

print(end-start)'''
#date = datetime.datetime
#print(datetime.datetime.now())
#print(datetime.date.today())
#print(time.clock())
#print(time.time())
'''
import os, sys, stat

# Assuming /tmp/foo.txt exists and has read/write permissions.
path = r"H:\\CLU_0002.DAT"
ret = os.access(path, os.F_OK)
print "F_OK - return value %s"% ret

ret = os.access(path, os.R_OK)
print "R_OK - return value %s"% ret

ret = os.access(path, os.W_OK)
print "W_OK - return value %s"% ret

os.chmod(path, stat.S_IWRITE)

ret = os.access(path, os.W_OK)
print "W_OK - return value %s"% ret

ret = os.access(path, os.X_OK)
print "X_OK - return value %s"% ret'''
'''
from tester import TesterU32

t = TesterU32(tmp_file_name=r"E:/An32_Tester32/CLU_0003.DAT",
              target_file_name="_result.dat",
              progress_bar = None,
              path_to_save=r"E:/An32_Tester32/",
              flag="an32")'''
