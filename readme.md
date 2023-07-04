# Pytest Async Generators

Pytest fixtures for async generators

## Usage

Invoke any async generator and call `wait_for_messages()` to retrieve the results.

```
async def count() -> AsyncGenerator[int, None]:
    for n in range(10):
        await asyncio.sleep(0.1)
        yield n


@pytest.mark.asyncio
async def test_counting(subscribe_to_messages) -> None:
    subscription = await subscribe_to_messages(count())
    messages = await subscription.wait_for_messages()
    assert messages == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

Note that with real generators you might need to cause events to happen by adding more code after `subscribe_to_messages` and before calling `wait_for_messages`.

## Caveats

The fixture assumes that each message takes approximately the same amount of time because the arrival time of the first message is used to determine the approximate timeout to wait before returning the collected messages. If your generators don't work this way this plugin will make yowon't work correctly and will make you sad.
