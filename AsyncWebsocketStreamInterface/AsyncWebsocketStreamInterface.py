import asyncio
import traceback
from abc import ABCMeta, abstractmethod
from copy import deepcopy

import beeprint
import websockets
from ensureTaskCanceled import ensureTaskCanceled
from loguru import logger


class AsyncWebsocketStreamInterface(metaclass=ABCMeta):
    '''
    Used in a asyncio event loop.
    '''

    def __init__(self):
        self._wsq: asyncio.Queue = asyncio.Queue()
        self._wsq.present_ws: websockets.WebSocketClientProtocol = None
        self._wsq.previous_ws: websockets.WebSocketClientProtocol = None
        self._exiting = False
        asyncio.create_task(self._ws_manager())
        self._handlers = set()
        self._ws_exchanged = asyncio.Event()

    # log_path = '/tmp/db.log'
    #
    # def connect(self):
    #     print('connect db ...')
    #
    # @abstractmethod
    # def query(self, sql):
    #     pass
    #
    # @abstractmethod
    # def update(self, sql):
    #     pass
    async def _handle_wsq(self):
        '''
        始终使用原生ws连接队列中的最后一个

        :return:
        '''
        _handle_raw_ws_msg_task = None
        while not self._exiting:
            # 拿到最新原生ws连接
            while True:
                self._wsq.previous_ws = self._wsq.present_ws
                self._wsq.present_ws = await self._wsq.get()
                self._wsq.task_done()

                # 关闭之前的ws连接
                if isinstance(self._wsq.previous_ws, websockets.WebSocketClientProtocol):
                    asyncio.create_task(self._wsq.previous_ws.close())
                # 拿完了，得到最后一个
                if self._wsq.qsize() <= 0:
                    if _handle_raw_ws_msg_task:
                        # 删除之前的ws处理任务
                        asyncio.create_task(ensureTaskCanceled(_handle_raw_ws_msg_task))
                    break
            _handle_raw_ws_msg_task = asyncio.create_task(self._handle_raw_ws_msg(self._wsq.present_ws))
            self._ws_exchanged.set()

    async def _handle_raw_ws_msg(self, ws: websockets.WebSocketClientProtocol):
        async for msg in ws:
            try:
                # logger.debug(repr(old_ws_update_ws_task))
                msg = await self._parse_raw_data(msg)
                logger.debug(
                    '\n' + beeprint.pp(msg, output=False, string_break_enable=False, sort_keys=False))
                # logger.debug('\n' + repr(self._update_ws_task))
                tasks = []
                for handler in self._handlers:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(asyncio.create_task(handler(deepcopy(msg))))
                    else:
                        try:
                            handler(deepcopy(msg))
                        except:
                            pass
                for task in tasks:
                    try:
                        await task
                    except:
                        pass
            except:
                logger.error('\n' + traceback.format_exc())

    @abstractmethod
    async def _parse_raw_data(self, raw_data):
        pass

    @property
    def ws(self):
        return self._wsq.present_ws

    async def send(self, msg):
        await self.ws.send(msg)

    @abstractmethod
    async def _create_ws(self):
        '''
        Create a websockets connection.

        :return:websockets ws instance just created.
        '''
        pass

    @abstractmethod
    async def _when2create_new_ws(self):
        '''

        :return:
        '''
        pass

    async def exit(self):
        self._exiting = True
        await asyncio.create_task(self._wsq.present_ws.close())

    async def _ws_manager(self):
        # 启动ws连接队列的消息对接handlers处理任务
        asyncio.create_task(self._handle_wsq())
        # 初始创建一个ws连接
        self._wsq.put_nowait(await self._create_ws())
        while not self._exiting:
            # 等待需要更新连接的信号
            await self._when2create_new_ws()
            # reset exchange ok event
            self._ws_exchanged.clear()
            # 更新连接
            self._wsq.put_nowait(await self._create_ws())
            # wait until ws is exchanged.
            await self._ws_exchanged.wait()
            logger.debug('New ws connection opened.')

            # # 通知实例化完成
            # if not self._instantiate_ok.done():
            #     self._instantiate_ok.set_result(None)


# todo  stream_filter 初始ws


if __name__ == '__main__':
    class C(AsyncWebsocketStreamInterface):
        async def create_ws(self):
            pass


    C()
