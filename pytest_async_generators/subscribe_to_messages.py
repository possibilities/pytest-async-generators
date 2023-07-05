import time
import asyncio
import typing
import pytest_asyncio
from dataclasses import dataclass


@dataclass
class AsyncGeneratorSubscriber:
    wait_for_messages: typing.Callable[
        [], typing.Coroutine[typing.Any, typing.Any, typing.List[typing.Any]]
    ]


@pytest_asyncio.fixture
async def subscribe_to_messages(timeout: float = 0.5) -> typing.Callable:
    async def _subscribe_to_messages(
        generator: typing.AsyncGenerator,
    ) -> AsyncGeneratorSubscriber:
        results = []

        async def collector() -> None:
            start_time = time.time()
            while True:
                try:
                    try:
                        elapsed_time = time.time() - start_time
                        remain_timeout = max(0, timeout - elapsed_time)
                        value = await asyncio.wait_for(
                            generator.asend(None), remain_timeout
                        )
                        results.append(value)
                        start_time = time.time()
                    except asyncio.TimeoutError:
                        break
                except StopAsyncIteration:
                    break
                except asyncio.CancelledError:
                    pass

        collector_task = asyncio.create_task(collector())

        async def wait_for_messages() -> typing.List[typing.Any]:
            await collector_task
            return results

        return AsyncGeneratorSubscriber(wait_for_messages=wait_for_messages)

    return _subscribe_to_messages
