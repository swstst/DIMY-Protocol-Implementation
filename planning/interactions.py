def gen_eph_id(time, generator) -> int:
      seed = time
      secret = random.seed(seed)
      return generator ** secret

# or use pycryptodome 
def chunk_n_ephID(ephID, n) -> list[bytes]:
      ephID_chunks = []
      # some sort of masking
      return 


def dh_shared_ephID(shared_secret, secret, domain):
      return (shared_secret ** secret % domain)


def put_in_DBF(user, shared_ephi, start_time) ->: None
      if (curr_time - start_time )< 24hours:
            item = hash(shared_ephi)
            user.dailybloomfilter.add(shared_ephi)

      else:
            ...

      return

