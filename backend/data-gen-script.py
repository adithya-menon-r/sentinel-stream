import happybase
import time
import random
import multiprocessing
import sys
import hashlib
import os

# Config
HBASE_MASTER_IP = '127.0.0.1' 
BATCH_SIZE = 200 
NUM_WORKERS = multiprocessing.cpu_count() 
NUM_USERS = 2500

# Constants
COL_TYPE = b'm:type'
COL_AMT = b'm:amt'
COL_IP = b'm:ip'
COL_DEV = b'm:dev'
COL_STATUS = b'm:status'
COL_RAW = b'p:raw_agent'

VAL_SUCCESS = b'SUCCESS'
VAL_FAILED = b'FAILED'
VAL_AGENT = b'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X)...'

TYPE_LOGIN_OK = b'login_success'
TYPE_LOGIN_FAIL = b'login_failed'
TYPE_TRANSFER = b'transfer_attempt'
TYPE_RESET = b'password_reset'


def get_salt(identifier):
    return hashlib.md5(identifier.encode('utf-8')).hexdigest()[0]


# Data Pools
USERS = [f"user_{i}" for i in range(1, NUM_USERS + 1)]
USER_SALTS = {u: get_salt(u) for u in USERS}

WHALES = set(random.sample(USERS, 15))

DEVICES = [os.urandom(4).hex() for _ in range(1000)]
DEVICE_SALTS = {d: get_salt(d) for d in DEVICES}

IPS = [f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}" for _ in range(1000)]

BOT_DEVICES = [f"BOT_{os.urandom(2).hex()}" for _ in range(8)]
BOT_DEVICE_SALTS = {d: get_salt(d) for d in BOT_DEVICES}


def worker(worker_id):
    time.sleep(worker_id * 0.1) 
    
    try:
        connection = happybase.Connection(HBASE_MASTER_IP)
        events_table = connection.table('events')
        activity_table = connection.table('user_activity')
        risk_table = connection.table('risk_scores')
    except Exception as e:
        print(f"Worker {worker_id} connection failed: {e}")
        return

    print(f"Worker {worker_id} started. Pushing data...")
    
    while True:
        try:
            current_ts = int(time.time() * 1000)
            hour_bucket = time.strftime('%Y%m%d%H', time.gmtime(current_ts / 1000.0)).encode('utf-8')
            day_bucket = time.strftime('%Y%m%d', time.gmtime(current_ts / 1000.0)).encode('utf-8')
            
            brute_force_active = os.path.exists("attack.txt")
            rapid_active = os.path.exists("rapid.txt")
            suspicious_active = os.path.exists("suspicious.txt")
            
            with events_table.batch(batch_size=BATCH_SIZE) as b:
                events_in_batch = 0
                
                while events_in_batch < BATCH_SIZE:
                    current_ts += 1 
                    reverse_ts = sys.maxsize - current_ts
                    
                    # ATTACK MODE OVERRIDE
                    if brute_force_active:
                        u, d, ip = random.choice(USERS), random.choice(DEVICES), random.choice(IPS)
                        salt = USER_SALTS[u]
                        row_key = f"{salt}-{u}-{reverse_ts}".encode('utf-8')
                        
                        b.put(row_key, {
                            COL_TYPE: TYPE_LOGIN_FAIL, COL_AMT: b'0',
                            COL_IP: ip.encode('utf-8'), COL_DEV: d.encode('utf-8'),
                            COL_STATUS: VAL_FAILED, COL_RAW: VAL_AGENT
                        })
                        events_in_batch += 1
                        continue

                    roll = random.random()
                    
                    if rapid_active:
                        roll = 0.0
                    elif suspicious_active:
                        roll = 0.015
                    
                    # RAPID TRANSFERS - 1%
                    if roll < 0.01: 
                        u, d, ip = random.choice(USERS), random.choice(DEVICES), random.choice(IPS)
                        salt = USER_SALTS[u]
                        v_key = f"{salt}-{u}-".encode('utf-8') + hour_bucket
                        total_amt = 0
                        for _ in range(5):
                            current_ts += 1
                            r_ts = sys.maxsize - current_ts
                            row_key = f"{salt}-{u}-{r_ts}".encode('utf-8')
                            amt = random.randint(800, 2000)
                            total_amt += amt
                            
                            b.put(row_key, {
                                COL_TYPE: TYPE_TRANSFER, COL_AMT: str(amt).encode('utf-8'),
                                COL_IP: ip.encode('utf-8'), COL_DEV: d.encode('utf-8'),
                                COL_STATUS: VAL_SUCCESS, COL_RAW: VAL_AGENT
                            })
                            events_in_batch += 1
                        activity_table.counter_inc(v_key, b'v:tx_sum_cents', total_amt * 100)

                    # SUSPICIOUS NODE - 1%
                    elif roll < 0.02:
                        d = random.choice(BOT_DEVICES)
                        d_salt = BOT_DEVICE_SALTS[d]
                        ip = "45.33.22.11"
                        victims = random.sample(USERS, 10)
                        
                        for v in victims:
                            current_ts += 1
                            r_ts = sys.maxsize - current_ts
                            v_salt = USER_SALTS[v]
                            b.put(f"{v_salt}-{v}-{r_ts}".encode('utf-8'), {
                                COL_TYPE: TYPE_LOGIN_OK, COL_AMT: b'0',
                                COL_IP: ip.encode('utf-8'), COL_DEV: d.encode('utf-8'),
                                COL_STATUS: VAL_SUCCESS, COL_RAW: VAL_AGENT
                            })
                            c_key = f"{d_salt}-{d}-".encode('utf-8') + day_bucket
                            risk_table.counter_inc(c_key, b'c:interactions', 1)
                            events_in_batch += 1

                    # NORMAL - 98%
                    else:
                        u, d, ip = random.choice(USERS), random.choice(DEVICES), random.choice(IPS)
                        salt = USER_SALTS[u]
                        row_key = f"{salt}-{u}-{reverse_ts}".encode('utf-8')
                        
                        if random.random() < 0.30:
                            ev_type = TYPE_TRANSFER
                            amt = random.randint(10000, 50000) if u in WHALES else random.randint(10, 500)
                        else:
                            ev_type = TYPE_LOGIN_OK
                            amt = 0
                        
                        b.put(row_key, {
                            COL_TYPE: ev_type, COL_AMT: str(amt).encode('utf-8'),
                            COL_IP: ip.encode('utf-8'), COL_DEV: d.encode('utf-8'),
                            COL_STATUS: VAL_SUCCESS, COL_RAW: VAL_AGENT
                        })
                        events_in_batch += 1

        except Exception as e:
            time.sleep(0.5)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    print(f"Starting data generation with {NUM_WORKERS} parallel workers...")
    
    processes = []
    for i in range(NUM_WORKERS):
        p = multiprocessing.Process(target=worker, args=(i,))
        p.daemon = True
        processes.append(p)
        p.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
        print("Data Generation stopped")
