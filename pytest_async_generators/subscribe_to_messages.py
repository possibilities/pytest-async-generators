import asyncio
import pytest_asyncio
from dataclasses import dataclass
from typing import List, Any, AsyncGenerator, Coroutine, Callable


@dataclass
class AsyncGeneratorSubscriber:
    wait_for_messages: Callable[[], Coroutine[Any, Any, List[Any]]]


@pytest_asyncio.fixture
async def subscribe_to_messages() -> Callable:
    async def _subscribe_to_messages(
        generator: AsyncGenerator,
    ) -> AsyncGeneratorSubscriber:
        results = []
        last_received_time = asyncio.get_event_loop().time()

        async def collector() -> None:
            nonlocal last_received_time

            value = await generator.asend(None)
            results.append(value)
            first_received_elapsed = (
                asyncio.get_event_loop().time() - last_received_time
            )
            last_received_time = asyncio.get_event_loop().time()

            while True:
                try:
                    try:
                        value = await asyncio.wait_for(
                            generator.asend(None), first_received_elapsed * 1.25
                        )
                        results.append(value)
                        last_received_time = asyncio.get_event_loop().time()
                    except asyncio.TimeoutError:
                        if (
                            asyncio.get_event_loop().time() - last_received_time
                            > first_received_elapsed
                        ):
                            break
                except StopAsyncIteration:
                    break
                except asyncio.CancelledError:
                    pass

        collector_task = asyncio.create_task(collector())

        async def wait_for_messages() -> List[Any]:
            await collector_task
            return results

        return AsyncGeneratorSubscriber(wait_for_messages=wait_for_messages)

    return _subscribe_to_messages
