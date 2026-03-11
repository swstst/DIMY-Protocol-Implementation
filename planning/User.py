from secrets import randbits
from Crypto.Protocol.SecretSharing import Shamir
from Crypto.Cipher import AES
# Need to use AES.EAX to ensure reconstruction of secret is successful
import sys

class User:
      def __init__(self, Dt, qbf: BloomFilter):
            self.cycle = Dt
            self.qbf = qbf
            self.dbfs = list[BloomFilters]
            self.ephID = self.gen_ephID()

      def gen_ephID(self) -> bytes:
            # generate a random number as secret key. 
            # result need to be 256-bits
            ...

      def counter(self):
            # thread for the time every second
            self.cycle -= 1

      def add_dbf_to_qbf(self):
            self.qbf.add(self.dbf)

      def upload_dbf(self, cbf):
            # combine all dbfs to upload to cbf
            cbf.upload(self.dbfs)


# for unit testing
if __name__ == '__main__':
      user = User()

      assert len(user.ephID) == 256, f"Error [User.py]: EphID need to be 256-bits, not {len(user.eph_ID)}"

      # eg command line
      # python3 file.py -t [] -k [] -n []