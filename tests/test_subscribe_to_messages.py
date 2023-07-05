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


@pytest.mark.asyncio
async def test_subscription_counting(
    subscription_client: Callable,
    subscribe_to_messages: Callable,
) -> None:
    subscription = subscription_client(
        "subscription Count { count(target: 3) }",
    )

    subscribing = await subscribe_to_messages(subscription)

    messages = await subscribing.wait_for_messages()
    assert messages == [{"count": 0}, {"count": 1}, {"count": 2}]
