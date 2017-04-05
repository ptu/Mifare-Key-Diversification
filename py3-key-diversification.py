def gen_subkeys(K,cipher):
    """Generate subkeys of cipher"""
    from struct import pack, unpack
    
    L = cipher.encrypt(bytes.fromhex("00000000000000000000000000000000"))

    LHigh = unpack(">Q",L[:8])[0]
    LLow  = unpack(">Q",L[8:])[0]

    K1High = ((LHigh << 1) | ( LLow >> 63 )) & 0xFFFFFFFFFFFFFFFF
    K1Low  = (LLow << 1) & 0xFFFFFFFFFFFFFFFF

    if (LHigh >> 63):
        K1Low ^= 0x87

    K2High = ((K1High << 1) | (K1Low >> 63)) & 0xFFFFFFFFFFFFFFFF
    K2Low  = ((K1Low << 1)) & 0xFFFFFFFFFFFFFFFF

    if (K1High >> 63):
        K2Low ^= 0x87

    K1 = pack(">QQ", K1High, K1Low)
    K2 = pack(">QQ", K2High, K2Low)

    return K1, K2

def xor(data, key):
    """XOR function"""
    from itertools import cycle
    xored = "".join( "%02x" % (x ^ y) for (x,y) in zip(data, cycle(key)))
    return xored

def cmac_div(key, UID, Sector_number):
    """"""
    from Crypto.Cipher import AES

    IV = bytes.fromhex("00000000000000000000000000000000") ##Init vector for AES
    cipher = AES.new(bytes.fromhex(key), AES.MODE_CBC, IV) ##AES in Cipher block Chaining mode, Init Vector=00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    K1, K2 = gen_subkeys( key, cipher )
    xorkey = K1

    M = "01" + UID + Sector_number
    padding = "8000000000000000000000000000000000000000000000000000"
    
    if len(M) < 64: ## if padding needed
            M += padding
            xorkey = K2
    
    if len(M) != 64:
            print("M != 32 byte!")
            exit()

    xordata = bytes.fromhex(M[-32:]) ##last 16 bytes of M
    xoreddata = xor(xordata,xorkey)##xor xordata with K1 of K2
    M = M[:-32] + xoreddata ##replace last 16 bytes with xordata
    cipher = AES.new( bytes.fromhex(key), AES.MODE_CBC, IV)##reset cipher
    divkey = cipher.encrypt( bytes.fromhex(M) ).hex()[-32:-20] ##AES M and slice out the right piece

    print("AES version")
    print("Masterkey:\t " + key.upper())
    print("UID:\t\t " + UID.upper())
    print("Sector:\t\t " + Sector_number.upper())
    print("Subkey 1:\t " + K1.hex().upper())
    print("Subkey 2:\t " + K2.hex().upper())
    print("Message:\t " + M.upper())
    print("Diversified key: " + divkey.upper())
    print() 

    return divkey

def des3_div(key, UID, Sector_number, MIFkey):
    """"""
    from Crypto.Cipher import DES3

    trailerblock = 4*int(Sector_number)+3 ##van sector naar trailerblock van sector
    trailerblock = "{:02x}".format(trailerblock)

    M = MIFkey[:8]
    M += xor( bytes.fromhex(MIFkey[8:10]), bytes.fromhex(UID[:2]))
    M += xor( bytes.fromhex(MIFkey[10:]),  bytes.fromhex(UID[2:4]))
    M += xor( bytes.fromhex(trailerblock), bytes.fromhex(UID[4:6]))
    M += UID[6:]
	
    cipher = DES3.new( bytes.fromhex(key) )
    divkey=cipher.encrypt( bytes.fromhex(M) ).hex()[2:14]

    print("3DES version")
    print("Masterkey:\t " + key.upper())
    print("UID:\t\t " + UID.upper())
    print("Sector:\t\t " + Sector_number.upper())
    print("Trailer Block:\t " + trailerblock)
    print("Mifare key:\t " + MIFkey.upper())
    print("Message:\t " + M.upper())
    print("Diversified key: " + divkey.upper())
    print()

    return divkey

if __name__ == "__main__":

    masterkey = "00112233445566778899aabbccddeeff"
    UID="F4EA548E"
    Sector_number="05"
    MIFkey="A0A1A2A3A4A5" ## Only needed for 3DES version(MF RC171)
    
    cmac_div(masterkey, UID, Sector_number)
    des3_div(masterkey, UID, "01", MIFkey)
