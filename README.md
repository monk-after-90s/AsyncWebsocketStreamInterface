# AsyncWebsocketStreamInterface

AsyncWebsocketStreamInterface is an abstract class interface to be inherited to implement a certain asynchronous
websocket client.

We will take class BinanceFapiAsyncWs from
repository [BinanceAsyncWebsocket](https://github.com/monk-after-90s/BinanceAsyncWebsocket.git) as example to
demonstrate.

---

### [Install](#Install) · [Inherit](#Inherit)· [Usage](#Usage) ·

---

## Install

[AsyncWebsocketStreamInterface in **PyPI**](https://pypi.org/project/AsyncWebsocketStreamInterface/)

```shell
pip install AsyncWebsocketStreamInterface
```

## Inherit

There are 3 **abstract methods** in class AsyncWebsocketStreamInterface which is enforced to be inherited: _create_ws, _
when2create_new_ws, _parse_raw_data. In BinanceFapiAsyncWs, we implement more than these 3 mainly for these reasons:
this websocket is private thus it needs a apiKey, and it needs to send restful request for a listenkey and to send
heartbeats regularly to maintain a stable connection. So these relative implementation will not be discussed in detail.

### _create_ws

```python
async def _create_ws(self):
    ws = await websockets.connect(self.ws_baseurl + '/ws/' + await self._generate_listenkey())
    return ws
```

This is intuitive. You would have to create and return a websockets client. For more information about module
websockets, refer to
https://pypi.org/project/websockets/.

### _when2create_new_ws

```python
async def _when2create_new_ws(self):
    listenKeyExpired_stream = self.stream_filter([{'e': 'listenKeyExpired'}])

    async def read_listenKeyExpired_stream(listenKeyExpired_stream):
        async for news in listenKeyExpired_stream:
            try:
                return
            finally:
                asyncio.create_task(listenKeyExpired_stream.close())

    read_listenKeyExpired_stream_task = asyncio.create_task(read_listenKeyExpired_stream(listenKeyExpired_stream))
    # 20小时更新连接一次，或者服务端推送消息listenKey过期
    await asyncio.create_task(
        asyncio.wait(
            [read_listenKeyExpired_stream_task, asyncio.sleep(20 * 3600)],
            return_when='FIRST_COMPLETED'))
    logger.debug('Time to update ws connection.')
```

This method decides when to create and update new websockets client. Every time when a websockets client is created,
this method is called, and the coroutine is awaited. The coroutine is pending while the corresponding websockets client
is alive. When the coroutine is done, the corresponding websockets client is closed and abandoned, and a new one is
created.

In our example, 2 coroutines(task) is awaited --  "read_listenKeyExpired_stream_task" and "asyncio.sleep(20 * 3600)",
and the first completing one will trigger coroutine _when2create_new_ws set done, and the websockets client updated.

### _parse_raw_data

```python
async def _parse_raw_data(self, raw_data):
    msg = json.loads(raw_data)
    return msg
```

This method parse the raw data from the server to some format you wish.

In our simple example, we parse the json string to the data of certain type.

### Usage

After inheriting abstract methods, we would look to how to use our inheriting class. You may have already noticed that
we have inherited 3 'private' methods, which we might not even find them in our editor hint. In fact, they are not
methods which you will call in your codes.

#### stream_filter(_filters: list = None)

Transfer one normal asynchronous websocket connection to unlimited number of data streams. stream_filter returns an
asynchronous iterator. Whenever you want to set a coroutine to watch the websocket data, you could create a data stream:

```python
async def watcher():
    stream = ws.filter_stream()
    async for news in stream:
        print(news)
```

Remember that you'd better explicitly close the stream when it is no longer used:

```python
close_task = asyncio.create_task(stream.close())
...
await close_task
```

Parameter _filters is a list of dictionaries. If pairs of key and value of any dictionary could all be matched by some
message, then the message would be filtered, and the asynchronous iterator to be returned will generate only these
filtered message. For example,

```python
stream_filter([{'a': 1}, {'b': 2, "c": 3}])
```

Message

```python
{'a': 1, 'c': 2}
```

and

```python
{'b': 2, 'c': 3, 'd': 4}
```

would be filtered. However

```python
{'a': 2, 'c': 2}
```

or

```python
{'b': 2, 'c': 4, 'd': 4}
```

would not.

#### present_ws

This property returns the current alive websockets client.

#### send(msg)

Send a message to the websocket server.

#### exit()

Gracefully exit the instance of the websocket client class.

#### add_handler(function_or_coroutine_function)

Add a function or coroutine function to handle the new message. This handler takes the message as the only parameter.
For example:

```python
def f(msg):
    print(msg)


async def f2(msg):
    print(msg)    
```


