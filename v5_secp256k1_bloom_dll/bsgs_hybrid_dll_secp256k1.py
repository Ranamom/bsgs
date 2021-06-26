# -*- coding: utf-8 -*-
"""
Usage :
 > python bsgs_hybrid_dll_secp256k1.py -pfile test_pubkeys.txt -b FULLbpfile.bin -bl 2B_bloom.bin -n 80000000000000 -keyspace 800000000000000000000000000000:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
 > python bsgs_hybrid_dll_secp256k1.py -pfile Pub50.txt -b FULLbpfile.bin -bl 2B_bloom.bin -n 8000000000 -rand1

@author: iceland
@credits: Alberto, Keyhunt gmp library
"""
import time
import random
import bit
import os
import ctypes
import math
import sys
import platform
import argparse


parser = argparse.ArgumentParser(description='This tool use bsgs algo for sequentially searching all pubkeys (together) in the given range', 
                                 epilog='Enjoy the program! :)    Tips BTC: bc1q39meky2mn5qjq704zz0nnkl0v7kj4uz6r529at \
                                 \nThanks a lot to AlbertoBSD Tips BTC: 1ABSD1rMTmNZHJrJP8AJhDNG1XbQjWcRz7')
parser.version = '26062021'
parser.add_argument("-pfile", "--pfile", help = "Public Key in hex format (compressed or uncompressed) line by line", action="store")
parser.add_argument("-xfile", "--xfile", help = "xpoint in hex format line by line. Both 02 & 03 will be considered automatically", action="store")
parser.add_argument("-b", "--bpfile", help = "Baby Point file. created using create_bPfile_mcpu2.py", required=True)
parser.add_argument("-bl", "--bloomfile", help = "Bloom filter file. created using bPfile_2_bloom_dll_batch.py", required=True)
parser.add_argument("-n", help = "Total sequential search in 1 loop. default=8000000000", action='store')
parser.add_argument("-keyspace", help = "Keyspace Range ( hex ) to search from min:max. default=1:order of curve", action='store')
parser.add_argument("-rand", help = "Start from a random value in the given range from min:max and search n values then again take a new random", action="store_true")
parser.add_argument("-rand1", help = "First Start from a random value, then go fully sequential, in the given range from min:max", action="store_true")

if len(sys.argv)==1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()


seq = int(args.n) if args.n else 8000000000  # Approx (250 Trillion / number of pubkeys)
ss = args.keyspace if args.keyspace else '1:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140'
flag_random = True if args.rand else False
flag_random1 = True if args.rand1 else False
bs_file = args.bpfile       # 'FULLbpfile.bin'
bloom_file = args.bloomfile # 'Big_dll_bloom.bin'
public_key_file = args.pfile if args.pfile else ''
xpoint_file = args.xfile if args.xfile else ''
if flag_random1: flag_random = True
if public_key_file == '' and xpoint_file == '': 
    print('One of the required option missing -pfile or -xfile'); sys.exit(1)
###############################################################################
a, b = ss.split(':')
a = int(a, 16)
b = int(b, 16)


if os.path.isfile(bloom_file) == False:
    print('File {} not found'.format(bloom_file))
    print('create it from : bPfile_2_bloom_dll_batch.py')
    sys.exit()
if os.path.isfile(bs_file) == False:
    print('File {} not found'.format(bs_file))
    print('Specify the input file used to create the bloom filter or create it from : create_bPfile_mcpu2.py. Even little smaller file is OK.')
    sys.exit()
if os.path.isfile(public_key_file) == False and public_key_file != '':
    print('File {} not found'.format(public_key_file))
    print('1 pubkey per line in hex format,  in the file (compressed or uncompressed)')
    sys.exit()
if os.path.isfile(xpoint_file) == False and xpoint_file != '':
    print('File {} not found'.format(xpoint_file))
    print('1 xpoint per line in hex format,  in the file.')
    sys.exit()
# ======== 1st Part : File ===============

# m = 40000000     # m = math.floor(math.sqrt(k2-k1))
m_bb = int((os.stat(bs_file).st_size)/32)      # each xpoint is 32 bytes in the file
lastitem = 0

if platform.system().lower().startswith('win'):
    pathdll = os.path.realpath('bloom_batch.dll')
    mylib = ctypes.CDLL(pathdll)
    
elif platform.system().lower().startswith('lin'):
    pathdll = os.path.realpath('bloom_batch.so')
    mylib = ctypes.CDLL(pathdll)
    
else:
    print('[-] Unsupported Platform currently for ctypes dll method. Only [Windows and Linux] is working')
    sys.exit()


bloom_check_add = mylib.bloom_check_add
bloom_check_add.restype = ctypes.c_int
bloom_check_add.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_ulonglong, ctypes.c_ubyte, ctypes.c_char_p]

###############################################################################

if platform.system().lower().startswith('win'):
    pathdll = os.path.realpath('ice_secp256k1.dll')
    ice = ctypes.CDLL(pathdll)
    
elif platform.system().lower().startswith('lin'):
    pathdll = os.path.realpath('ice_secp256k1.so')
    ice = ctypes.CDLL(pathdll)
    
else:
    print('[-] Unsupported Platform currently for ctypes dll method. Only [Windows and Linux] is working')
    sys.exit()


ice.scalar_multiplication.argtypes = [ctypes.c_char_p, ctypes.c_char_p]            # pvk,ret
ice.point_increment.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p] # x,y,ret
ice.point_negation.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]  # x,y,ret
ice.point_doubling.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]  # x,y,ret
ice.create_baby_table.argtypes = [ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_char_p] # start,end,ret
ice.point_addition.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p] # x1,y1,x2,y2,ret
ice.point_subtraction.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p] # x1,y1,x2,y2,ret
ice.point_loop_subtraction.argtypes = [ctypes.c_ulonglong, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p] # k,x1,y1,x2,y2,ret

ice.init_secp256_lib()


def scalar_multiplication(kk):
    res = (b'\x00') * 65
    pass_int_value = hex(kk)[2:].encode('utf8')
    ice.scalar_multiplication(pass_int_value, res)
    return res

def point_increment(pubkey_bytes):
    x1 = pubkey_bytes[1:33]
    y1 = pubkey_bytes[33:]
    res = (b'\x00') * 65
    ice.point_increment(x1, y1, res)
    return res

def point_negation(pubkey_bytes):
    x1 = pubkey_bytes[1:33]
    y1 = pubkey_bytes[33:]
    res = (b'\x00') * 65
    ice.point_negation(x1, y1, res)
    return res

def create_baby_table(start_value, end_value):
    res = (b'\x00') * ((1+end_value-start_value) * 32)
    ice.create_baby_table(start_value, end_value, res)
    return res

def point_doubling(pubkey_bytes):
    x1 = pubkey_bytes[1:33]
    y1 = pubkey_bytes[33:]
    res = (b'\x00') * 65
    ice.point_doubling(x1, y1, res)
    return res

def point_addition(pubkey1_bytes, pubkey2_bytes):
    x1 = pubkey1_bytes[1:33]
    y1 = pubkey1_bytes[33:]
    x2 = pubkey2_bytes[1:33]
    y2 = pubkey2_bytes[33:]
    res = (b'\x00') * 65
    ice.point_addition(x1, y1, x2, y2, res)
    return res

def point_subtraction(pubkey1_bytes, pubkey2_bytes):
    x1 = pubkey1_bytes[1:33]
    y1 = pubkey1_bytes[33:]
    x2 = pubkey2_bytes[1:33]
    y2 = pubkey2_bytes[33:]
    res = (b'\x00') * 65
    ice.point_subtraction(x1, y1, x2, y2, res)
    return res

def point_loop_subtraction(num, pubkey1_bytes, pubkey2_bytes):
    x1 = pubkey1_bytes[1:33]
    y1 = pubkey1_bytes[33:]
    x2 = pubkey2_bytes[1:33]
    y2 = pubkey2_bytes[33:]
    res = (b'\x00') * (65 * num)
    ice.point_loop_subtraction(num, x1, y1, x2, y2, res)
    return res

###############################################################################
def randk(a, b):
	if flag_random:
		random.seed(random.randint(1,2**256))
		return random.SystemRandom().randint(a, b)
	else:
		if lastitem == 0:
			return a
		elif lastitem > b:
			print('[+] Range Finished')
			exit()
		else:
			return lastitem + 1

def scan_str(num):
	# Kilo/Mega/Giga/Tera/Peta/Exa/Zetta/Yotta
    dict_suffix = {0:'', 1:'Thousands', 2:'Million', 3:'Billion', 4:'Trillion'}
    num *= 1.0
    idx = 0
    for ii in range(4):
        if int(num/1000) > 0:
            idx += 1
            num /= 1000
    return ('%.5f '%num)+dict_suffix[idx]
    
# =============================================================================
# def pub2point(pub_hex):
# 	x = int(pub_hex[2:66],16)
# 	if len(pub_hex) < 70:
# 		y = bit.format.x_to_y(x, int(pub_hex[:2],16)%2)
# 	else:
# 		y = int(pub_hex[66:], 16)
# 	return ec.Point(x, y)
# =============================================================================
def getX2Y(X, y_parity, p=115792089237316195423570985008687907853269984665640564039457584007908834671663):
    Y = 3
    tmp = 1
    while Y:
        if Y & 1:
            tmp = tmp * X % p
        Y >>= 1
        X = X * X % p

    X = (tmp + 7) % p

    Y = (p + 1) // 4
    tmp = 1
    while Y:
        if Y & 1:
            tmp = tmp * X % p
        Y >>= 1
        X = X * X % p

    Y = tmp

    if Y % 2 != y_parity:
        Y = -Y % p

    return Y

def pub2upub(pub_hex):
	x = int(pub_hex[2:66],16)
	if len(pub_hex) < 70:
		y = bit.format.x_to_y(x, int(pub_hex[:2],16)%2)
#		y = getX2Y(x, int(pub_hex[:2],16)%2)
	else:
		y = int(pub_hex[66:],16)
	return bytes.fromhex('04'+ hex(x)[2:].zfill(64) + hex(y)[2:].zfill(64))

def read_pubkey_file():
    publist = [line.split()[0] for line in open(public_key_file,'r')]
    return publist

def read_xpoint_file():
    # use both 02 & 03 type xpoint
    publist = ['02'+line.split()[0] for line in open(xpoint_file,'r')]
    publist.extend( ['03'+line.split()[0] for line in open(xpoint_file,'r')] )
    return publist

def read_FULL_baby_file(num_bytes):
#    a = array('B')
#    elem = int((os.stat(bs_file).st_size)/3)
    with open(bs_file,'rb') as f:
        a = bytearray(f.read(num_bytes))
#        a.fromfile(f, elem)
    return a

def bloom_read_dll_from_file():
    with open(bloom_file,'rb') as f:
        ba_bloom2 = bytes(f.read())
#        ba_bloom2 = bytes( bytearray(f.read()) )
    return ba_bloom2


###############################################################################

st = time.time()
print('\n[+] Starting Program : BSGS mode with hybrid algo using bloom dll and secp256k1 dll     Version [', parser.version,']')

if public_key_file != '' and xpoint_file == '':
    Qlist = [ bytes(bytearray(pub2upub(line))) for line in read_pubkey_file() ]
    print('[+] Loading {} Public Keys to search'.format(len(Qlist)))
if xpoint_file != '':
    Qlist = [ bytes(bytearray(pub2upub(line))) for line in read_xpoint_file() ]
    print('[+] Loading {} Xpoints to search'.format(len(Qlist)))

# Q = pub2point(public_key)

if flag_random1 == True:
    print('[+] Search Mode: Random Start then Fully sequential from it')
elif flag_random == True:
    print('[+] Search Mode: Random Start after every n sequential key search')
else:
    print('[+] Search Mode: Sequential search in the given range')
    
    
bloom_filter = bloom_read_dll_from_file()
print('[+] Reading bloom filter from file complete in : {0:.5f} sec'.format(time.time() - st))
st = time.time()
# =============================================================================
bloom_bits = len(bloom_filter)*8        # 862655256        # fix value. Dont change
bloom_hashes = 30                       # fix value. Dont change
bloom_prob = 0.000000001                # False Positive = 1 out of 1 billion
bloom_bpe = -(math.log(bloom_prob) / 0.4804530139182014)
m = math.floor(bloom_bits/bloom_bpe)
# =============================================================================
w = math.ceil(math.sqrt(m))         # secondary table elements needed
if w > m_bb:
    print('[*] Warning. Small bPfile found. Is it ok ? Proceeding...')
    w = m_bb
# =============================================================================
#bloom_filter_gmp = gmpy2.xmpz(int.from_bytes(bloom_filter.tobytes(), byteorder='big'))
#del bloom_filter
# =============================================================================
baby_bin = read_FULL_baby_file(w*32)
print('[+] Reading Baby table from file complete in : {0:.5f} sec'.format(time.time() - st))
st = time.time()
# baby_steps = [baby_bin[cnt*32:cnt*32+32].hex() for cnt in range(w)]
# baby_steps = {int(line,10):k for k, line in enumerate(baby_steps)}
# baby_steps = set(baby_steps)
# =============================================================================

# We have to solve P = k.G, we know that k lies in the range ]k1,k2]
k1 = randk(a, b) # start from
k2 = k1 + seq

# Reset the flag after getting 1st Random Start Key
if flag_random1 == True: flag_random = False

print('[+] seq value:',seq,'   m value :' , m)
# G = ec.G
# Zp = ec.Point.IDENTITY_ELEMENT
print('[+] Search Range:',hex(a),' to ', hex(b))
###############################################################################


print('                                                                [+] k1:', hex(k1))


k1G = bytes(bytearray(scalar_multiplication(k1)))
mG = bytes(bytearray(scalar_multiplication(m)))
mGneg = bytes(bytearray(point_negation(mG)))
wG = bytes(bytearray(scalar_multiplication(w)))

st = time.time()

###############################################################################

def bsgs_exact_key(pubkey_point, z1, z2):
    z1G = bytes(bytearray(scalar_multiplication(z1)))
    if z1G == pubkey_point:
        print('BSGS FOUND PrivateKey ', hex(z1))
        return True
    S = bytes(bytearray(point_subtraction(pubkey_point, z1G)))
    
#    hex_line = bytes(bytearray(S[1:33]))
#    S2_list = bytes(bytearray(point_loop_subtraction( 1+(k2-k1)//m, S, wG )))
#    curr_byte_pos = 0
    
    stp = 0
    print('[*] Bloom collision... Checking inside the bPfile Now... ')
    while stp<(1+z2-z1):
        hex_line = bytes(bytearray(S[1:33]))
#        hex_line = hex(S.x)[2:].zfill(64)
#        idx = baby_bin.find(bytes.fromhex(hex_line), 0)
        idx = baby_bin.find(hex_line, 0)
        if idx > 0:
            kk = z1+stp+int(idx/32)+1
            print('[*] Bloom collision and bPfile collision... Final check for the key', hex(kk))
            if bytes(bytearray(scalar_multiplication(kk))) == pubkey_point:
                print('============== KEYFOUND ==============')
                print('BSGS FOUND PrivateKey ',hex(kk))
                print('======================================')
                return True
            else:
                S = bytes(bytearray(point_subtraction(S, wG)))
                stp = stp + w
                
        else:
            # Giant step
            S = bytes(bytearray(point_subtraction(S, wG)))
            stp = stp + w
        
#        hex_line = bytes(bytearray(S2_list[curr_byte_pos+1:curr_byte_pos+33]))
#        curr_byte_pos += 65
        
    print('[-] A False collision ignored. Bloom collision, but No bPfile collision.')
    return False

#################################

def bsgs_keys(pubkey_point, k1, k2):
    found = False
    if pubkey_point == k1G:
        print('BSGS FOUND PrivateKey ', hex(k1))
        found = True
        return found
    
    S = bytes(bytearray(point_subtraction(pubkey_point, k1G)))
#    hex_line = bytes(bytearray(S[1:33]))
#    S_list = bytes(bytearray(point_loop_subtraction(1+(k2-k1)//m, S, mG)))
#    curr_byte_pos = 0
    
    
    found = False
    step = 0
	
    while found is False and step<(1+k2-k1):
        hex_line = bytes(bytearray(S[1:33]))
#        hex_line = hex(S.x)[2:].zfill(64)
#        if bloom_check_add(bytes.fromhex(hex_line), 32, 0, bloom_bits, bloom_hashes, bloom_filter) > 0:
        if bloom_check_add(hex_line, 32, 0, bloom_bits, bloom_hashes, bloom_filter) > 0:
            rt = bsgs_exact_key(pubkey_point, k1+step, k1+step+m)
            if rt == True:
                return True
#            print('A False collision ignored between ',hex(k1+step), ' and ', hex(k1+step+m))
            S = bytes(bytearray(point_subtraction(S, mG)))
            step = step + m
            
# =============================================================================

        else: # Giant step
            S = bytes(bytearray(point_subtraction(S, mG)))
            step = step + m
        
#        hex_line = bytes(bytearray(S_list[curr_byte_pos+1:curr_byte_pos+33]))
#        curr_byte_pos += 65
            
    return found

# =============================================================================
if seq < m: seq = m
# =============================================================================
el = 0
while True:
    found_list = []
    for Q in Qlist:
        found = bsgs_keys(Q, k1, k2)
        if found == True:
            found_list.append(Q)
#            print("Removed Found Q from Search   ")
            el = time.time() - st
            #break
    for line in found_list:
        del Qlist[Qlist.index(line)]
    if len(Qlist) == 0:
        print("Search Finished. All pubkeys Found !")
        exit()
    else:
        curr = time.time() - st
        el += curr
        lastitem = k2
        k1 = randk(a, b)
        print('PVK not found. {0} scanned in {1:.2f} sec. New range [+] k1: {2}'.format(scan_str(seq), curr, hex(k1)))
        st = time.time()
        k2 = k1 + seq
        k1G = bytes(bytearray(scalar_multiplication(k1)))
#        print('[+] k1:', hex(k1))
print("Time Spent : {0:.5f} seconds".format(el))
