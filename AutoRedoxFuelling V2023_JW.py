import os
import time
from jwslib import read_file
from matplotlib import pyplot as plt
import numpy as np
import serial


dn = "C:\\DATA\\Juntian\\20240127_measure"
fnlog = "C:\\DATA\\Juntian\\20240127_log\\jw_20240127_log.csv"
units = ["mL/min","mL/hr","uL/min","uL/hr"]

def read_jws(fn):
  ndata, header, data = read_file(fn)
  x = np.arange(header.x_for_first_point,
                header.x_for_last_point+header.x_increment,
                header.x_increment)
  y = np.array(data[0])
  return x, y

def fusion_cmd(sp,cmd):
  sp.write("{cmd}\r".format(cmd=cmd).encode("ascii"))
  answer = ""
  while True:
    c = sp.read(1).decode("utf-8")
    if c in ('>',''):
      break
    answer = answer + c

  return [v.strip() for v in answer.split("\n")]

def fusion_getpar(sp):
  answer = fusion_cmd(sp,"view parameter")
  par = {}
  for l in answer :
    if '=' in l:
      k,v = l.strip().split('=')
      k = k.strip()
      v = v.strip()
      par[k] = units[int(v)] if k == "unit" else v
  return par

spreduc = serial.Serial("COM4",
                        baudrate=9600,
                        bytesize=8,
                        parity="N",
                        stopbits=1,
                        xonxoff=0,
                        rtscts=0,
                        timeout=1)

spoxid = serial.Serial("COM3",
                        baudrate=9600,
                        bytesize=8,
                        parity="N",
                        stopbits=1,
                        xonxoff=0,
                        rtscts=0,
                        timeout=1)

print(fusion_getpar(spreduc))
print(fusion_getpar(spoxid))


print(fusion_cmd(spreduc, "set units 3"))
print(fusion_cmd(spreduc, "set rate 5"))
print(fusion_cmd(spreduc, "set diameter 4.61"))
print(fusion_cmd(spreduc, "set volume 1000"))

print(fusion_cmd(spoxid, "set units 3"))
print(fusion_cmd(spoxid, "set rate 5"))
print(fusion_cmd(spoxid, "set diameter 4.61"))
print(fusion_cmd(spoxid, "set volume 1000"))
#print(fusion_cmd(spreduc, "set volume 0.01"))
#print(fusion_cmd(spreduc, "start"))

os.chdir(dn)
nfiles = 0
i = 0

zset = 12.089
zsetp = 12.335
zsetm = 11.841

spoxidon = False
spreducon = False


while True:
  dirlist = sorted([(os.stat(fn).st_mtime,fn) for fn in os.listdir(".")])
  if (nfiles != len(dirlist)):
    if nfiles == 0:
      nfiles = len(dirlist)
      continue
    else:
      nfiles = len(dirlist)
    fnlast = dirlist[-1][1]
    x,y = read_jws(fnlast)
    y266 = y[x==266][0]
    y332 = y[x==332][0]
    y500 = y[x==500][0]
    yt = y266 - y500
    yi = y332 - y500
    z = yt / yi
    plt.scatter(i, y266, color='blue')
    plt.scatter(i, y332, color='red')
    plt.scatter(i, z, color='green')

    reducstat = fusion_cmd(spreduc, "status")[1]
    oxidstat = fusion_cmd(spoxid, "status")[1]
    
    if (z < zsetm):
      if oxidstat == '1':
        print(fusion_cmd(spoxid, "stop"))
      if reducstat == '0':
        print(fusion_cmd(spreduc, "start"))
        
      spoxidon = False
      spreducon = True
    elif (z > zsetp):
      if reducstat == '1':        
        print(fusion_cmd(spreduc, "stop"))
      if oxidstat == '0':
        print(fusion_cmd(spoxid, "start"))
        
      spreducon = False
      spoxidon = True
    else :
      if reducstat == '0':        
        print(fusion_cmd(spreduc, "start"))
      if oxidstat == '0':
        print(fusion_cmd(spoxid, "start"))
      
      spoxidon = True
      spreducon = True
    logline = (time.time(), spreducon, spoxidon, y332, y266, y500, yi, yt, z)
    print(logline)
    f = open(fnlog, 'a')
    f.write('\t'.join(map(str, logline)))
    f.write('\n')
    f.close()
    i = i + 1
    
  plt.pause(1)

spreduc.close()
spoxid.close()
