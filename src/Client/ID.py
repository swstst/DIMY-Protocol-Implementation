from Crypto.Random.random import getrandbits
from Crypto.Protocol.SecretSharing import Shamir
from Crypto.PublicKey import ECC
from shamir import Shares, split, combine

def gen_EphID(t: int):
    """
    Generate Ephemeral IDs by building a ECC key pair.

    args:
        G ==> Generator of Elliptic curve

    returns:
        Eph_ID ==> the resulting ephemeral ID
    """
    # use t to seed the randomness (?)
    
    # secret - could use secrets instead of PyCrypto's random lib, however didn't find anything bad about it ...
    d = getrandbits(256)
    
    keyPair = ECC.construct(curve='p256', d=d)
    EphID = keyPair.pointQ.x

    return EphID

def SharedSecret_gen(new_EphID, k:int, n:int) -> tuple:
    """
    Generate k-out-of-n shamir shares

    args:
        new_EphID => the new ephemeral ID
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
    
