from random import SystemRandom

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


def SharedSecret_Distribution():
    pass

def SharedSecret_gen():
    pass

        
