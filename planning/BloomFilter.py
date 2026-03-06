class BloomFilter:
      def __init__(self, size):
            pass

      def __add__(self, other):
            pass


class DailyBloomFilter(BloomFilter):
      
      def __init__(self, size, t):
            self.encounter_timer = (t * 6)
            self.existence_timer = (t * 6 * 6) / 60
            # decrement per second
            super().__init__(size)

      def __add__(self, other):
            return super().__add__(other)


class ContactBloomFilter(BloomFilter):
      
      def __init__(self, size):
            self.data = []
            super().__init__(size)

      def upload(self, dbfs):
            ...

      def send(self, backend_server_addr):
            # TCP socket send self.data to backend_server_addr
            # receive response
            
            ...