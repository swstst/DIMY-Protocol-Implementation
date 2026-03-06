class User:
      def __init__(self, Dt, qbf: BloomFilter):
            self.cycle = Dt
            self.qbf = qbf
            self.dbfs = list[BloomFilters]

      def counter(self):
            # thread for the time every second
            self.cycle -= 1

      def add_dbf_to_qbf(self):
            self.qbf.add(self.dbf)

      def upload_dbf(self, cbf):
            # combine all dbfs to upload to cbf
            cbf.upload(self.dbfs)

      