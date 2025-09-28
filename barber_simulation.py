# barber_simulation.py
import threading, time, random, queue

class BarberSimulation:
    def __init__(self, num_barbers=1, num_chairs=3, arrival_rate=1.0, enable_solution=True):
        self.num_barbers = max(1, int(num_barbers))
        self.num_chairs = max(0, int(num_chairs))
        self.arrival_rate = float(arrival_rate)
        self.enable_solution = bool(enable_solution)

        self.waiting = queue.Queue(maxsize=self.num_chairs)
        self.barbers = []
        # O estado "sleeping" será usado para visualizar o deadlock
        self.barber_states = ["idle"] * self.num_barbers
        self.customer_count = 0
        self.served_count = 0
        self.turned_away_count = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        # Semáforo é a "solução" para o problema. Usado apenas no modo SAFE.
        self.customers_sem = threading.Semaphore(0)

    def start(self):
        self.stop_event.clear()
        for i in range(self.num_barbers):
            t = threading.Thread(target=self.barber_worker, args=(i,), daemon=True)
            t.start()
            self.barbers.append(t)
        self.arrival_thread = threading.Thread(target=self.arrival_worker, daemon=True)
        self.arrival_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.enable_solution:
            for _ in range(self.num_barbers):
                try:
                    self.customers_sem.release()
                except:
                    pass

    def arrival_worker(self):
        while not self.stop_event.is_set():
            base_interval = self.arrival_rate / max(1, self.num_barbers * 0.8)
            sleep_time = max(0.05, random.expovariate(1.0 / base_interval))
            time.sleep(sleep_time)

            with self.lock:
                self.customer_count += 1
                cid = self.customer_count
            
            try:
                self.waiting.put_nowait(cid)
                if self.enable_solution:
                    self.customers_sem.release()
            except queue.Full:
                with self.lock:
                    self.turned_away_count += 1

    def barber_worker(self, idx):
        while not self.stop_event.is_set():
            if self.enable_solution:
                # MODO SAFE: O barbeiro espera no semáforo até um cliente o acordar.
                self.customers_sem.acquire()
            else:
                # MODO BUGGY: Lógica ajustada para forçar o deadlock de forma visível.
                if self.waiting.empty():
                    # 1. Barbeiro olha a fila, não vê ninguém e decide dormir.
                    with self.lock:
                        self.barber_states[idx] = "sleeping"
                    
                    # 2. Ele dorme por um instante. ESTA é a janela crítica.
                    #    Se um cliente chegar AGORA, ele verá o barbeiro "sleeping"
                    #    e esperará, mas o barbeiro nunca foi notificado.
                    time.sleep(0.5) 
                    
                    # 3. Barbeiro "acorda" por conta própria e checa a fila de novo.
                    #    Se um cliente chegou durante o passo 2, o barbeiro não sabe.
                    #    Ele vai apenas continuar o loop e voltar a dormir. DEADLOCK!
                    if self.waiting.empty():
                        continue # Volta para o início do loop e dorme de novo.
                    else:
                        # Se por sorte ninguém chegou, ele volta ao estado idle.
                        with self.lock:
                            self.barber_states[idx] = "idle"

            if self.stop_event.is_set():
                break
                
            try:
                cid = self.waiting.get_nowait()
            except queue.Empty:
                continue

            with self.lock:
                self.barber_states[idx] = "serving"
            
            # Muda o estado para o cliente específico que está sendo atendido
            with self.lock:
                 self.barber_states[idx] = f"serving {cid}"

            time.sleep(random.uniform(0.5, 1.5))  # Tempo do corte
            
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
                "turned_away_count": self.turned_away_count,
            }
