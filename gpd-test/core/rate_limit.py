import asyncio
import time

class TokenBucketLimiter:
    def __init__(self, rate: float, capacity: float | None = None):
        self.capacity = capacity or rate
        self.tokens = self.capacity
        self.refill_rate = rate
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                if elapsed > 0:
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                    self.last_refill = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
            await asyncio.sleep(0.005)
