from random import random
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from vk_api.bot_longpoll import VkBotMessageEvent

from chatbot import Bot


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {'message': {'date': 1596283667, 'from_id': 19038361, 'id': 175, 'out': 0, 'peer_id': 19038361,
                              'text': 'Привет, бот', 'conversation_message_id': 175, 'fwd_messages': [],
                              'important': False, 'random_id': 0, 'attachments': [], 'is_hidden': False},
                  'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                                  'keyboard': True, 'inline_keyboard': True, 'carousel': False, 'lang_id': 0}},
        'group_id': 197152310, 'event_id': '29ce915ff6851f119272d1f331dbe313cb5bd791'}
    
    def test_run(self):
        count = 5
        events = [{}] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock
        with patch('chatbot.vk_api.VkApi'):
            with patch('chatbot.VkBotLongPoll', return_value=long_poller_listen_mock):
                chatbot = Bot('', '')
                chatbot.on_event = Mock()
                chatbot.run()
                chatbot.on_event.assert_called()
                chatbot.on_event.assert_any_call(event={})
                chatbot.on_event.call_count = count
    
    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        send_mock = Mock()
        with patch('chatbot.vk_api.VkApi'):
            with patch('chatbot.VkBotLongPoll'):
                chatbot = Bot('', '')
                chatbot.api = Mock()
                chatbot.api.messages.send = send_mock
                chatbot.on_event(event=event)
        
        send_mock.assert_called_once_with(
            message=f'Здравствуй, Никита!',
            random_id=ANY,
            peer_id=self.RAW_EVENT['object']['message']['peer_id'],
        )

