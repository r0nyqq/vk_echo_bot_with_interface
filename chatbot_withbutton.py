# -*- coding: utf-8 -*-
from copy import copy

import vk_api
import random
import logging
import json

import handlers
from database.DB_updater import DatabaseUpdater

try:
    import settings, _token
except ImportError:
    exit('Do cp settings.py.default settings.py and set token!')
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

log_file = 'log_file.txt'
welcome_message_list = ['привет', 'здравствуй', 'здарова', 'хай', 'hi', 'hello', 'прив']
log = logging.getLogger('bot')


class UserState:
    """состояние пользователя внутри сценария"""
    
    def __init__(self, scenario_name, step, context=None, best_way=None, favorites=None):
        self.scenario_name = scenario_name
        self.step_name = step
        self.context = context or {}
        self.best_ways = best_way or []


class Bot:
    """
    Сценарий поиска билетов на авиасейл
    Use python3.8
    """
    
    def __init__(self, group_id, token_vk):
        """
        :param group_id: из группы vk импортируется из _token
        :param token_vk: секретный токен от группы vk импортируется из _token
        """
        self.group_id = group_id
        self.token = token_vk
        self.vk = vk_api.VkApi(token=token_vk)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
        self.user_name = self.api.users.get
        self.user_state = dict()  # user_id -> UserState
    
    def get_button(self, colors, text_in_button, payload=''):
        return {
                   "action": {
                       "type": "text",
                       "payload": json.dumps(payload),
                       "label": text_in_button
                   },
                   "color": colors
               },
    
    def create_buttons(self, params, inline=False, one_time=True):
        list_param = [self.get_button(param[0], param[1]) for param in params]
        return str(
            json.dumps({"one_time": one_time, "buttons": list_param, 'inline': inline}, ensure_ascii=False).encode(
                'utf-8').decode(
                'utf-8'))
    
    def run(self):
        """Запуск бота."""
        for event in self.long_poller.listen():
            try:
                self.on_event(event=event)
            except Exception as err:
                log.exception(f'ошибка в обработке события: "{err}"')
    
    def on_event(self, event):
        """Отправляет сообщение назад, если это сообщение текстовое
        :param event: VkBotEventType object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Мы пока не умеем обрабатывать события такого типа: %s', event.type)
            return
        
        user_id = event.object.message['from_id']
        text = event.object.message['text']
        try:
            if user_id in self.user_state and self.user_state[user_id].best_ways:
                for flight in self.user_state[user_id].best_ways:
                    if flight[0].startswith(text):
                        self.send_messages(user_id, settings.text_for_send['add_favorite'].format(flight[0]))
                        DatabaseUpdater(user_id=user_id, ticket=flight[0], date=flight[3], orig=flight[1],
                                        destination=flight[2]).update_db()
                        self.user_state.pop(user_id)
            
            elif text == 'Показать билеты в избранном':
                retrieve = DatabaseUpdater(user_id=user_id).retrieval_data()
                if not retrieve:
                    text_to_send = 'В избранном билеты отсутствуют'
                else:
                    text_to_send = ''
                    for ticket in retrieve:
                        text_to_send += f'\n {ticket.ticket}'
                self.send_messages(user_id, text_to_send)
            
            elif text == 'Помощь':
                text_to_send = settings.text_for_send['help']
                self.send_messages(user_id, text_to_send)
            
            elif text == 'Искать билет':
                self.start_scenarios(user_id)
            
            elif text == 'Вернуться в главное меню' or not self.user_state:
                if user_id in self.user_state:
                    del self.user_state[user_id]
                buttons = [['positive', 'Искать билет'], ['primary', 'Помощь'],
                           ['primary', 'Показать билеты в избранном']]
                self.send_messages(user_id, settings.text_for_send['main_menu'], buttons)
            
            elif user_id in self.user_state and text != 'Показать билеты':
                self.continue_scenarios(text, user_id)
            
            elif text == 'Показать билеты':
                self.create_and_show_ticket_list(user_id)
        
        except ValueError as exc:
            self.send_messages(user_id, exc)
    
    def start_scenarios(self, user_id):
        scenario = settings.SCENARIOS['registration']
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_state[user_id] = UserState(scenario_name='registration', step=first_step)
        self.send_messages(user_id, text_to_send)
    
    def continue_scenarios(self, text, user_id):
        state = self.user_state[user_id]
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            button = next_step['button']
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
        else:
            button = None
            text_to_send = step['failure_text'].format(**state.context)
        if button:
            self.send_messages(user_id, text_to_send, next_step['button_form'], main_menu=True)
        else:
            self.send_messages(user_id, text_to_send)
    
    def create_and_show_ticket_list(self, user_id):
        list_for_show = []
        ways = self.user_state[user_id].context['ways']
        for flight in ways:
            list_for_show.append([
                'primary', f"Цена: {flight['value']}, АК:{flight['gate']}, Класс: {flight['trip_class']}",
                flight['origin'], flight['destination'], flight['depart_date']
            ])
        for i, flight in enumerate(list_for_show):
            if i == 5:
                break
            self.user_state[user_id].best_ways.append(
                (f'{flight[1]}. Направление:{self.user_state[user_id].context["from_to"]}', flight[2], flight[3],
                 flight[4]))
        text = settings.text_for_send['chose_to_favorite'].format(**self.user_state[user_id].context)
        self.send_messages(user_id=user_id, text=text, button_list=list_for_show, main_menu=True)
    
    def send_messages(self, user_id, text, button_list=None, main_menu=False):
        buttons = copy(button_list)
        if buttons:
            buttons.append(['negative', 'Вернуться в главное меню']) if main_menu else buttons
            buttons = self.create_buttons(buttons)
        else:
            buttons = self.create_buttons([['negative', 'Вернуться в главное меню']])
        self.api.messages.send(
            peer_id=user_id,
            message=text,
            keyboard=buttons,
            random_id=random.randint(0, 2 ** 20)
        )


def configure_logging(log_file_name):
    file_handler = logging.FileHandler(filename=log_file_name, mode='a', encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter('| %(asctime)s | %(levelname)-10s |\n| Cообщение: %(message)s |', datefmt='%d-%m-%Y %H:%M')
    )
    file_handler.setLevel(logging.ERROR)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('| %(levelname)s | %(message)s |'))
    stream_handler.setLevel(logging.DEBUG)
    
    log.addHandler(stream_handler)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


if __name__ == '__main__':
    configure_logging(log_file)
    bot = Bot(group_id=_token.group_id, token_vk=_token.token_vk)
    bot.run()
    bot.vk.get_api()
