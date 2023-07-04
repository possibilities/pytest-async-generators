import time
import asyncio
import pytest
from typing import Any, AsyncGenerator, Callable


class EventBusWithAsyncGenerator:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()

    async def send_message(self, event: Any) -> None:
        await self.queue.put(event)

    async def to_async_generator(self) -> AsyncGenerator[Any, None]:
        start_time = time.time()
        yield await self.queue.get()

        first_event_elapsed_time = time.time() - start_time
        timeout = first_event_elapsed_time * 1.25
        while True:
            try:
                yield await asyncio.wait_for(self.queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                break


@pytest.mark.asyncio
async def test_fake_generator(subscribe_to_messages: Callable) -> None:
    event_bus = EventBusWithAsyncGenerator()

    subscription = await subscribe_to_messages(event_bus.to_async_generator())

    await asyncio.sleep(0.10)
    await event_bus.send_message("first-message")
    await asyncio.sleep(0.11)
    await event_bus.send_message("second-message")
    await asyncio.sleep(0.12)
    await event_bus.send_message("third-message")

    [message_1, message_2, message_3] = await subscription.wait_for_messages()

    assert message_1 == "first-message"
    assert message_2 == "second-message"
    assert message_3 == "third-message"


async def count() -> AsyncGenerator[int, None]:
    for n in range(10):
        await asyncio.sleep(0.1)
        yield n


@pytest.mark.asyncio
async def test_realish_generator(subscribe_to_messages: Callable) -> None:
    subscription = await subscribe_to_messages(count())
    messages = await subscription.wait_for_messages()
    assert messages == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
