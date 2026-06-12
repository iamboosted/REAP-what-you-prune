## c1

```python

def merge_intervals(intervals):
    """
    Merges overlapping or touching intervals and returns a sorted list of merged intervals.
    
    Args:
        intervals: List of [start, end] pairs (inclusive), can be unsorted and empty.
        
    Returns:
        List of merged intervals sorted by start.
    """
    if not intervals:
        return []

    # Sort intervals by start time
    intervals_sorted = sorted(intervals, key=lambda x: x[0])

    merged = []
    current_start, current_end = intervals_sorted[0]

    for start, end in intervals_sorted[1:]:
        # Overlap or touching? (touching if start == current_end)
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append([current_start, current_end])
            current_start, current_end = start, end

    # Append the last interval
    merged.append([current_start, current_end])
    return merged


# Test cases
assert merge_intervals([]) == [], "Empty list test"
assert merge_intervals([[1, 5]]) == [[1, 5]], "Single interval test"
assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]], "Touching intervals test"
assert merge_intervals([[1, 4], [2, 3]]) == [[1, 4]], "Fully nested intervals test"
assert merge_intervals([[4, 5], [1, 2], [2, 3]]) == [[1, 5]], "Unsorted input test"

```

---

## c2

Here are the bugs found in the function, followed by the corrected version.

### Bug 1: Mutable Default Argument
**The Issue:**
```python
def add_item(item, inventory={}):
```
In Python, default arguments are evaluated only once when the function is defined, not every time the function is called. By setting the default value to an empty dictionary `{}`, you create a single dictionary object that persists across all calls to the function.

**The Consequence:**
If you call `add_item("apple")` and then `add_item("banana")`, both calls modify the *same* dictionary in memory. The function will not reset the inventory between calls, causing counts to accumulate unexpectedly or data to leak between different operations.

### Bug 2: Incorrect Increment Operator
**The Issue:**
```python
inventory[item] =+ 1
```
This is a common syntax mistake. The operator `=+` is treated by the parser as a unary plus applied to the right-hand side, resulting in `+1` (which is just `1`), followed by an assignment.

**The Consequence:**
This line does **not** add 1 to the current value. Instead, it replaces the current value with `1`. This means if you try to add "apple" a second time, the count resets to 1 instead of increasing to 2. The correct operator for addition is `+=`.

---

### Corrected Version

To fix this, we should pass `None` as the default argument and initialize the dictionary inside the function if it doesn't exist. We also change the increment operator to `+=`.

```python
def add_item(item, inventory=None):
    # Initialize the dictionary if it hasn't been passed in yet
    if inventory is None:
        inventory = {}
    
    # Check if the item exists to handle initialization logic cleanly
    if item not in inventory:
        inventory[item] = 0
        
    # Use += to correctly increment the value
    inventory[item] += 1
    
    return inventory
```

### Alternative (Best Practice) Approach
A slightly more Pythonic version uses the `.get()` method or `collections.defaultdict`, but the version above is the closest fix to the original code's logic.

```python
def add_item(item, inventory=None):
    if inventory is None:
        inventory = {}
    # Sets value to 0 if it doesn't exist, or returns the current value if it does
    inventory[item] = inventory.get(item, 0) + 1
    return inventory
```

---

## c3

Here is the PostgreSQL query. It uses Common Table Expressions (CTEs) to first aggregate the data and calculate the rank, then filters for the "Top 3 including ties" using the logic that everyone with an amount equal to the person ranked 3rd should be included.

```sql
WITH monthly_totals AS (
    SELECT
        TO_CHAR(o.created_at, 'YYYY-MM') AS month,
        c.name,
        SUM(o.amount) AS total
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE EXTRACT(YEAR FROM o.created_at) = 2025
    GROUP BY 1, 2
),
ranked_data AS (
    SELECT
        month,
        name,
        total,
        RANK() OVER (PARTITION BY month ORDER BY total DESC) AS rank
    FROM monthly_totals
),
rank_3_cutoff AS (
    SELECT
        month,
        total AS third_place_amount
    FROM ranked_data
    WHERE RANK() OVER (PARTITION BY month ORDER BY total DESC) = 3
)
SELECT
    r.month,
    r.name,
    r.total,
    r.rank
FROM ranked_data r
JOIN rank_3_cutoff c ON r.month = c.month
WHERE r.rank <= 3
ORDER BY r.month, r.rank;
```

### Explanation of Logic
1.  **`monthly_totals`**: Aggregates the total amount per customer for each month of 2025.
2.  **`ranked_data`**: Applies the window function `RANK()` (`PARTITION BY month`, `ORDER BY total DESC`) to assign each customer a rank within their specific month.
3.  **`rank_3_cutoff`**: Identifies the specific dollar amount of the customer who finished in the 3rd position for that month.
4.  **Final Select**: Joins the ranked data back with the cutoff amounts. It includes rows where `rank <= 3` AND `total >= third_place_amount`. This ensures that if Customer A has \$1000, Customer B has \$900, and Customer C has \$900, Customer C is included (because they tie for the cutoff amount of the 3rd place finisher).

---

## c4

```python
import asyncio
import aiohttp

async def fetch_all(urls):
    """
    Fetch a list of URLs concurrently, respecting these constraints:
    - At most 5 requests are in flight at any time.
    - Each request has a 10-second timeout.

    Returns a dict mapping each URL to its response body (if successful)
    or to an error string of the form 'ERROR: <reason>'.
    """
    # Configure a session with a 10-second timeout for every request.
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Semaphore to limit the number of active requests to at most 5.
        semaphore = asyncio.Semaphore(5)

        async def fetch_one(url: str):
            """Fetch a single URL, respecting the semaphore and timeout."""
            result = None
            async with semaphore:
                try:
                    # The ClientSession timeout ensures the whole request finishes within 10s.
                    async with session.get(url) as response:
                        result = await response.text()
                except Exception as e:
                    # Any error (timeout, HTTP error, network error, etc.) is caught.
                    result = f'ERROR: {e}'
            return result

        # Dispatch all tasks; the semaphore will keep only 5 tasks running at once.
        tasks = [asyncio.create_task(fetch_one(url)) for url in urls]
        # Wait for every task to complete and collect results.
        results = await asyncio.gather(*tasks)

        # Build the final dictionary: URL -> result.
        return {url: result for url, result in zip(urls, results)}
```

---

## c5

```python

class Node:
    """Doubly linked list node for the LRU cache."""
    def __init__(self, key: int, value: int):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    """LRU cache implementation using a doubly linked list and a dictionary."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}                     # maps key -> node
        # Dummy head and tail simplify insertion/removal
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: Node) -> None:
        """Remove a node from the doubly linked list."""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _add(self, node: Node) -> None:
        """Insert a node right after the dummy head (most recent position)."""
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def _move_to_head(self, node: Node) -> None:
        """Move an existing node to the most recently used position."""
        self._remove(node)
        self._add(node)

    def get(self, key: int) -> int:
        """Return value if key exists, else -1."""
        if key in self.cache:
            node = self.cache[key]
            self._move_to_head(node)
            return node.value
        return -1

    def put(self, key: int, value: int) -> None:
        """Insert or update a key-value pair. Evicts the LRU entry if capacity is full."""
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._move_to_head(node)
        else:
            if len(self.cache) == self.capacity:
                # Evict the least recently used node (the one before the dummy tail)
                lru_node = self.tail.prev
                self._remove(lru_node)
                del self.cache[lru_node.key]
            new_node = Node(key, value)
            self._add(new_node)
            self.cache[key] = new_node


# ==========================================
# Demonstration of correct eviction order
# ==========================================
if __name__ == "__main__":
    cache = LRUCache(2)

    # Expected: cache after each step
    # 1) put(1,1) -> {1:1} (most recent: 1)
    # 2) put(2,2) -> {1:1,2:2} (most recent: 2)
    # 3) get(1)   -> returns 1, order becomes {2:2,1:1} (most recent: 1)
    # 4) put(3,3) -> evicts key 2, cache {1:1,3:3} (most recent: 3)
    # 5) get(2)   -> returns -1 (not present)
    # 6) get(3)   -> returns 3
    # 7) put(4,4) -> evicts key 1, cache {3:3,4:4} (most recent: 4)
    # 8) get(1)   -> returns -1
    # 9) get(3)   -> returns 3
    # 10) get(4)  -> returns 4

    cache.put(1, 1)
    cache.put(2, 2)
    print(cache.get(1))   # expected: 1
    cache.put(3, 3)      # evicts key 2
    print(cache.get(2))   # expected: -1
    print(cache.get(3))   # expected: 3
    cache.put(4, 4)      # evicts key 1
    print(cache.get(1))   # expected: -1
    print(cache.get(3))   # expected: 3
    print(cache.get(4))   # expected: 4

```

---

## r1

Here are the deduction steps to solve the puzzle:

**1. Analyze the Constraints:**
*   **People:** Ana, Ben, Cal, Dee
*   **Pets:** Cat, Dog, Fish, Hawk
*   **Floors:** 1, 2, 3, 4

**2. Apply the Clues:**

*   **Clue 3:** Cal lives on floor 3 and does not own the hawk.
    *   *Fact:* Cal = Floor 3.
    *   *Fact:* Cal $\neq$ Hawk.

*   **Clue 4:** Ben owns the cat.
    *   *Fact:* Ben = Cat.

*   **Clue 2:** The fish owner lives on floor 1.
    *   *Fact:* Floor 1 = Fish.

*   **Clue 5:** Dee does not live on floor 2.

**3. Logical Deductions:**

*   **Step A: Determine Cal's pet.**
    *   Ben owns the Cat, and Cal does not own the Hawk (Clue 3).
    *   Therefore, Cal must own the **Dog**.
    *   *Current Status:* Cal (Floor 3) owns the Dog.

*   **Step B: Determine Ana's pet and floor.**
    *   We know Ben has the Cat, Cal has the Dog, and the Fish is on Floor 1.
    *   The only pet left for Ana is the **Hawk**.
    *   Clue 1 says: "Ana lives directly above the dog owner."
    *   Since Cal (the dog owner) lives on Floor 3, Ana must live on the floor directly above it, which is **Floor 4**.

*   **Step C: Determine who lives on Floor 1.**
    *   The Fish owner lives on Floor 1.
    *   We know Ben owns the Cat, so he cannot be on Floor 1 (because the person on Floor 1 owns the Fish).
    *   We know Cal is on Floor 3 and Ana is on Floor 4.
    *   This leaves Ben and Dee for Floors 1 and 2.
    *   Clue 5 says Dee does not live on Floor 2.
    *   Therefore, **Dee** lives on **Floor 1** (and owns the Fish).
    *   Consequently, **Ben** must live on **Floor 2** (and owns the Cat).

**4. Final Verification:**
*   Ana (Floor 4) owns the Hawk. Does she live above the dog owner? Yes, above Cal (Floor 3).
*   Fish owner is on Floor 1. Yes, it's Dee.
*   Cal is on Floor 3 and does not own the Hawk (owns Dog). Yes.
*   Ben owns the Cat. Yes.
*   Dee does not live on Floor 2. Yes, she is on Floor 1.

**Final Answer:**

*   **Ana:** Hawk, Floor 4
*   **Ben:** Cat, Floor 2
*   **Cal:** Dog, Floor 3
*   **Dee:** Fish, Floor 1

---

## r2

The net filling rate when all three devices are operating is the sum of the rates of the filling pumps minus the emptying rate of the drain.

- Pump A fills at \(\frac{1}{6}\) tank per hour.
- Pump B fills at \(\frac{1}{4}\) tank per hour.
- Drain C empties at \(\frac{1}{12}\) tank per hour (negative contribution).

Combined rate:
\[
\frac{1}{6} + \frac{1}{4} - \frac{1}{12} = \frac{2}{12} + \frac{3}{12} - \frac{1}{12} = \frac{4}{12} = \frac{1}{3}\text{ tank per hour}.
\]

Initially the tank is \(\frac{1}{4}\) full. The volume needed to reach full is:
\[
1 - \frac{1}{4} = \frac{3}{4}\text{ tank}.
\]

The time required to fill this additional volume is:
\[
\text{time} = \frac{\text{volume needed}}{\text{rate}} = \frac{3/4}{1/3} = \frac{3}{4} \times 3 = \frac{9}{4}\text{ hours}.
\]

Thus, the tank will be full in exactly \(\frac{9}{4}\) hours.

\[
\boxed{\frac{9}{4}}
\]

---

## r3

To find the probability that a person actually has the disease given they tested positive, we use **Bayes' Theorem**.

Here are the given values:
*   **Prevalence (Disease Prevalence):** 1 in 1,000 ($P(\text{Disease}) = 0.001$)
*   **Sensitivity (True Positive Rate):** 99% ($P(\text{Positive} | \text{Disease}) = 0.99$)
*   **Specificity (True Negative Rate):** 95% ($P(\text{Negative} | \text{No Disease}) = 0.95$)

First, we determine the False Positive Rate, which is the probability of testing positive when you do *not* have the disease.
$$\text{False Positive Rate} = 1 - \text{Specificity} = 1 - 0.95 = 0.05$$

We also determine the probability of *not* having the disease.
$$P(\text{No Disease}) = 1 - P(\text{Disease}) = 1 - 0.001 = 0.999$$

Now, we apply Bayes' Theorem formula:
$$P(\text{Disease} | \text{Positive}) = \frac{P(\text{Positive} | \text{Disease}) \times P(\text{Disease})}{P(\text{Positive})}$$

**1. Calculate the Numerator (True Positives):**
$$\text{Numerator} = P(\text{Positive} | \text{Disease}) \times P(\text{Disease})$$
$$\text{Numerator} = 0.99 \times 0.001 = 0.00099$$

**2. Calculate the Denominator (Total Positives):**
The denominator is the total probability of getting a positive result, which includes both people with the disease who tested positive (True Positives) and people without the disease who tested positive (False Positives).
$$P(\text{Positive}) = [P(\text{Positive} | \text{Disease}) \times P(\text{Disease})] + [P(\text{Positive} | \text{No Disease}) \times P(\text{No Disease})]$$
$$P(\text{Positive}) = (0.99 \times 0.001) + (0.05 \times 0.999)$$
$$P(\text{Positive}) = 0.00099 + 0.04995$$
$$P(\text{Positive}) = 0.05094$$

**3. Final Calculation:**
$$P(\text{Disease} | \text{Positive}) = \frac{0.00099}{0.05094}$$
$$P(\text{Disease} | \text{Positive}) \approx 0.019445$$

**4. Convert to Percentage and Round:**
$$0.019445 \times 100 = 1.9445\%$$

Rounding to one decimal place, the probability is **1.9%**.

**Answer:** 1.9%

---

## r4

The only consistent assignment is:  
- **A is a knight** (always tells the truth).  
- **B is a knave** (always lies).  
- **C is a knave** (always lies).

### Proof  

Let \(K\) denote a knight and \(N\) a knave. The statements are:

- A says: “B is a knave.”
- B says: “A and C are the same type.”
- C says: “B is a knight.”

Consider the two possible truth values for A.

#### Case 1: A is a knight.  
Then A’s statement is true, so **B is a knave**.  
Since B is a knave, B’s statement is false: “A and C are the same type” is false, so A and C have different types.  
A is a knight, therefore C must be a knave.  
Now check C: C says “B is a knight.” B is a knave, so the statement is false, which is consistent because C is a knave.  
All statements are satisfied, so (A=K, B=N, C=N) works.

#### Case 2: A is a knave.  
Then A’s statement is false, so B is not a knave, i.e., **B is a knight**.  
Since B is a knight, his statement is true: “A and C are the same type.”  
A is a knave, so C must also be a knave.  
Now C is a knave, so his statement “B is a knight” must be false. But B is a knight, so the statement is true – a contradiction.  
Hence this case is impossible.

Since A can only be knight or knave, the first case is the only consistent possibility. Therefore the assignment is unique.

∎

---

## r5

The sequence starting from 7 is:

\[
\begin{array}{c|l|l}
\text{Step} & n & \text{Computation} \\
\hline
0 & 7 & \text{starting value} \\
1 & 26 & f(7)=3\cdot7+5=21+5=26 \\
2 & 13 & f(26)=26/2=13 \\
3 & 44 & f(13)=3\cdot13+5=39+5=44 \\
4 & 22 & f(44)=44/2=22 \\
5 & 11 & f(22)=22/2=11 \\
6 & 38 & f(11)=3\cdot11+5=33+5=38 \\
7 & 19 & f(38)=38/2=19 \\
8 & 62 & f(19)=3\cdot19+5=57+5=62 \\
9 & 31 & f(62)=62/2=31 \\
10 & 98 & f(31)=3\cdot31+5=93+5=98 \\
11 & 49 & f(98)=98/2=49 \\
12 & 152 & f(49)=3\cdot49+5=147+5=152 \\
13 & 76 & f(152)=152/2=76 \\
14 & 38 & f(76)=76/2=38
\end{array}
\]

The value 38 reappears at step 14, and from that point the sequence repeats the same eight values. Thus the sequence enters a cycle.

**Full cycle:**  
\[
38,\; 19,\; 62,\; 31,\; 98,\; 49,\; 152,\; 76
\]
(length 8).

**Step at which the cycle is first entered:** Step 6 (i.e., the 6th term of the sequence is 38, the first element of the cycle).

---

