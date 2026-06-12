## c1

```python

def merge_intervals(intervals):
    """
    Merge a list of intervals that are overlapping or touching.

    Args:
        intervals: List of [start, end] pairs (inclusive, any order).

    Returns:
        List of merged intervals sorted by start.
    """
    if not intervals:
        return []

    # Sort intervals by start
    intervals_sorted = sorted(intervals, key=lambda x: x[0])
    merged = []

    for start, end in intervals_sorted:
        # If merged is empty or the current interval starts after the last merged ends,
        # it is disjoint → add it as a new interval.
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            # Overlap or touching → extend the last merged interval if needed.
            merged[-1][1] = max(merged[-1][1], end)

    return merged


if __name__ == "__main__":
    # Test cases
    assert merge_intervals([]) == []
    assert merge_intervals([[1, 3]]) == [[1, 3]]
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]
    assert merge_intervals([[1, 6], [2, 3], [4, 5]]) == [[1, 6]]
    assert merge_intervals([[5, 7], [1, 3], [3, 6]]) == [[1, 7]]
    print("All test cases passed.")

```

---

## c2

Here are the bugs found in the function:

### 1. Mutable Default Argument (Shared State)
**The Code:** `def add_item(item, inventory={}):`

**The Bug:** This is one of the most common Python pitfalls. Default arguments are evaluated **only once** when the function is defined, not every time the function is called.
Because `inventory={}` is a mutable dictionary, this single dictionary object is created in memory when the module loads. If you call `add_item` multiple times, every call adds to the *same* dictionary object. This causes the state to persist across function calls unexpectedly.

### 2. Incorrect Arithmetic Operator
**The Code:** `inventory[item] =+ 1`

**The Bug:** This line intends to increment the count by 1, but the syntax is incorrect due to operator precedence.
In Python, the unary plus operator (`+`) has higher precedence than the assignment operator (`=`).
*   `inventory[item] =+ 1` is actually parsed as `inventory[item] = (+1)`.
*   This simply assigns the value `1` to the key, **overwriting** the previous value. It does not actually add 1 to the existing count.

---

### Corrected Version

To fix these issues, we must change the default argument to `None` and initialize the dictionary inside the function to ensure a new dictionary is created for every clean call. We also change the operator to `+=`.

```python
def add_item(item, inventory=None):
    # If inventory hasn't been set (or is the default None), create a new dict
    if inventory is None:
        inventory = {}
    
    # This handles initialization automatically for new items and increments correctly
    inventory[item] += 1
    
    return inventory
```

---

## c3

```sql
SELECT
    to_char(DATE_TRUNC('month', o.created_at), 'YYYY-MM') AS month,
    c.name AS "customer name",
    SUM(o.amount) AS total,
    RANK() OVER (
        PARTITION BY DATE_TRUNC('month', o.created_at)
        ORDER BY SUM(o.amount) DESC
    ) AS rank
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE EXTRACT(YEAR FROM o.created_at) = 2025
GROUP BY
    DATE_TRUNC('month', o.created_at),
    c.name
ORDER BY
    month,
    rank,
    total DESC;
```

---

## c4

```python

import asyncio
import aiohttp
from aiohttp import ClientTimeout

async def fetch_all(urls):
    """
    Asynchronously fetches all URLs, limiting concurrency to 5 requests at a time,
    and a timeout of 10 seconds per request. Returns a dict mapping each URL to
    its response body or an error message.
    """
    async def fetch(session, url, semaphore):
        try:
            # The semaphore ensures at most 5 concurrent requests.
            async with semaphore:
                # 10-second timeout per request.
                async with session.get(url, timeout=ClientTimeout(total=10)) as response:
                    # Assume successful request; HTTP errors are considered part of the body.
                    return (url, await response.text())
        except Exception as e:
            # Catch any failure (network errors, timeouts, etc.) and record the reason.
            return (url, f'ERROR: {e}')

    # Use a single session for all requests to improve performance.
    async with aiohttp.ClientSession() as session:
        # Limit the number of simultaneous requests.
        semaphore = asyncio.Semaphore(5)
        # Create a fetch coroutine for each URL; the semaphore controls concurrency.
        fetches = [fetch(session, url, semaphore) for url in urls]
        # Run all coroutines concurrently; results are returned in the order of the URLs.
        results = await asyncio.gather(*fetches)

    # Convert the list of (url, result) tuples into the desired dict.
    return {url: body_or_error for url, body_or_error in results}

```

---

## c5

```python
class LRUCache:
    """LRU cache implementation using a doubly linked list and a dictionary."""
    
    class Node:
        """Doubly linked list node."""
        __slots__ = ("key", "value", "prev", "next")
        
        def __init__(self, key=None, value=None):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
    
    def __init__(self, capacity):
        """Initialize the cache with given capacity."""
        self.capacity = capacity
        self.cache = {}                     # key -> Node
        self.head = self.Node()             # sentinel, most recent
        self.tail = self.Node()             # sentinel, least recent
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0
    
    def _remove_node(self, node):
        """Remove a node from the linked list."""
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _add_to_front(self, node):
        """Insert a node right after the head (most recent position)."""
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node
    
    def _move_to_front(self, node):
        """Move an existing node to the front (most recent)."""
        self._remove_node(node)
        self._add_to_front(node)
    
    def get(self, key):
        """Return the value for key if present, else -1. Updates usage."""
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._move_to_front(node)
        return node.value
    
    def put(self, key, value):
        """Insert or update the key with value. Evicts the least recently used
        when capacity is exceeded. No effect if capacity is zero."""
        if self.capacity == 0:
            return
        
        if key in self.cache:
            # Key exists: update value and move to front
            node = self.cache[key]
            node.value = value
            self._move_to_front(node)
            return
        
        # New key: evict if full
        if self.size == self.capacity:
            lru = self.tail.prev          # the least recently used node
            self._remove_node(lru)
            del self.cache[lru.key]
            self.size -= 1
        
        # Insert new node at the front
        new_node = self.Node(key, value)
        self.cache[key] = new_node
        self._add_to_front(new_node)
        self.size += 1


if __name__ == "__main__":
    # Demo proving correct eviction order
    lru = LRUCache(3)

    lru.put(1, 'a')
    lru.put(2, 'b')
    lru.put(3, 'c')

    print(lru.get(1))   # 'a' -> key 1 is accessed, becomes most recent
    # Expected: 'a'

    lru.put(4, 'd')     # capacity 3 is full, so key 2 (LRU) is evicted
    print(lru.get(3))   # 'c' -> still present
    print(lru.get(2))   # -1  -> key 2 was evicted
    print(lru.get(1))   # 'a' -> still present, most recent after get(1) then put(4)
    print(lru.get(4))   # 'd' -> most recent

    # Expected output:
    # 'a'
    # 'c'
    # -1
    # 'a'
    # 'd'
```

---

## r1

Here is the step-by-step deduction to solve the puzzle:

**1. Analyze Pets and Floors:**
*   **Clue 2** states that "The fish owner lives on floor 1."
    *   *Current Status:* Floor 1 Pet = **Fish**.
*   **Clue 4** states that "Ben owns the cat."
    *   *Current Status:* Ben’s Pet = **Cat**.

**2. Analyze Cal's Information:**
*   **Clue 3** states that "Cal lives on floor 3 and does not own the hawk."
*   We already know the pets are Cat, Dog, Fish, and Hawk.
*   Since Ben owns the Cat and Fish is on Floor 1, and Cal doesn't own the Hawk, Cal must own the **Dog**.
    *   *Current Status:* Cal lives on **Floor 3** and owns the **Dog**.

**3. Analyze Ana's Information:**
*   **Clue 1** states that "Ana lives directly above the dog owner."
*   We just determined that the dog owner (Cal) lives on Floor 3.
*   Therefore, Ana must live on Floor 4.
    *   *Current Status:* Ana lives on **Floor 4**.

**4. Determine Dee's Location:**
*   We have floors 1 through 4.
*   **Clue 5** states that "Dee does not live on floor 2."
*   We know Ana lives on Floor 4 and Cal lives on Floor 3.
*   This leaves only Floor 1 and Floor 2 available for Ben and Dee.
*   Since Dee cannot be on Floor 2, Dee must live on **Floor 1**.
*   Since Floor 1's pet is Fish, Dee must own the **Fish**.

**5. Fill in the remaining gaps:**
*   The only friend left is **Ben**, and the only floor left is **Floor 2**. Therefore, Ben lives on Floor 2.
*   The only pet left is the **Hawk**, and the only person left for Floor 4 is **Ana**. Therefore, Ana owns the Hawk.

***

### Final Answer:

*   **Ana:** Lives on Floor 4, owns the **Hawk**
*   **Ben:** Lives on Floor 2, owns the **Cat**
*   **Cal:** Lives on Floor 3, owns the **Dog**
*   **Dee:** Lives on Floor 1, owns the **Fish**

---

## r2

The tank's net filling rate when all three are open is the sum of the individual rates:

\[
\text{Rate}_A = \frac{1}{6} \quad (\text{tank per hour}), \qquad
\text{Rate}_B = \frac{1}{4} \quad (\text{tank per hour}), \qquad
\text{Rate}_C = -\frac{1}{12} \quad (\text{tank per hour, since it empties}).
\]

\[
\text{Net rate} = \frac{1}{6} + \frac{1}{4} - \frac{1}{12}
= \frac{2}{12} + \frac{3}{12} - \frac{1}{12}
= \frac{4}{12}
= \frac{1}{3} \text{ tank per hour}.
\]

The tank starts one quarter full and ends full, so the amount that must be added is

\[
1 - \frac{1}{4} = \frac{3}{4} \text{ tank}.
\]

Time required is the volume needed divided by the net rate:

\[
t = \frac{\frac{3}{4}}{\frac{1}{3}} = \frac{3}{4} \cdot \frac{3}{1} = \frac{9}{4} \text{ hours}.
\]

Thus, the tank becomes full after \(\boxed{\frac{9}{4}}\) hours.

---

## r3

To calculate the probability that a person actually has the disease given that they tested positive, we use Bayes' Theorem.

**1. Identify the Variables:**
*   **Prevalence (Probability of Disease):** $1 \text{ in } 1,000 = 0.001$
*   **Probability of No Disease:** $1 - 0.001 = 0.999$
*   **Sensitivity ($P(\text{Positive} | \text{Disease})$):** $99\% = 0.99$
*   **Specificity:** $95\% = 0.95$
*   **False Positive Rate ($P(\text{Positive} | \text{No Disease})$):** $1 - 0.95 = 0.05$

**2. Set up the Calculation:**
We want to find $P(\text{Disease} | \text{Positive})$.
$$P(\text{Disease} | \text{Positive}) = \frac{P(\text{Positive} | \text{Disease}) \times P(\text{Disease})}{P(\text{Positive} | \text{Disease}) \times P(\text{Disease}) + P(\text{Positive} | \text{No Disease}) \times P(\text{No Disease})}$$

**3. Substitute the Values:**
$$P(\text{Disease} | \text{Positive}) = \frac{0.99 \times 0.001}{0.99 \times 0.001 + 0.05 \times 0.999}$$

**4. Solve the Numerator and Denominator:**
*   **Numerator:** $0.99 \times 0.001 = 0.00099$ (True Positives)
*   **False Positives:** $0.05 \times 0.999 = 0.04995$
*   **Total Denominator:** $0.00099 + 0.04995 = 0.05094$

**5. Calculate the Final Probability:**
$$P(\text{Disease} | \text{Positive}) = \frac{0.00099}{0.05094} \approx 0.019444$$

**6. Convert to Percentage and Round:**
$$0.019444 \times 100 = 1.9444...\%$$

**Final Answer:**
**1.9%**

---

## r4

The only consistent assignment is:

- A is a knight.
- B is a knave.
- C is a knave.

**Proof:**

Assume A is a knight.  
- A's statement "B is a knave" is true, so B is a knave.  
- B's statement "A and C are the same type" is false (because B is a knave), so A and C are not the same type. Since A is a knight, C must be a knave.  
- C's statement "B is a knight" is false (C is a knave), so B is not a knight, which is consistent with B being a knave.

Thus (A = knight, B = knave, C = knave) is consistent.

Now assume A is a knave.  
- A's statement is false, so "B is a knave" is false → B is a knight.  
- B's statement is true (B is a knight), so "A and C are the same type." Since A is a knave, C must also be a knave.  
- C's statement is false (C is a knave), so "B is a knight" is false → B is not a knight, contradicting the earlier conclusion that B is a knight.

Hence A cannot be a knave. The only consistent assignment is A = knight, B = knave, C = knave.

---

## r5

Here is the step-by-step generation of the sequence starting from $n=7$.

**The function is defined as:**
$f(n) = \begin{cases} n/2 & \text{if } n \text{ is even} \\ 3n + 5 & \text{if } n \text{ is odd} \end{cases}$

**Step-by-Step Sequence:**

1.  **Current value:** $7$
    *   $7$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(7) + 5 = 21 + 5 = \mathbf{26}$

2.  **Current value:** $26$
    *   $26$ is **even**.
    *   Apply $n/2$:
    *   $26 / 2 = \mathbf{13}$

3.  **Current value:** $13$
    *   $13$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(13) + 5 = 39 + 5 = \mathbf{44}$

4.  **Current value:** $44$
    *   $44$ is **even**.
    *   Apply $n/2$:
    *   $44 / 2 = \mathbf{22}$

5.  **Current value:** $22$
    *   $22$ is **even**.
    *   Apply $n/2$:
    *   $22 / 2 = \mathbf{11}$

6.  **Current value:** $11$
    *   $11$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(11) + 5 = 33 + 5 = \mathbf{38}$

7.  **Current value:** $38$
    *   $38$ is **even**.
    *   Apply $n/2$:
    *   $38 / 2 = \mathbf{19}$

8.  **Current value:** $19$
    *   $19$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(19) + 5 = 57 + 5 = \mathbf{62}$

9.  **Current value:** $62$
    *   $62$ is **even**.
    *   Apply $n/2$:
    *   $62 / 2 = \mathbf{31}$

10. **Current value:** $31$
    *   $31$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(31) + 5 = 93 + 5 = \mathbf{98}$

11. **Current value:** $98$
    *   $98$ is **even**.
    *   Apply $n/2$:
    *   $98 / 2 = \mathbf{49}$

12. **Current value:** $49$
    *   $49$ is **odd**.
    *   Apply $3n + 5$:
    *   $3(49) + 5 = 147 + 5 = \mathbf{152}$

13. **Current value:** $152$
    *   $152$ is **even**.
    *   Apply $n/2$:
    *   $152 / 2 = \mathbf{76}$

14. **Current value:** $76$
    *   $76$ is **even**.
    *   Apply $n/2$:
    *   $76 / 2 = \mathbf{38}$

At step 14, the value **38** is generated. This is the same value generated at **step 6**, confirming that the sequence has looped back.

**Results:**

*   **Does the sequence enter a cycle?** **Yes**
*   **Full Cycle:** $38, 19, 62, 31, 98, 49, 152, 76$
*   **Step entered:** The cycle is first entered at **Step 7** (when the value $38$ is generated).

---

