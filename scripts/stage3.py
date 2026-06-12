#!/usr/bin/env python3
# Stage 3: blind hand-graded task eval.
#
# Downloads required first (gpt-oss):
#   hf download ggml-org/gpt-oss-20b-GGUF --include "*mxfp4*" --local-dir /workspace/models/gpt-oss
#
# Runs 10 prompts (5 coding, 5 reasoning) through each model at its
# recommended deployment samplers, via llama-server. Models are shuffled
# into anonymous labels A/B/C at runtime; the mapping is written to
# key.txt — do not open it until grading is complete.
#
# Run under nohup:
#   nohup python3 stage3.py > stage3.log 2>&1 &

import json, os, random, subprocess, time, urllib.request

LLAMA = "/workspace/llama.cpp/build/bin/llama-server"
OUT = "/workspace/stage3"
PORT = 8089

def find_gguf(d):
    hits = []
    for root, _, files in os.walk(d):
        hits += [os.path.join(root, f) for f in files if f.endswith(".gguf")]
    if not hits:
        raise SystemExit(f"no gguf under {d}")
    return sorted(hits)[0]

MODELS = {
    "gpt-oss-20b": {"path": find_gguf("/workspace/models/gpt-oss"),
        "samplers": {"temperature": 1.0, "top_p": 1.0, "top_k": 0}},
    "flash-q4": {"path": find_gguf("/workspace/models/flash-q4"),
        "samplers": {"temperature": 1.0, "top_p": 0.95, "min_p": 0.01, "repeat_penalty": 1.0}},
    "reap-iq4xs": {"path": find_gguf("/workspace/models/reap-iq4xs"),
        "samplers": {"temperature": 1.0, "top_p": 0.95, "min_p": 0.01, "repeat_penalty": 1.0}},
}

PROMPTS = [
("c1", """Write a Python function merge_intervals(intervals) that merges overlapping or touching intervals. Input: a list of [start, end] pairs in any order. Return the merged list sorted by start. Handle empty input. After the function, include exactly 5 assert test cases covering: empty list, single interval, touching intervals like [1,2] and [2,3], fully nested intervals, and unsorted input."""),
("c2", """Find every bug in this Python function, explain each one, and provide a corrected version:

def add_item(item, inventory={}):
    if item not in inventory:
        inventory[item] = 0
    inventory[item] =+ 1
    return inventory"""),
("c3", """PostgreSQL. Tables: orders(id, customer_id, amount numeric, created_at timestamptz) and customers(id, name). Write one query returning, for each calendar month of 2025, the top 3 customers by total order amount in that month, including ties at rank 3. Columns: month, customer name, total, rank. Use a window function."""),
("c4", """Using Python asyncio and aiohttp, write fetch_all(urls) that fetches a list of URLs with at most 5 requests in flight at any time, a 10-second timeout per request, and returns a dict mapping each url to either its response body or the string 'ERROR: <reason>'. One failure must not cancel the other requests. Include brief comments explaining the concurrency control."""),
("c5", """Implement an LRU cache class in Python with get(key) and put(key, value) in O(1), capacity set at init. Do not use OrderedDict, functools, or any imports - plain dict plus your own doubly linked list. After the class, add a short demo proving the eviction order is correct, with comments stating the expected output."""),
("r1", """Four friends - Ana, Ben, Cal, Dee - each own a different pet (cat, dog, fish, hawk) and live on different floors (1-4) of the same building. Clues: 1) Ana lives directly above the dog owner. 2) The fish owner lives on floor 1. 3) Cal lives on floor 3 and does not own the hawk. 4) Ben owns the cat. 5) Dee does not live on floor 2. Determine who owns which pet and lives on which floor. Show your deduction steps, then state the final answer clearly."""),
("r2", """Pump A fills a tank in 6 hours, pump B fills it in 4 hours, and drain C empties it in 12 hours. The tank starts one quarter full and all three are opened at once. Exactly how long until the tank is full? Give the answer as an exact fraction of an hour, with work shown."""),
("r3", """A disease affects 1 in 1,000 people. A test has 99% sensitivity and 95% specificity. A randomly screened person tests positive. What is the probability they actually have the disease? Show the calculation and give the final answer as a percentage to one decimal place."""),
("r4", """On an island, knights always tell the truth and knaves always lie. A says: 'B is a knave.' B says: 'A and C are the same type.' C says: 'B is a knight.' Determine the type of each person. Show that your answer is the only consistent one."""),
("r5", """Define f(n) = n/2 if n is even, and 3n + 5 if n is odd. Starting from 7, repeatedly apply f and write out the sequence of values. Does the sequence enter a cycle? If yes, list the full cycle and state the step at which it is first entered. Show every arithmetic step."""),
]

os.makedirs(OUT, exist_ok=True)
labels = ["A", "B", "C"]
names = list(MODELS); random.shuffle(names)
key = dict(zip(labels, names))
with open(f"{OUT}/key.txt", "w") as f:
    for l, n in key.items(): f.write(f"{l} = {n}\n")

def wait_health():
    for _ in range(240):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            return True
        except Exception:
            time.sleep(2)
    return False

for label in labels:
    cfg = MODELS[key[label]]
    print(f"=== model {label}: loading ===", flush=True)
    srv = subprocess.Popen([LLAMA, "-m", cfg["path"], "-ngl", "999", "-c", "16384",
        "--jinja", "--port", str(PORT), "--host", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not wait_health():
        srv.terminate(); raise SystemExit(f"server for {label} never came up")
    with open(f"{OUT}/answers_{label}.md", "w") as out:
        for pid, prompt in PROMPTS:
            body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                "max_tokens": 8192, **cfg["samplers"]}).encode()
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                data=body, headers={"Content-Type": "application/json"})
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=900) as r:
                    msg = json.loads(r.read())["choices"][0]["message"]
                ans = (msg.get("content") or "").strip()
                if "</think>" in ans: ans = ans.split("</think>")[-1].strip()
            except Exception as e:
                ans = f"[RUN ERROR: {e}]"
            out.write(f"## {pid}\n\n{ans}\n\n---\n\n"); out.flush()
            print(f"{label} {pid} done in {time.time()-t0:.0f}s", flush=True)
    srv.terminate(); srv.wait(); time.sleep(5)

print("ALL DONE - answers in answers_A.md / B / C. Do NOT open key.txt until grades are in.")
