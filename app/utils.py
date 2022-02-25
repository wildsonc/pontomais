from dateutil.relativedelta import relativedelta
from prettytable import PrettyTable
from datetime import datetime, date
from django.conf import settings

from .models import Team, TelegramGroup, History, Shift

import operator
import requests
import time
import pytz
import json

import telepot

bot = telepot.Bot(settings.BOT_TOKEN)

BASE_URL = settings.URL


def req(url, data=None):
    token = settings.TOKEN
    header = {"Content-Type": "application/json", "access-token": token}
    if data:
        data = json.dumps(data)
        r = requests.post(f"{BASE_URL}/{url}", data=data, headers=header).json()
    else:
        r = requests.get(f"{BASE_URL}/{url}", headers=header).json()
    return r


def date_parser(date, time):
    timezone = pytz.timezone(settings.TIME_ZONE)
    date = date[-10:]
    string = f"{date} {time}"
    date = datetime.strptime(string, '%d/%m/%Y %H:%M')
    return timezone.localize(date)


def time_parser(time, revert=False):
    if revert:
        _ = 1
        signal = ''
        if time < 0:
            _ = -1
            signal = '-'
        hour = (time * _ // 60)
        minute = (time * _ % 60)
        return f"{signal}{hour}:{'{0:02}'.format(minute)}"
    hour, minute, *rest = time.split(':')
    return int(minute) + (int(hour) * 60)


def extra_time(data):
    count = 0
    if not even(len(data)):
        time = datetime.now().time()
        time = str(time)[:5]
        data.append({'time': time})
        for index, i in enumerate(data):
            if even(index):
                count += time_parser(data[index + 1]['time']) - time_parser(i['time'])
        shift = Shift.objects.get(name=data[0]['shift_name'])
        time = shift.periods[week_day()]
        extra = count - time
        if count > time:
            if extra % 10 == 0:
                msg = ''
                if extra == 60:
                    msg = '\n&#9208; <i>Notificações pausadas para esse usuário</i>'
                if extra <= 60:
                    return f"&#9203;<b>{data[0]['employee_name']}</b>\n<i>Hora extra:</i> <b>{extra}</b> <i>minutos</i>{msg}"


def week_day():
    n = date.today().isoweekday()
    n = 0 if n == 7 else n
    return n


def even(num):
    return True if (num % 2) == 0 else False


def card_parser(data):
    h = data[-1]
    try:
        History.objects.create(name=h["employee_name"],
                               index=h["time_card_index"],
                               date_time=date_parser(h["date"], h["time"]))
    except Exception as e:
        return
    if h['manually_changed'] == 'Sim':
        address = "\n&#9997; Endereço editado"
    else:
        if h['original_address']:
            address = f"\n&#128205; {h['original_address']}"
        else:
            address = ''
    source = '&#128241;'
    if h['source'] == 'Relógio':
        source = '&#127915; '
        address = ''
    msg = [f'{source}<b><i>{h["employee_name"]}{address}</i></b>']
    msg = _history_parser(data, msg)
    return '\n'.join(msg)


def _history_parser(data, msg):
    for r in data:
        icon = '&#128308;'
        if 'Entrada' in r['time_card_index']:
            icon = '&#128994;'
        j = f"{icon}{r['time_card_index']} {r['time']}"
        msg.append(j)
    return msg


class Group:
    def __init__(self):
        self.obj = {}

    def get_group(self, team, data):
        team = Team.objects.get(name=team)
        groups = TelegramGroup.objects.all()
        for group in groups:
            d = self._check(team.department.get_name, group.department)
            t = self._check(team.get_name, group.team)
            c = self._check(team.get_city, group.city)
            cp = self._check(team.get_company, group.company)
            valid = self._validate(d, t, c, cp, group)
            if valid:
                try:
                    self.obj[group.name]['data'].append(data)
                except:
                    self.obj[group.name] = {}
                    self.obj[group.name]['data'] = [data]
                    self.obj[group.name]['chat_id'] = group.chat_id
                    self.obj[group.name]['active'] = group.active
        return self.obj

    def _check(self, *args):
        if args[1]:
            for d in args[1]:
                if d == args[0]:
                    return True
            return False
        else:
            return True

    def _op(self, value):
        op = {
            'and': operator.and_,
            'or': operator.or_,
            'not': operator.not_
        }
        return op[value]

    def _validate(self, d, t, c, cp, group):
        if group.team_filter != 'not':
            a = self._op(group.team_filter)(d, t)
        else:
            a = d and not t
        if group.team_filter != 'not':
            b = self._op(group.city_filter)(a, c)
        else:
            b = a and not c
        if group.team_filter != 'not':
            j = self._op(group.company_filter)(b, cp)
        else:
            j = b and not cp
        return j


def send_message(data, chat_id, title=None):
    msg = '\n\n'.join(data)
    if title:
        msg = f'{title}\n\n{msg}'
    try:
        bot.sendMessage(chat_id, msg, 'html')
    except:
        time.sleep(30)
        bot.sendMessage(chat_id, msg, 'html')


def send_table(data, chat_id):
    t = PrettyTable()
    t.field_names = ['Nome', 'Horas', 'Faltas', 'Ajustes', 'Order']
    t.add_rows(data)

    hours, missing_days, proposals = 0, 0, 0
    for r in data:
        hours += int(r[4])
        missing_days += int(r[2])
        proposals += int(r[3])
    t.add_row(['Total', time_parser(hours, True), missing_days, proposals, -10000])

    table = t.get_string(title='Saldo de horas', sortby="Order", reversesort=True, fields=['Nome', 'Horas', 'Faltas', 'Ajustes'], end=45)
    bot.sendMessage(chat_id, f'<pre>{table}</pre>', 'html')

    if len(data) > 45:
        table = t.get_string(sortby="Order", reversesort=True, fields=['Nome', 'Horas', 'Faltas', 'Ajustes'], start=45, end=90)
        bot.sendMessage(chat_id, f'<pre>{table}</pre>', 'html')


def work_days(delay: int = 0):
    today = datetime.now().replace(day=26)
    start_date = today.date() + relativedelta(months=-(1 + delay))
    end_date = today.date().replace(day=25) + relativedelta(months=-delay)
    if today.day > 26:
        start_date = today.date() + relativedelta(months=-delay)
    return str(start_date), str(end_date)


def extra_time_table(data):
    total_time = 0
    for e in data['extra_time']:
        total_time += time_parser(e)
    missing = time_parser(data['summary'][1])
    total = total_time - missing
    name = data['employee_name'].split(' ')
    name = f'{name[0]} {name[-1]}'
    return [name, time_parser(total, True), data['missing_days'], data['proposals'], total]
