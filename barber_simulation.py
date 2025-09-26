# barber_simulation.py
# Simulação do problema do barbeiro dorminhoco com modos 'safe' e 'buggy' (possível deadlock).
import threading, time, random, queue

class BarberSimulation:
    def __init__(self, num_barbers=1, num_chairs=3, arrival_rate=1.0, enable_solution=True):
        self.num_barbers = max(1, int(num_barbers))
        self.num_chairs = max(0, int(num_chairs))
        self.arrival_rate = float(arrival_rate)  # avg seconds between arrivals
        self.enable_solution = bool(enable_solution)

        self.waiting = queue.Queue(maxsize=self.num_chairs)
        self.barbers = []
        self.barber_states = ["idle"] * self.num_barbers
        self.customer_count = 0
        self.served_count = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        # semaphore used in safe mode to wake barbers
        self.customers_sem = threading.Semaphore(0)
        self.barbers_sem = threading.Semaphore(0)

    def start(self):
        self.stop_event.clear()
        # start barber threads
        for i in range(self.num_barbers):
            t = threading.Thread(target=self.barber_worker, args=(i,), daemon=True)
            t.start()
            self.barbers.append(t)
        # start arrival thread
        self.arrival_thread = threading.Thread(target=self.arrival_worker, daemon=True)
        self.arrival_thread.start()

    def stop(self):
        self.stop_event.set()
        # release semaphores to unblock threads
        for _ in range(self.num_barbers):
            try:
                self.customers_sem.release()
            except:
                pass

    def arrival_worker(self):
        while not self.stop_event.is_set():
            time.sleep(max(0.01, random.expovariate(1.0/self.arrival_rate)))
            # new customer arrives
            with self.lock:
                self.customer_count += 1
                cid = self.customer_count
            # safe mode: try to sit in waiting room, else leave
            if self.enable_solution:
                try:
                    self.waiting.put_nowait(cid)
                    # signal a customer available
                    self.customers_sem.release()
                except queue.Full:
                    # customer leaves
                    pass
            else:
                # buggy mode: naive handling - try to acquire both a barber and a chair in inconsistent order to simulate potential deadlock
                # We simulate the buggy behavior: if waiting room full, customer spins attempting to reserve a barber lock, which may deadlock
                reserved = False
                # attempt to take a spot or forcefully try to get service (buggy)
                # We'll attempt to put even if full by blocking on a lock to simulate a stuck customer
                try:
                    # try without blocking first
                    self.waiting.put_nowait(cid)
                    self.customers_sem.release()
                    reserved = True
                except queue.Full:
                    # simulate problematic behavior: try to acquire a barber slot (by acquiring main lock)
                    # but barbers also may try to acquire lock in different order -> deadlock can happen
                    acquired = self.lock.acquire(timeout=2)
                    if acquired:
                        # unable to sit, we keep lock and sleep (simulates blocking customer holding lock)
                        try:
                            time.sleep(2)
                        finally:
                            self.lock.release()
                    else:
                        # timed out acquiring lock: leave
                        pass

    def barber_worker(self, idx):
        while not self.stop_event.is_set():
            if self.enable_solution:
                # safe mode: wait for a customer signal
                self.customers_sem.acquire()
                if self.stop_event.is_set():
                    break
                try:
                    cid = self.waiting.get_nowait()
                except queue.Empty:
                    continue
                with self.lock:
                    self.barber_states[idx] = f"serving {cid}"
                # simulate haircut
                time.sleep(max(0.1, random.uniform(0.5, 1.5)))
                with self.lock:
                    self.served_count += 1
                    self.barber_states[idx] = "idle"
            else:
                # buggy mode: barber tries to grab lock and waiting customer in inconsistent order
                # barber acquires a per-barber lock then tries to get waiting without using semaphore -> potential race
                with self.lock:
                    self.barber_states[idx] = "looking_for_customer"
                    try:
                        cid = self.waiting.get_nowait()
                        self.barber_states[idx] = f"serving {cid}"
                    except queue.Empty:
                        # go to sleep (but buggy: we sleep while holding no signal to wake properly)
                        self.barber_states[idx] = "sleeping (buggy)"
                        # in buggy case, we sleep and won't be notified correctly
                        time.sleep(2)
                        self.barber_states[idx] = "idle"
                        continue
                # haircut
                time.sleep(max(0.1, random.uniform(0.5, 1.5)))
                with self.lock:
                    self.served_count += 1
                    self.barber_states[idx] = "idle"

    def snapshot(self):
        with self.lock:
            return {
                "num_barbers": self.num_barbers,
                "num_chairs": self.num_chairs,
                "waiting": list(self.waiting.queue),
                "barber_states": list(self.barber_states),
                "customer_count": self.customer_count,
                "served_count": self.served_count,
            }

if __name__ == '__main__':
    sim = BarberSimulation()
    sim.start()
    time.sleep(3)
    print(sim.snapshot())
