from ID import *

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

t = 15
k = 3
n = 5
eph_id = gen_EphID(t)

# verify SSS
shares = SharedSecret_gen(eph_id, k, n)
assert len(shares) == n, f"ID.py Err: {n} shares required but only got {len(shares)}"

# test reconstruction of secrets with n-n shares
_n_n_shares = verify_k_of_n_shares_reconstruction(shares, eph_id.to_bytes(), n, n)
assert (_n_n_shares == True), "ID.py Err: shares not constructed correctly"

# test reconstruction of secrets with insufficient shares
_i_n_shares = verify_k_of_n_shares_reconstruction([shares[1], shares[3]],eph_id.to_bytes(), 2, n)
assert (_i_n_shares == False), "ID.py Err: shares not constructed correctly"

# test reconstruction of secrets with k-n shares
_k_n_shares = verify_k_of_n_shares_reconstruction(shares[:k], eph_id.to_bytes(), k, n)
assert (_k_n_shares == True), "ID.py Err: shares not constructed correctly"
