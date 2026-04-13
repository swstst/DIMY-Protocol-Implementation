from ephID.ID import *
from Crypto.Hash import SHA256

if __name__ == '__main__':
        
        ephid, d = gen_EphID()
        new_shares = gen_shares(new_EphID=ephid, k=3, n=5)
        shares = new_shares.copy()
        shares = shares[:2] 
        shares.append(new_shares[1])
        print("SHARES: ", shares)
        combined = combine_shares(shares)
        

        data = ephid.to_bytes(32, 'big')
        print(ephid)
        print("EPHID: ", SHA256.new(data=data).digest())
        print(new_shares)
        print("COMBINED: ", SHA256.new(data=combined).digest())
