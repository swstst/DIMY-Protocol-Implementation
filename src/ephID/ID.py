from Crypto.Random.random import getrandbits
from Crypto.Protocol.SecretSharing import Shamir
from Crypto.PublicKey import ECC
from shamir import Shares, split, combine
import math


def gen_keyPair(d: int):
    """
    Generate ECC key pair for Ephemeral IDs.

    args:
        d ==> random 256-bit secret

    returns:
        keyPair ==> ECC key pair

    """
    keyPair = ECC.construct(curve="p256", d=d)
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

    return EphID, d


def gen_shares(new_EphID, k: int, n: int) -> tuple:
    """
    Generate k-out-of-n shamir shares

    args:        new_EphID => the new ephemeral ID
        k => the minimum amount of shares needed to reconstruct ID
        n => ID is split into n shares

    return:
        the shares back, the shares are in form (idx, share)
    """

    # convert ephID into bytes
    eph_id_bytes = int(new_EphID).to_bytes(32, byteorder="big")
    shares = split(secret=eph_id_bytes, parts=n, threshold=k)

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


def ECDH(pk, sk):
    """
    Elliptic Curve Diffie Hellman key exchange to get shared secret

    args:
        pk => public key of exchange buddy, in this case only the x of (x,y)
        sk => private key

    return:
        sharedSecret.x => x point of the shared secret of the exchange
    """
    # FIPS 186-4 NIST prime
    p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF

    # FIPS constant
    b = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B

    x = int(pk)
    y_squared = (x**3 - 3 * x + b) % p  # p256 curve equation

    # Tonelli-Shanks Algorithm to get Mod roots
    y = pow(y_squared, (p + 1) // 4, p)  # get the y back ( decompress )

    # TODO confirm that this has neglible guessing advantage

    assert (y * y) % p == y_squared

    # full public key
    pub_key = ECC.construct(curve="p256", point_x=x, point_y=y).pointQ

    sharedSecret = pub_key * sk

    return sharedSecret
