# Pytest Async Generators

Pytest fixtures for async generators

## Usage

Invoke any async generator with `await subscribe_to_messages()` and then `await wait_for_messages()` to retrieve the results.

```
import asyncio
import pytest
from typing import AsyncGenerator, Callable


@pytest.mark.asyncio
async def test_counting(subscribe_to_messages: Callable) -> None:
    async def count() -> AsyncGenerator[int, None]:
        for n in range(10):
            await asyncio.sleep(0.1)
            yield n

    subscription = await subscribe_to_messages(count())
    messages = await subscription.wait_for_messages()
    assert messages == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

`subscribe_to_messages()` can be passed a `timeout` parameter to control how long to wait for new messages.
