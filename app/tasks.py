from datetime import datetime, timedelta
from celery import shared_task


from .models import Shift, Department, Employee, Journey
from .utils import *


@shared_task
def update_cards():
    today = str(datetime.today())
    payload = {
        "report": {
            "start_date": today,
            "end_date": today,
            "group_by": "employee",
            "row_filters": "",
            "columns": "employee_name,team_name,time,source,original_address,edited_address,manually_changed,time_card_index,time_cards,shift_name",
            "format": "json"
        }
    }

    data = req('reports/time_cards', payload)
    g = Group()
    groups = None
    if data['data']:
        for r in data['data'][0]:
            time_card = card_parser(r['data'])
            if time_card:
                groups = g.get_group(r['data'][0]['team_name'], time_card)

            extra = extra_time(r['data'])
            if extra:
                groups = g.get_group(r['data'][0]['team_name'], extra)
        if groups:
            for group in groups.items():
                if group[1]['active']:
                    send_message(group[1]['data'], group[1]['chat_id'])


@shared_task
def update_shift():
    data = req('shifts?attributes=id,name,days')
    for r in data['shifts']:
        times = []
        for day in r['days']:
            if day['periods']:
                count = 0
                for p in day['periods']:
                    count += time_parser(p['leave_time']) - time_parser(p['enter_time'])
                times.append(count)
            else:
                times.append(0)
        Shift.objects.update_or_create(pk=r['id'], defaults={'periods': times, 'name': r['name']})


@shared_task
def update_departments():
    data = req('teams?attributes=id,name,department')
    for row in data['teams']:
        dep, c = Department.objects.update_or_create(pk=row['department']['id'], name=row['department']['name'])
        Team.objects.update_or_create(pk=row['id'], defaults={'name': row['name'], 'department': dep})


@shared_task
def update_extra_time():
    start_date, end_date = work_days()
    g = Group()
    groups = None

    payload = {
        "report": {
            "start_date": start_date,
            "end_date": end_date,
            "group_by": "",
            "columns": "employee_name,extra_time,missing_days,proposals,team_name,summary,total_time",
            "format": "json"}}
    data = req('reports/period_summaries', payload)['data'][0]
    if data:
        data = data[0]['data']
        for r in data:
            row = extra_time_table(r)
            if row:
                groups = g.get_group(r['team_name'], row)
        if groups:
            for group in groups.items():
                if group[1]['active']:
                    send_table(group[1]['data'], group[1]['chat_id'])


@shared_task
def update_occurrences():
    yesterday = str(datetime.today() - timedelta(days=1))
    payload = {
        "report": {
            "start_date": yesterday,
            "end_date": yesterday,
            "columns": "employee_name,date,team_name",
            "format": "json"
        }
    }
    data = req('reports/occurrences', payload)['data'][0]
    if data:
        data = data[0]['data']
        g = Group()
        groups = None
        for r in data:
            msg = f'<b>{r["employee_name"]}</b>\n&#x203C;<i>{r["employee_name"]}</i>'
            groups = g.get_group(r['team_name'], msg)
        if groups:
            for group in groups.items():
                if group[1]['active']:
                    msg = group[1]['data']
                    send_message(msg, group[1]['chat_id'], f'<pre>&#128467; {data[0]["date"]}</pre>')


@shared_task
def update_signatures():
    start_date, end_date = work_days(1)
    payload = {
        "report": {
            "start_date": start_date,
            "end_date": end_date,
            "columns": "team_name,signed",
            "row_filters": "",
            "format": "json"
        }
    }
    data = req('reports/signatures', payload)['data'][0]
    if data:
        data = data[0]['data']
        g = Group()
        groups = None
        for r in data:
            if ['signed'] == 'Sim':
                msg = f'<b>{r["employee_name"]}</b>'
                t = r['team_name'].split('-')
                team = f"{t[1].strip()} -{t[2]}-{t[3]}"
                groups = g.get_group(team, msg)
        if groups:
            for group in groups.items():
                if group[1]['active']:
                    msg = group[1]['data']
                    send_message(msg, group[1]['chat_id'], '<pre>&#128395; Assinaturas pendentes</pre>')


@shared_task
def update_employees():
    employees = req('employees?active=true&attributes=id,first_name,last_name,team')['employees']
    for employee in employees:
        team = Team.objects.get(pk=employee['team']['id'])
        Employee.objects.update_or_create(pk=employee['id'],
                                          defaults={'name': f"{employee['first_name']} {employee['last_name']}",
                                          'team': team})


@shared_task
def update_journey():
    start_date, end_date = work_days()
    payload = {
        "report": {
            "start_date": start_date,
            "end_date": end_date,
            "group_by": "",
            "row_filters": "",
            "columns": "employee_name,extra_time,missing_days,proposals,team_name,summary,total_time",
            "format": "json"
        }
    }
    data = req('reports/period_summaries', payload)['data'][0]
    timezone = pytz.timezone(settings.TIME_ZONE)
    date = datetime.now() - timedelta(days=1)
    dt = timezone.localize(date)
    if data:
        data = data[0]['data']
        for r in data:
            employee = Employee.objects.get(name=r['employee_name'])
            h1, h2, h3, h4 = [time_parser(e) for e in r['extra_time']]
            interval, missing, normal = [time_parser(e) for e in r['summary']]
            Journey.objects.create(employee=employee,
                                   h1=h1,
                                   h2=h2,
                                   h3=h3,
                                   h4=h4,
                                   interval=interval,
                                   missing=missing,
                                   normal=normal,
                                   total_time=time_parser(r['total_time']),
                                   missing_days=r['missing_days'],
                                   proposals=r['proposals'],
                                   dt=dt)
