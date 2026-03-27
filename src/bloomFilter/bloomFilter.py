from bitarray import bitarray

class bloomFilter():
    def __init__(self):
        self.bitarray = bitarray(256).setall(0)

    def update( item ):
        pass #self.bitarray.add(H(item))

    def check_membership(item):
         pass # returns T/F
