import time

transformed_path = r"\\.\L:"
dat = file(transformed_path, "rb")
start = time.clock()
dat.read(32768)
copy = dat.read(10)
for each in copy:
    print(ord(each))
end = time.clock()

print(end-start)
