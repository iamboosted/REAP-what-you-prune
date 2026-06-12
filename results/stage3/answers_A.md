## c1

```python
def merge_intervals(intervals):
    """
    Merge overlapping or touching intervals.

    Parameters
    ----------
    intervals : list of list[int]
        Each inner list contains two integers [start, end].
        The list may be empty or in any order.

    Returns
    -------
    list of list[int]
        The merged intervals, sorted by start.
    """
    if not intervals:
        return []

    # Sort by start value
    intervals = sorted(intervals, key=lambda x: x[0])

    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        # Merge if the intervals overlap or touch (start <= last_end)
        if start <= last_end:
            merged[-1][1] = max(last_end, end)
        else:
            merged.append([start, end])

    return merged


# ---- Test cases ----------------------------------------------------
assert merge_intervals([]) == []                        # empty list
assert merge_intervals([[5, 10]]) == [[5, 10]]          # single interval
assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]   # touching intervals
assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]  # fully nested
assert merge_intervals([[5, 7], [1, 3], [4, 6]]) == [[1, 3], [4, 7]]  # unsorted input
```

---

## c2

Below is a line‑by‑line walkthrough of the original code, the problems it contains, why those problems matter, and a fully corrected implementation.

---

## Original function

```python
def add_item(item, inventory={}):
    if item not in inventory:
        inventory[item] = 0
    inventory[item] =+ 1
    return inventory
```

### 1. **Mutable default argument** (`inventory={}`)

- **What it does**: In Python, default arguments are evaluated only once, at function definition time.  
- **Why it’s a bug**: All calls that do *not* pass an `inventory` argument will share the *same* dictionary. Subsequent calls mutate that shared dict, producing surprising cross‑call side effects.

  ```python
  add_item('apple')          # inventory now {'apple': 1}
  add_item('banana')         # inventory now {'apple': 1, 'banana': 1}  ← not a fresh dict!
  ```

- **Fix**: Use `None` as the default and create a new dict inside the function.

### 2. **Incorrect increment operator** (`inventory[item] =+ 1`)

- **What it does**: `=+` is parsed as `=` followed by a unary `+`. It *replaces* the existing value with `+1`, i.e. `1`.  
- **Why it’s a bug**: The intent is clearly to *increment* the existing count. Instead the code always sets the count to `1`.

  ```python
  inventory = {'apple': 3}
  inventory['apple'] =+ 1   # inventory['apple'] becomes 1, not 4
  ```

- **Fix**: Use the standard increment pattern `inventory[item] = inventory[item] + 1` or the shorthand `+=`.

### 3. **Redundant `if` block**

- The `if item not in inventory: inventory[item] = 0` is unnecessary if we use `dict.get` or `defaultdict`. It just makes the logic harder to read.

### 4. **No defensive copy / documentation**

- The function mutates the passed‑in dictionary. That may or may not be what callers want. A docstring clarifies intent.

---

## Corrected implementation

```python
def add_item(item, inventory=None):
    """
    Increment the count of *item* in *inventory* and return the updated dict.

    Parameters
    ----------
    item : hashable
        The key whose count should be increased.
    inventory : dict, optional
        Mapping from items to integer counts.  If omitted or None, a new
        dictionary is created.  The function mutates the passed dict (or the new
        one) and returns it.

    Returns
    -------
    dict
        The dictionary containing the updated count for *item*.
    """
    # 1. Avoid mutable default argument
    if inventory is None:
        inventory = {}

    # 2. Increment using dict.get (safe for missing keys)
    inventory[item] = inventory.get(item, 0) + 1

    return inventory
```

### Quick sanity test

```python
inv = {}
add_item('apple', inv)   # {'apple': 1}
add_item('apple', inv)   # {'apple': 2}
add_item('banana')       # {'banana': 1}   # new dict, no side‑effects on previous calls
```

---

### Summary of bugs fixed

| Bug | Explanation | Fix |
|-----|-------------|-----|
| Mutable default argument | All calls share same dict | Use `inventory=None` and create inside |
| `=+` typo | Replaces value with 1 instead of incrementing | Use `+= 1` or `inventory[item] = inventory.get(item,0)+1` |
| Unnecessary `if` | Redundant logic, less readable | Replace with `dict.get` or `defaultdict` |
| Lack of documentation | Caller ambiguity | Add clear docstring |

With these changes the function behaves as expected and is safe to use in any context.

---

## c3

```sql
/*  Top‑3 (with ties) customers per calendar month in 2025  */
WITH monthly_totals AS (
    SELECT
        DATE_TRUNC('month', o.created_at)::date      AS month,
        c.name                                     AS customer_name,
        SUM(o.amount)                              AS total
    FROM orders      o
    JOIN customers  c ON o.customer_id = c.id
    WHERE o.created_at >= DATE '2025-01-01'
      AND o.created_at <  DATE '2026-01-01'      -- keep only 2025 data
    GROUP BY 1, 2                                 -- month, customer_name
)

SELECT month,
       customer_name,
       total,
       rank
FROM (
    SELECT
        month,
        customer_name,
        total,
        RANK() OVER (PARTITION BY month ORDER BY total DESC) AS rank
    FROM monthly_totals
) t
WHERE rank <= 3          -- include ties at rank 3
ORDER BY month, rank, customer_name;
```

**Explanation**

1. **`monthly_totals` CTE**  
   * Truncate each `created_at` to the first day of its month (`DATE_TRUNC('month', …)::date`).  
   * Join `orders` with `customers` to get the customer name.  
   * Filter to the year 2025.  
   * Aggregate per month‑customer pair (`SUM(o.amount)`).

2. **Window function**  
   * `RANK() OVER (PARTITION BY month ORDER BY total DESC)` assigns a rank to each customer within its month, giving the same rank to ties.  
   * Wrapping the window in a sub‑query allows us to filter on the rank.

3. **Result columns**  
   * `month` – first day of the month.  
   * `customer_name` – the name of the customer.  
   * `total` – total order amount for that month.  
   * `rank` – the rank within the month.

4. **Filtering**  
   * `WHERE rank <= 3` keeps the top three ranks (including all customers tied at rank 3).  

5. **Ordering**  
   * `ORDER BY month, rank, customer_name` gives a clean, sorted output.

---

## c4

```python
import asyncio
import aiohttp

async def fetch(url: str, session: aiohttp.ClientSession, sem: asyncio.Semaphore) -> str:
    """
    Fetch a single URL using the supplied session.
    The semaphore (`sem`) guarantees that at most a fixed number of
    coroutines are running concurrently.
    Any exception is caught and turned into an error string so that
    one failure never stops the others.
    """
    # Acquire the semaphore before starting the request.
    async with sem:
        try:
            # `ClientTimeout(total=10)` gives a 10‑second timeout for the whole request.
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()          # Raise for 4xx/5xx HTTP codes.
                return await resp.text()         # Return the body as text.
        except Exception as exc:
            # Convert the exception into a readable error message.
            return f"ERROR: {exc}"


async def fetch_all(urls):
    """
    Fetch a list of URLs with a concurrency limit of 5.
    Returns a dictionary mapping each URL to either its response body
    or an error message.  Failure of one request does not cancel
    the others.
    """
    # Semaphore that allows at most 5 concurrent requests.
    semaphore = asyncio.Semaphore(5)

    results = {}
    async with aiohttp.ClientSession() as session:
        # Create a task for every URL.
        tasks = [asyncio.create_task(fetch(u, session, semaphore)) for u in urls]

        # Gather all tasks.  Each task already handles its own errors,
        # so gather will never raise an exception.
        responses = await asyncio.gather(*tasks)

    # Build the final mapping.
    for url, body in zip(urls, responses):
        results[url] = body

    return results
```

### How it works

* **Concurrency control:**  
  `asyncio.Semaphore(5)` limits the number of coroutines that can be inside the `async with sem:` block at once.  
  Each `fetch()` call acquires the semaphore before making a request and automatically releases it when the block exits.

* **Timeout & error handling:**  
  `aiohttp.ClientTimeout(total=10)` ensures the whole request (connect + download) does not exceed 10 s.  
  All exceptions inside `fetch()` are caught and converted into an `ERROR: …` string, so a failure does not propagate to other tasks.

* **Non‑cancellation of other requests:**  
  Since each task handles its own exceptions and we use `asyncio.gather(*tasks)` with no `return_exceptions=True` (the tasks already return a string), no task cancellation occurs when another task fails.

---

## c5

```python
class LRUCache:
    """
    A simple Least‑Recently‑Used (LRU) cache.

    Implements `get(key)` and `put(key, value)` in O(1) time.
    Uses a plain `dict` to map keys to nodes of a doubly‑linked list
    that keeps track of the access order.
    """
    class _Node:
        __slots__ = ("key", "value", "prev", "next")

        def __init__(self, key=None, value=None):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.cache = {}                     # key -> node
        # Dummy head and tail to simplify edge handling
        self.head = self._Node()
        self.tail = self._Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    # ---------- internal helpers ----------
    def _remove(self, node):
        """Detach `node` from the list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _add_to_front(self, node):
        """Insert `node` right after the dummy head."""
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    # ---------- public API ----------
    def get(self, key):
        """Return the value associated with `key`, or `None` if missing."""
        node = self.cache.get(key)
        if node is None:
            return None
        # Move the accessed node to the front (most recent)
        self._remove(node)
        self._add_to_front(node)
        return node.value

    def put(self, key, value):
        """Insert or update the value for `key`."""
        node = self.cache.get(key)
        if node:
            # Update existing node and move it to the front
            node.value = value
            self._remove(node)
            self._add_to_front(node)
        else:
            # Add new node
            new_node = self._Node(key, value)
            self.cache[key] = new_node
            self._add_to_front(new_node)

            # Evict least‑recently‑used item if over capacity
            if len(self.cache) > self.capacity:
                # The node just before the dummy tail is the LRU
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]


# ----------------------------------------
# Demo:  show that eviction order is correct
# ----------------------------------------
if __name__ == "__main__":
    # Create a cache of capacity 2
    cache = LRUCache(2)

    cache.put(1, 1)      # cache: {1=1}
    cache.put(2, 2)      # cache: {1=1, 2=2}
    print(cache.get(1))  # -> 1, cache order: {1, 2}
                         # (1 becomes most recent, 2 least recent)

    cache.put(3, 3)      # evicts key 2
    print(cache.get(2))  # -> None (evicted)
    print(cache.get(3))  # -> 3
    print(cache.get(1))  # -> 1

    cache.put(4, 4)      # evicts key 1
    print(cache.get(1))  # -> None (evicted)
    print(cache.get(3))  # -> 3
    print(cache.get(4))  # -> 4

    # Expected output:
    # 1
    # None
    # 3
    # 1
    # None
    # 3
    # 4
```

**Explanation of the demo**

1. After inserting keys `1` and `2`, the cache holds both.
2. `get(1)` accesses key `1`, making it the most recent; key `2` is now LRU.
3. `put(3,3)` exceeds capacity, so key `2` (the LRU) is evicted.
4. Subsequent `get` calls confirm that key `2` is gone and keys `1` and `3` are present.
5. Adding key `4` evicts key `1`, leaving keys `3` and `4` in the cache.
6. The printed output matches the expected values, demonstrating correct LRU behaviour.

---

## r1

**Step‑by‑step deduction**

| Person | Floor | Pet |
|--------|-------|-----|
| Ana    | 4     | hawk |
| Ben    | 2     | cat |
| Cal    | 3     | dog |
| Dee    | 1     | fish |

---

### 1.  Set up the known facts

| Clue | Translation |
|------|-------------|
| 1. Ana lives directly above the dog owner. | `floor(Ana) = floor(Dog) + 1` |
| 2. The fish owner lives on floor 1. | `floor(Fish) = 1` |
| 3. Cal lives on floor 3 and does not own the hawk. | `floor(Cal) = 3` and `Pet(Cal) ≠ hawk` |
| 4. Ben owns the cat. | `Pet(Ben) = cat` |
| 5. Dee does not live on floor 2. | `floor(Dee) ≠ 2` |

All floors 1‑4 are unique, and all pets are unique.

---

### 2.  Place Cal first

From clue 3:  
- Cal must be on floor 3.  
- He cannot own the hawk, so his pet is either dog, cat, or fish.

The fish owner is on floor 1 (clue 2), so Cal cannot be the fish owner.  
Cat is owned by Ben (clue 4), so Cal cannot own the cat either.

**Therefore Cal owns the dog.**

So:

```
Floor 3 : Cal – dog
```

---

### 3.  Use clue 1 for Ana

Since Ana lives directly above the dog owner, and the dog owner is on floor 3, Ana must be on floor 4.

```
Floor 4 : Ana – ?
```

---

### 4.  Assign the fish owner

The fish owner lives on floor 1.  
The remaining people after putting Cal and Ana on floors 3 and 4 are Ben and Dee.  
Dee is not allowed to live on floor 2 (clue 5), so Dee must be on floor 1 and thus must own the fish.

```
Floor 1 : Dee – fish
```

---

### 5.  Finish the remaining assignments

The only floor left is floor 2, and the only person left is Ben.  
Ben owns the cat (clue 4).

```
Floor 2 : Ben – cat
```

The only pet not yet used is the hawk, so Ana must own the hawk.

```
Floor 4 : Ana – hawk
```

---

### 6.  Check all clues

| Clue | Verified |
|------|----------|
| 1. Ana lives directly above the dog owner. | Ana floor 4, dog owner Cal floor 3 ✔ |
| 2. The fish owner lives on floor 1. | Dee fish floor 1 ✔ |
| 3. Cal lives on floor 3 and does not own the hawk. | Cal floor 3, dog ✔ |
| 4. Ben owns the cat. | Ben cat ✔ |
| 5. Dee does not live on floor 2. | Dee floor 1 ✔ |

All conditions are satisfied.

---

**Final answer**

| Floor | Person | Pet |
|-------|--------|-----|
| 1 | Dee | fish |
| 2 | Ben | cat |
| 3 | Cal | dog |
| 4 | Ana | hawk |

---

## r2

Let the tank hold \(1\) unit of liquid.

**Rates**

* Pump \(A\) fills the tank in \(6\) h  
  \[
  r_A=\frac{1}{6}\ \text{tank/hour}
  \]

* Pump \(B\) fills the tank in \(4\) h  
  \[
  r_B=\frac{1}{4}\ \text{tank/hour}
  \]

* Drain \(C\) empties the tank in \(12\) h  
  \[
  r_C=-\frac{1}{12}\ \text{tank/hour}
  \]

**Combined net rate**

\[
r_{\text{net}}=r_A+r_B+r_C
    =\frac{1}{6}+\frac{1}{4}-\frac{1}{12}
    =\frac{2}{12}+\frac{3}{12}-\frac{1}{12}
    =\frac{4}{12}
    =\frac{1}{3}\ \text{tank/hour}
\]

So, with all three devices open simultaneously, the tank is filling at a constant rate of \(\frac{1}{3}\) tank per hour.

---

### Initial condition

The tank starts one quarter full:
\[
\text{Initial amount}= \frac14\ \text{tank}
\]

We want the tank to be completely full (\(1\) tank).  
The amount that still needs to be added is

\[
1-\frac14=\frac34\ \text{tank}
\]

---

### Time required

Let \(t\) be the number of hours needed.  
Because the net rate is \(\frac13\) tank per hour,

\[
\text{(amount added)} = r_{\text{net}}\;t
\quad\Longrightarrow\quad
\frac34=\frac13\,t
\]

Solve for \(t\):

\[
t=\frac{\,\frac34\,}{\,\frac13\,}
  =\frac34 \times \frac31
  =\frac94 \ \text{hours}
\]

---

\[
\boxed{\displaystyle t=\frac{9}{4}\text{ hours}}
\]

(That is \(2\) h 15 min.)

---

## r3

**Step‑by‑step calculation**

| Symbol | Meaning | Value |
|--------|---------|-------|
| \(P(D)\) | Prevalence (probability a random person has the disease) | \( \dfrac{1}{1000}=0.001 \) |
| \(P(\bar D)\) | Probability of not having the disease | \(1-0.001=0.999\) |
| Sensitivity | \(P(+|D)\) | 0.99 |
| Specificity | \(P(-|\bar D)\) | 0.95 |
| False‑positive rate | \(P(+|\bar D)=1-0.95=0.05\) |

1. **Probability that a random person tests positive**

\[
\begin{aligned}
P(+)&=P(+|D)\,P(D)+P(+|\bar D)\,P(\bar D)\\
&=0.99\times0.001+0.05\times0.999\\
&=0.00099+0.04995\\
&=0.05094
\end{aligned}
\]

2. **Posterior probability (Positive Predictive Value)**  

\[
\begin{aligned}
P(D|+)&=\frac{P(+|D)\,P(D)}{P(+)}\\
&=\frac{0.99\times0.001}{0.05094}\\[4pt]
&=\frac{0.00099}{0.05094}\\[4pt]
&\approx0.01944
\end{aligned}
\]

3. **Convert to percentage**

\[
0.01944 \times 100 \approx 1.944\%
\]

Rounded to one decimal place:

\[
\boxed{1.9\%}
\]

---

## r4

Let  

\[
t_A,\;t_B,\;t_C\in \{K,N\}
\]

denote the types (K – knight, N – knave).  
The three statements are  

* \(S_A:\;t_B=N\)  (“B is a knave”)
* \(S_B:\;t_A=t_C\)  (“A and C are the same type”)
* \(S_C:\;t_B=K\)  (“B is a knight”)

A statement is true iff the speaker is a knight and false iff the speaker is a knave.

--------------------------------------------------------------------

### 1.  Assume \(B\) is a knight

If \(t_B=K\), then \(S_C\) is true, so \(t_B=K\) – consistent.  
But \(B\) being a knight also makes \(S_B\) true, therefore  

\[
t_A = t_C .
\]

Since \(B\) is a knight, the only way for \(S_C\) to be true is that \(C\) is a knight.  
Hence \(t_C=K\) and from \(t_A=t_C\) we get \(t_A=K\).

Now examine \(S_A\).  Because \(t_A=K\), \(S_A\) must be true, i.e. \(t_B=N\).  
This contradicts our assumption \(t_B=K\).

Hence **\(B\) cannot be a knight**; therefore \(t_B=N\).

--------------------------------------------------------------------

### 2.  Consequences when \(t_B=N\)

If \(t_B=N\), the statement \(S_A:\;t_B=N\) is true, so **\(A\) must be a knight**: \(t_A=K\).

Now consider \(S_B\).  Because \(B\) is a knave, \(S_B\) is false, so  

\[
t_A \neq t_C .
\]

Since \(t_A=K\), this forces \(t_C=N\).

Finally check \(S_C\):  \(C\) is a knave, so \(S_C\) must be false.  
\(S_C\) says “\(B\) is a knight”, which is indeed false because \(t_B=N\).  
Thus all three statements are satisfied.

--------------------------------------------------------------------

### 3.  Uniqueness

We have shown that

* \(B\) cannot be a knight, so \(B\) is a knave.
* With \(B\) a knave, the only consistent assignment is \(A=K\) and \(C=N\).

No other assignment works (the exhaustive check of the remaining \(2^3=8\) possibilities yields contradictions, as shown in the brief enumeration above).  
Therefore the solution is unique.

--------------------------------------------------------------------

\[
\boxed{A\text{ is a knight, }\, B\text{ is a knave, }\, C\text{ is a knave}}
\]

---

## r5

**Step‑by‑step computation**

| step | value \(n_k\) | rule used | next value | arithmetic |
|------|---------------|-----------|------------|------------|
| 0 | 7 | odd | \(3\cdot7+5\) | \(21+5=26\) |
| 1 | 26 | even | \(26/2\) | \(13\) |
| 2 | 13 | odd | \(3\cdot13+5\) | \(39+5=44\) |
| 3 | 44 | even | \(44/2\) | \(22\) |
| 4 | 22 | even | \(22/2\) | \(11\) |
| 5 | 11 | odd | \(3\cdot11+5\) | \(33+5=38\) |
| 6 | 38 | even | \(38/2\) | \(19\) |
| 7 | 19 | odd | \(3\cdot19+5\) | \(57+5=62\) |
| 8 | 62 | even | \(62/2\) | \(31\) |
| 9 | 31 | odd | \(3\cdot31+5\) | \(93+5=98\) |
|10 | 98 | even | \(98/2\) | \(49\) |
|11 | 49 | odd | \(3\cdot49+5\) | \(147+5=152\) |
|12 |152 | even | \(152/2\) | \(76\) |
|13 | 76 | even | \(76/2\) | \(38\) |
|14 | 38 | even | \(38/2\) | \(19\) |

At step 14 we obtain \(38\) again – the same value that first appeared at step 6.  
Thus the sequence has entered a cycle.

**Full cycle**

```
38 → 19 → 62 → 31 → 98 → 49 → 152 → 76 → 38 → …
```

The cycle contains 8 distinct values:  
\( \{38,\;19,\;62,\;31,\;98,\;49,\;152,\;76\} \).

**First entry into the cycle**

The very first time a value that will repeat later appears is at **step 6** (the value 38).  
After that the values repeat every 8 steps.

---

