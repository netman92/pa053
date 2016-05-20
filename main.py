import json
import os

import requests
from bottle import route, run, response, request

numbers = set([str(i) for i in range(10)])
arithmetic_allowed_chars = {'(', ')', '+', '-', '*', '/'}.union(numbers)
iata_url = 'http://www.airport-data.com/api/ap_info.json?iata={0}'
weather_url = 'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid=d78388e82cfb073ad5426bed3729376a&units=metric'
finance_url = 'https://finance.yahoo.com/webservice/v1/symbols/{stock}/quote?format=json'


def is_arithmetic_operations(query):
    return all([i in arithmetic_allowed_chars for i in list(query)])


def run_arithmetic_operation(query):
    code = 200
    try:
        res = float(eval(query))
    except Exception as e:
        code = 500
        res = {
            'status': 'error',
            'msg': str(e)
        }
    return res, code


def is_iata(query):
    # simple check
    conds = {
        query.upper() == query,
        len(query) == 3
    }
    if not all(conds):
        return False

    try:
        res = requests.get(iata_url.format(query))
    except:
        return False
    res = res.json()
    if (res.get('longitude'), res.get('latitude')) == (0, 0):
        return False
    return res


def get_weather(iata_data):
    res = requests.get(weather_url.format(lat=iata_data['latitude'], lon=iata_data['longitude']))
    try:
        res = res.json()
        return float(res['main']['temp']), 200
    except Exception as e:
        return {
                   'status': 'error',
                   'msg': str(e)
               }, 500


def get_stock(query):
    conds = {
        query.upper() == query,
        len(query) in list(range(1, 5))
    }
    unknown = {
                  'status': 'error',
                  'msg': 'Unknown query'
              }, 500

    if not all(conds):
        return unknown

    json_res = requests.get(finance_url.format(stock=query)).json()
    if not json_res['list']['resources']:
        return unknown
    try:
        price = float(json_res['list']['resources'][0]['resource']['fields']['price'])
        return price, 200
    except (KeyError, ValueError):
        return unknown


def get_response(query):
    if query == 'None':
        return {
                   'status': 'error',
                   'msg': 'query param is missing'
               }, 400
    # arithmetic
    if is_arithmetic_operations(query):
        return run_arithmetic_operation(query)

    # iata
    iata_data = is_iata(query)
    if iata_data:
        return get_weather(iata_data)

    # stock
    return get_stock(query)


@route('/')
def index():
    query = str(request.GET.get('query'))
    resp, code = get_response(query)

    response.content_type = 'application/json'
    response.status = code
    return json.dumps(resp)


run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
