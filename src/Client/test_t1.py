from ID import *

def t15_k3_n5_id() -> None:
      t = 15
      k = 3
      n = 5
      eph_id = gen_EphID(t)

      print("="*3, "PUBLIC KEY", "="*3)
      #print(f"Public Key (x): {hex(eph_id.pointQ.x)}")
      #print(f"Public Key (y): {hex(eph_id.pointQ.y)}")
      print(f"Public Key (x): {hex(eph_id)}")

      # test private key generation
      print()
      print("="*3, "PRIVATE KEY PEM format", "="*3)
      priv_key = eph_id.export_key(format="PEM")
      print(priv_key)
      print()

      # verify SSS
      shares = SharedSecret_gen(eph_id, k, n)
      assert len(shares) == n, f"ID.py Err: {n} shares required but only got {len(shares)}"
      
      # test reconstruction of secrets with n-n shares
      _n_n_shares = verify_k_of_n_shares_reconstruction(shares, (eph_id.pointQ.x).to_bytes(), n, n)
      assert (_n_n_shares == True), "ID.py Err: shares not constructed correctly"
      
      # test reconstruction of secrets with insufficient shares
      _i_n_shares = verify_k_of_n_shares_reconstruction([shares[1], shares[3]],(eph_id.pointQ.x).to_bytes(), 2, n)
      assert (_i_n_shares == False), "ID.py Err: shares not constructed correctly"

      # test reconstruction of secrets with k-n shares
      _k_n_shares = verify_k_of_n_shares_reconstruction(shares[:k], (eph_id.pointQ.x).to_bytes(), k, n)
      assert (_k_n_shares == True), "ID.py Err: shares not constructed correctly"


def verify_k_of_n_shares_reconstruction(shares: list, eph_ID: bytes, i: int, n:int) -> bool:
      
      print("="*3, "SHARES RECEIVED", "="*3)
      for share in shares:
            print(share)
      
      print()
      print('='*3, f"CONSTRUCT SECRET FROM {i}-of-{n} SHARES", "="*3)
      recovered_secret = bytes(combine_shares(shares))

      print(recovered_secret)
      
      print('='*3, "ORIGINAL SECRET", "="*3)
      print(eph_ID)

      return recovered_secret == eph_ID

if __name__ == '__main__':
      t15_k3_n5_id()
      
