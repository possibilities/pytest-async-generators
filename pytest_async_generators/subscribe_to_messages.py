import time
import asyncio
import pytest
import pytest_asyncio
from dataclasses import dataclass
import typing
from aiohttp.test_utils import TestServer
from pytest_async_generators.app import create_app
from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
from graphql.language.ast import DocumentNode


@pytest_asyncio.fixture
async def server(
    aiohttp_server: typing.Callable[..., typing.Awaitable[TestServer]],
) -> TestServer:
    return await aiohttp_server(create_app())


@pytest_asyncio.fixture
async def websocket_transport(
    server: TestServer,
) -> typing.AsyncGenerator[WebsocketsTransport, None]:
    transport = WebsocketsTransport(
        url=f"ws://localhost:{server.port}/graphql", close_timeout=0.1
    )
    yield transport
    await transport.close()


@pytest.fixture
def subscription_client(websocket_transport: WebsocketsTransport) -> typing.Callable:
    def _subscription_client(query_string: str) -> typing.AsyncGenerator:
        query = gql(query_string)
        client = Client(
            transport=websocket_transport, fetch_schema_from_transport=False
        )
        return client.subscribe_async(query)

    return _subscription_client


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
