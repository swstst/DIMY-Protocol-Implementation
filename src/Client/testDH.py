from Crypto.Random.random import getrandbits
from Crypto.Protocol.SecretSharing import Shamir
from Crypto.PublicKey import ECC
from shamir import Shares, split, combine
import math

def gen_EphID():
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
    print(keyPair)
    EphID = keyPair.pointQ.x

    return EphID, d

def ECDH(pk, sk):
    """
    Elliptic Curve Diffie Hellman key exchange to get shared secret

    args:
        pk => public key of exchange buddy, in this case only the x of (x,y)
        sk => private key

    return:
        sharedSecret.x => x point of the shared secret of the exchange
    """
    print(int(pk))
    # FIPS 186-4 NIST prime
    p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
    b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
    x = int(pk)
    y_squared = (x**3 - 3*x + b) % p
    y = pow(y_squared, (p + 1) // 4, p)

    print('y= ' + str(y))
    print('y * y=     ' + str((y * y) % p))
    print('y_squared= ' + str(y_squared))
    assert((y * y) % p == y_squared)

    # full public key
    pub_key = ECC.construct(curve='p256', point_x=x, point_y=y).pointQ

    sharedSecret = pub_key * sk

    return sharedSecret


pk, sk = gen_EphID()

res = ECDH(pk, sk)
print(res.x)
