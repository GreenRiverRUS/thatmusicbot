import os
from typing import List
from uuid import uuid4
import logging

import aiohttp
from tornado.ioloop import IOLoop
from tornado import web
from wcpan.telegram import api, types

from constants import ABOUT_TEXT, START_TEXT, NO_COMMAND

INLINE_QUERY_CACHE_TIME = 24 * 60 * 60  # * 30 # 1 month
INLINE_QUERY_POPULAR_CACHE_TIME = 24 * 60 * 60  # 1 day
logging.basicConfig(format='{levelname:8s} [{asctime}] {message}', style='{', level=logging.DEBUG)


# noinspection PyAbstractClass
class BotHandler(api.BotHookHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self._bot_name = None

    @staticmethod
    def find_command(message: types.Message):
        entities = message.entities or []  # type: List[types.MessageEntity]
        commands = [entity for entity in entities if entity.type_ == 'bot_command']
        if len(commands):
            command = commands[0]
            command_name = message.text[command.offset:command.offset + command.length]
            command_args = message.text[command.offset + command.length:].strip()
            return command_name, command_args
        return None, None

    @staticmethod
    def get_username(user: types.User):
        if user.username is not None:
            return '@{}'.format(user.username)
        else:
            return user.first_name

    async def get_bot_name(self):
        if self._bot_name is None:
            client = self.settings['agent'].client  # type: api.BotClient
            bot_user = await client.get_me()  # type: types.User
            self._bot_name = self.get_username(bot_user)
        return self._bot_name

    async def search(self, query: str, limit: int = 50):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.settings['api_endpoint'],
                params={'q': query}
            ) as response:
                result = (await response.json())['data']

        return result[:limit]

    async def on_text(self, message: types.Message) -> None:
        client = self.settings['agent'].client  # type: api.BotClient
        logging.info('Message from {}: {}'.format(self.get_username(message.from_), message.text))

        user_id = message.from_.id_
        command, command_args = self.find_command(message)
        if command is not None:
            if command == '/start':
                bot_name = await self.get_bot_name()
                await client.send_message(
                    user_id, START_TEXT.format(bot_name=bot_name)
                )
            elif command == '/about':
                bot_name = await self.get_bot_name()
                await client.send_message(
                    user_id, ABOUT_TEXT.format(bot_name=bot_name), parse_mode='html'
                )
            else:
                await client.send_message(user_id, NO_COMMAND)
        else:
            await client.send_message(user_id, NO_COMMAND)

    @staticmethod
    def format_duration(duration: int):
        return '{}:{:02d}'.format(duration // 60, duration % 60)

    async def on_inline_query(self, inline_query: types.InlineQuery) -> None:
        client = self.settings['agent'].client  # type: api.BotClient
        logging.info('Inline query from {}: {}'.format(
            self.get_username(inline_query.from_), inline_query.query
        ))

        query = inline_query.query.strip()
        audios = await self.search(query)

        results = []
        for audio in audios:
            results.append(
                types.InlineQueryResultAudio(
                    id_=uuid4().hex,
                    audio_url=audio['download'],
                    title=audio['title'],
                    performer='{} · {}'.format(
                        audio['artist'], self.format_duration(audio['duration'])
                    ),
                    audio_duration=audio['duration']
                )
            )

        # logging.debug(results)

        if len(query):
            cache_time = INLINE_QUERY_CACHE_TIME
        else:
            cache_time = INLINE_QUERY_POPULAR_CACHE_TIME
        logging.debug('Cache time: {}'.format(cache_time))

        await client.answer_inline_query(
            inline_query.id_,
            results,
            cache_time=cache_time,
            is_personal=False
        )


class Bot:
    def __init__(self, token: str, host: str, api_endpoint: str,
                 port: int = 8000, certificate_path: str = None):
        self.token = token
        self.host = host
        self.port = port
        if certificate_path:
            self.certificate = types.InputFile(certificate_path)
        else:
            self.certificate = None

        self.api_endpoint = api_endpoint

        self.loop = IOLoop.current()
        self.app = None

    async def create_agent(self):
        agent = api.BotAgent(self.token)
        await agent.client.set_webhook(
            url=self.host, certificate=self.certificate
        )
        return agent

    def run(self):
        agent = self.loop.run_sync(self.create_agent)  # type: api.BotAgent
        self.app = web.Application(
            handlers=[
                ('/', BotHandler),
            ],
            agent=agent,
            api_endpoint=self.api_endpoint
        )
        self.app.listen(self.port)
        logging.info('Listening on {}, port {}'.format(self.host, self.port))
        self.loop.start()


if __name__ == '__main__':
    Bot(
        token=os.environ['BOT_TOKEN'],
        host=os.environ['WEBHOOK_HOST'],
        api_endpoint=os.environ['API_ENDPOINT'],
        certificate_path=os.environ.get('CERTIFICATE_PATH', None)
    ).run()
