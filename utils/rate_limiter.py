import asyncio
import random
import logging

logger = logging.getLogger(__name__)


async def polite_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def retry_async(coro_func, max_attempts: int = 3, base_delay: float = 5.0):
    for attempt in range(max_attempts):
        try:
            return await coro_func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
