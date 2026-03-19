from random import SystemRandom
from Crypto.Protocol.SecretSharing import Shamir


import threading

high_bound = 10**100

def gen_EphID(G):
    """
    Generate Ephemeral IDs 

    args:
        G ==> Generator of Elliptic curve

    returns:
        Eph_ID ==> the resulting ephemeral ID
    """
    cryptogen = SystemRandom()
    
    x = cryptogen.randrange(high_bound) 
    mask = (1 << 128) - 1
    Eph_ID = (G**x) & mask

    return Eph_ID

def SharedSecret_gen(new_EphID, k, n):
    """
    Generate k-out-of-n shamir shares

    args:
        new_EphID => the new ephemeral ID
        k => the minimum amount of shares needed to reconstruct ID
        n => ID is split into n shares
    
    return:
        the shares back, the shares are in form (idx, share)
    """
    shares = Shamir.split(k, n, new_EphID)
    return shares

def SharedSecret_Distribution():
    pass


        
