import asyncio
import pytest
from typing import AsyncGenerator, Callable


@pytest.mark.asyncio
async def test_counting(subscribe_to_messages: Callable) -> None:
    async def count() -> AsyncGenerator[int, None]:
        for n in range(10):
            await asyncio.sleep(0.2)
            yield n

    subscription = await subscribe_to_messages(count())
    messages = await subscription.wait_for_messages()
    assert messages == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
