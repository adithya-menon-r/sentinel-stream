# Sentinel Stream

Sentinel Stream is a real time financial fraud detection platform built on top of **Apache HBase** and **HDFS**. We built the platform primarily to demonstrate how wide-column NoSQL databases, like HBase, can be used for low-latency fraud analytics at scale. 

The platform ingests a continuous stream of transaction and authentication events, runs a pattern based fraud detection search, and sends the live alerts through a WebSocket connection to the dashboard. 

The dashboard displays the live alert feed, a rolling per-minute revenue chart to catch transfer spikes, a whale leaderboard ranking the top 10 users by volume, and an auth funnel tracking the success-to-failure ratio in real time. Users can also be looked up by ID to pull their transaction profile and last 10 events from HBase.


## Getting Started

### Prerequisites

Before running anything, `HDFS (Hadoop Distributed File System)` and `HBase` need to be set up. We designed Sentinel Stream to exclusively read data from HBase, which itself requires a running HDFS instance under the hood. Refer to the official [Hadoop](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html) and [HBase](https://hbase.apache.org/book.html) documentation to set up both the services.

> Make sure to point `hbase.rootdir` at the running HDFS instance (`hdfs://localhost:9000/hbase`)

> Please note that we used a three node cluster - **one master and two data nodes** when building Sentinel Stream. The table splits and row key design are sized for this cluster layout.

Once both services are up and the NameNode UI (`http://localhost:9870`) and HBase Master UI (`http://localhost:16010`) are reachable, open the HBase shell:

```bash
hbase shell
```

Run the following commands to create the three required tables:

```
create 'events', {NAME => 'm', VERSIONS => 1}, {NAME => 'p', VERSIONS => 1}
create 'user_activity', {NAME => 'v', TTL => 2592000}, SPLITS => ['4', '8', 'c']
create 'risk_scores', {NAME => 'c', TTL => 604800},  SPLITS => ['4', '8', 'c']
exit
```

The `SPLITS` on the `user_activity` and `risk_scores` tables ensure that they are pre-partitioned into four regions (`0–3`, `4–7`, `8–b`, `c–f`). This is so that writes are distributed evenly across region servers from the start. `user_activity` rows expire after 30 days (TTL 2,592,000 seconds) and `risk_scores` rows after 7 days (TTL 604,800 seconds).

### Backend
 
1. Navigate to the backend directory:
   
    ```bash
    cd backend
    ```
 
2. Create and activate a virtual environment:
   
    ```bash
    python -m venv .venv
    
    source .venv/bin/activate   # Windows: .venv\Scripts\activate     
    ```
 
3. Install dependencies:
   
    ```bash
    pip install -r requirements.txt
    ```
 
4. Configure environment variables:
   
    ```bash
    cp .env.example .env   # Set HBase_HOST and other env vars
    ```
 
5. Start the server:
   
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```
 
The API will be available at `http://localhost:8000`.   
 
### Frontend
 
1. Navigate to the frontend directory:
   
    ```bash
    cd frontend
    ```
 
2. Install dependencies:
   
    ```bash
    npm install
    ```
 
3. Start the dev server:
   
    ```bash
    npm run dev
    ```
 
The dashboard will be available at `http://localhost:5173`.

## Data Generation

`/backend/data-gen-script.py` is the the event generation script we wrote to insert synthetic transaction and authentication events into HBase.

It spawns one worker process per CPU core, with each worker maintaining its own HBase connection (through `happybase`) and inserting events in batches of 200. With an 8 core CPU, it can write about 2,000+ events/second under normal conditions and load.

Once all the dependencies are installed, you can run the script by:

```bash
python data-gen-script.py
```

The generator writes to all the three tables simultaneously:

| Table           | Purpose                                           |
| --------------- | ------------------------------------------------- |
| `events`        | Individual event rows (logins, transfers, resets) |
| `user_activity` | Rolling hourly transfer volume counters per user  |
| `risk_scores`   | Daily interaction counters per device             |

### Row Key Design

Event rows use a salted, reverse-timestamp key: `{salt}-{user_id}-{reverse_timestamp}`. 
- The salt (first hex char of `md5(user_id)`) prevents hot spotting across HBase region servers, which means data from one particular user, no matter how large is always spread out. 
- The reverse timestamp ensures the most recent events sort first, so a last-N-events query is a simple scan from the beginning of the user's key range.

### Population

The simulation runs against a fixed pool of 2,500 users, 1,000 devices, and 1,000 randomly generated IPs. 
- Within the user pool, 15 users are designated **whales** at startup and don't change. 
- A separate pool of 8 **bot devices** with their IDs having the `BOT_` prefix are used for the suspicious-node attack pattern.

### Event Distribution

Each batch of 200 events has an independent distribution and produces the following mix:

| Probability | Event Class          | Details                                                                                                                                                                                                                                                                                         |
| ----------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 98%         | Normal events        | Random normal events from the user, device, and IP pools                                                                                                                                                                                                                                        |
| 1%          | Rapid transfer burst | 5 back-to-back `transfer_attempt` events, each between $800 and $2000 from the same user and device in a single batch. This means cumulatively a session's transfer can be between $4000 - $10,000. If such bursts land close together, the user will definitely croos the detection threshold. |
| 1%          | Suspicious node      | 1 bot device performs a `login_success` event and authenticates as 10 randomly sampled victim accounts from a fixed IP (`45.33.22.11`). Each successful login increments the `risk_scores` counter, eventually crossing the detection threshold.                                                |

Within the 98% normal slice, event are split further:

| Probability | Type               | Amount Range                                                                                                    |
| ----------- | ------------------ | --------------------------------------------------------------------------------------------------------------- |
| ~30%        | `transfer_attempt` | $10 - $500 for regular users & $10,000 - $50,000 for whale users                                                |
| ~70%        | `login_success`    | $0 _(Most real world events aren't transactions but simple events like authentication, account checking, etc.)_ |


### Attack Modes

The three flag files are used to override the normal event distribution:

| Flag File        | Effect                                                                                  |
| ---------------- | --------------------------------------------------------------------------------------- |
| `attack.txt`     | All of the batch events become `login_fail` events to simulate a brute-force atack      |
| `rapid.txt`      | All events are rapid transfer bursts                                                    |
| `suspicious.txt` | All events are suspicious-node attacks with bot devices sending out events continuously |

Run the following commands to start or stop an override:
```bash
touch attack.txt   # Start the override
rm attack.txt      # Stop it
```

## Fraud Detection Patterns

The backend continuously scans HBase and attempts to detect the two following patterns:

| Pattern             | Trigger                                                                      |
| ------------------- | ---------------------------------------------------------------------------- |
| **Rapid Transfers** | A user's rolling hourly transfer total exceeds $10,000                       |
| **Suspicious Node** | A single device authenticates as more than 50 distinct accounts within a day |

Alerts are broadcast in real time over the `/ws/alerts` WebSocket endpoint as soon as a pattern matches.

## API Reference

| Method | Path                     | Description                                  |
| ------ | ------------------------ | -------------------------------------------- |
| GET    | `/health`                | Health check                                 |
| GET    | `/api/metrics/revenue`   | Per-minute transfer totals                   |
| GET    | `/api/metrics/whales`    | Top 10 users by transfer volume              |
| GET    | `/api/metrics/auth`      | Auth funnel stats (success vs failure rates) |
| GET    | `/api/user/{id}/profile` | User velocity profile from HBase             |
| GET    | `/api/user/{id}/history` | Last 10 events for a user                    |
| WS     | `/ws/alerts`             | Live fraud alerts                            |


## Contributors

| Name            | GitHub ID                                             |
| --------------- | ----------------------------------------------------- |
| Adithya Menon R | [adithya-menon-r](https://github.com/adithya-menon-r) |
| Narain BK       | [NarainBK](https://github.com/NarainBK)               |
| Varun Raj V     | [VarunRajV28](https://github.com/VarunRajV28)         |
| PG Karthikeyan  | [cootot](https://github.com/cootot)                   |
| Dheeraj KB     | [Dheeraj-74](https://github.com/Dheeraj-74)           |

## License

This project is licensed under the [MIT LICENSE](LICENSE).
