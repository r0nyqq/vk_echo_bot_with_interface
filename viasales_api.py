import requests

IATA_URL = 'https://www.travelpayouts.com/widgets_suggest_params?'
AVIASALES_URL = 'http://min-prices.aviasales.ru/calendar_preload'


class AviasalesApi:

    def __init__(self, from_to, date, sides=True):
        self.from_to = from_to
        self.date = date
        self.sides = sides
        self.best_ways = self.create_list_of_b_way()

    def get_fromto_iata_name(self):
        out_city = dict()
        req = requests.get(url=IATA_URL, params={'q': self.from_to})
        req_json = req.json()
        if not req_json:
            raise ValueError('Один из введенных вами городов не известен нашей системе, проси прощения за '
                             'предоставленные неудобства, пожалуйста попробуйте сформировать новый запрос.')
        for side in req_json:
            out_city[side] = req_json[side]['iata']
        return out_city

    def create_list_of_b_way(self):
        out_city = self.get_fromto_iata_name()
        list_way = list()
        req = requests.get(
            url=AVIASALES_URL,
            params={
                'origin': out_city['origin'],
                'destination': out_city['destination'],
                'depart_date': self.date,
                'one_way': self.sides
            }
        )
        price = req.json()
        if price['errors']:
            raise ValueError('Один из введенных вами городов не известен нашей системе, проси прощения за '
                             'предоставленные неудобства, пожалуйста попробуйте сформировать новый запрос.')
        
        for b_price in price['best_prices']:
            del b_price['show_to_affiliates'], b_price['found_at']
            list_way.append(b_price)
            if len(list_way) == 5:
                break
        return sorted(list_way, key=lambda x: x['value'])
