import asyncio
import logging
import os
import sys
from types import GeneratorType
from typing import Union

import toml

from InputHandler import InputsHandler
from Protocols.BaseProtocol import *
from Saveloader.SaveLoader import JsonSaveLoader
from Session.SessionHandler import UsersSessionHandler
from users import User

if not os.path.exists('storage'):
    os.mkdir('storage')


class Server:
    def __init__(self, host: str, port: int, proto: BaseProtocol):
        self.host = host
        self.port = port
        self.logger = self.__init_logger()

        self.__InputsHandler = InputsHandler({'superuser'})
        self.UserDataHandler = JsonSaveLoader(storage_path='storage')
        self.UsersSessionHandler = UsersSessionHandler(self.UserDataHandler)
        self.Proto = proto

    async def run(self):
        '''

        start file server
        '''
        server = await asyncio.start_server(self.handle_connection, self.host, self.port)
        self.logger.info(f"Start server... {self.host}:{self.port} ({self.Proto.__class__.__name__})")
        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader, writer):
        addr = writer.get_extra_info("peername")
        uid = await self.Proto.handshake(reader, writer)
        await self.UsersSessionHandler.check_user(reader, writer, uid.strip())  # check user
        self.logger.info(f'connected by {addr}')
        while True:
            try:
                if not await self._handle_query(self.UsersSessionHandler.from_user(addr)):
                    await self.UsersSessionHandler.end_user_session(addr)
                    break
            except ConnectionError:
                self.logger.info(f'Client suddenly closed while receiving from {addr}')
                await self.UsersSessionHandler.end_user_session(addr)
                break
        self.logger.info(f'Disconnected by {addr}')

    async def _handle_query(self, user: User) -> bool:
        '''
        handle queries from users
        '''
        command, data_length = await self.Proto.receive_data(user.sock.reader, user.sock.writer)
        if command and not command.startswith(b'exit'):
            if command.startswith((b'send', b'open')):
                output_data = await self.__InputsHandler.handle_files(user, command, data_length, self.Proto)
            else:
                output_data = await self.__InputsHandler.handle_text_command(user, command, data_length)
            return await self.__handle_answer(user, output_data)
        else:

            return False

    async def __handle_answer(self, user: User, output_data: Union[GeneratorType, bytes]) -> bool:
        '''
        send text answer or file as bytes to user
        output_data is bytes for text answer
        or
        <class 'generator'> in case of file sending

        '''
        if isinstance(output_data[0], GeneratorType):
            await self.Proto.send_file(user.sock.reader, user.sock.writer, output_data)
        else:
            await self.Proto.send_data(user.sock.reader, user.sock.writer, output_data)
        return True

    async def stop(self):
        sessions = set(addr for addr in self.UsersSessionHandler.active_sessions.keys())
        for addr in sessions:
            await self.UsersSessionHandler.end_user_session(addr)
        logging.warning('STOP')

    @staticmethod
    def __init_logger() -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter(fmt='[%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        return logger


if __name__ == "__main__":
    Protocols = {'simple': SimpleProto,
                 'tcd8': TCD8}

    loop = asyncio.new_event_loop() # does not work correctly
    config = toml.load('cfg/config.toml')
    host, port, proto = config['conn'].values()

    # loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    server = Server(host, port, proto=Protocols[proto]())

    try:
        loop.run_until_complete(server.run())
    except KeyboardInterrupt:
        loop.run_until_complete(server.stop())
