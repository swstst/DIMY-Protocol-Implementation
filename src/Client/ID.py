from Crypto.Random.random import getrandbits
from Crypto.Protocol.SecretSharing import Shamir
from Crypto.PublicKey import ECC
from shamir import Shares, split, combine

def gen_keyPair(d: int):
    """
    Generate ECC key pair for Ephemeral IDs.

    args:
        d ==> random 256-bit secret

    returns:
        keyPair ==> ECC key pair 
        
    """
    keyPair = ECC.construct(curve='p256', d=d)
    return keyPair

def gen_EphID(t: int):
    """
    Generate Ephemeral IDs

    args:
        t ==> time to seed randomness (if possible)

    returns:
        Eph_ID ==> the resulting ephemeral ID (public key of ECC key pair)
    """
    # use t to seed the randomness (?)
    
    # secret - could use secrets instead of PyCrypto's random lib, however didn't find anything bad about it ...
    d = getrandbits(256)
    
    EphID = gen_keyPair(d).pointQ.x

    return EphID


def SharedSecret_gen(new_EphID, k:int, n:int) -> tuple:
    """
    Generate k-out-of-n shamir shares

    args:        new_EphID => the new ephemeral ID
        k => the minimum amount of shares needed to reconstruct ID
        n => ID is split into n shares
    
    return:
        the shares back, the shares are in form (idx, share)
    """

    # convert ephID into bytes
    eph_id_bytes = int(new_EphID).to_bytes(32, byteorder='big')
    shares = split(secret = eph_id_bytes, parts = n, threshold = k)

    return shares

def combine_shares(shares: list) -> bytearray:
    """
    Reconstruct secret from k shares

    args:
        new_EphID => the new ephemeral ID
        k => the minimum amount of shares needed to reconstruct ID
        n => ID is split into n shares
    
    return:
        the shares back, the shares are in form (idx, share)
    """
    
    recovered = combine(shares)
    return recovered