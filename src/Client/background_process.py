"""
This is the background processes class,
where all the processes run.
"""

import threading

import * from ID

class backgroundProcess():
    def __init__(self, EphID_time):
        self.stop_event = None
        self.EphID_time_var = EphID_time
        self.EphID_ready_event = threading.Event()
        self.curr_EphID = None
        self.curr_secrets = None

    
    def gen_EphID_every_t(self):
        """
        The thread process to generate EphIDs every t
        """
        while not self.stop_event.is_set():
            gen_EphID()
            self.stop_event.wait(self.EphID_time_var)

    def SharedSecret_gen_thread_process(self):
        """
        The thread process to generate Shared Secrets of every new EphIDs 
        once the EphIDs are generated
        """
        while not self.stop_event.is_set():
            self.EphID_ready_event.wait(self.EphID_time_var + 2)

            self.secrets = SharedSecret_gen() # needs to take the new EphID as input
    
    def SharedSecret_Distribution(self):
        """
        The thread process to distribute the secrets
        """
        pass

    def ID_processes(self):
        EphID_gen_thread = threading.Thread(target=gen_EphID_every_t, daemon=True)

        SharedSecret_gen_thread = threading.Thread(target=SharedSecret_gen, daemon=True)

        SSS_thread = threading.Thread(target=SharedSecret_Distribution, daemon=True)

