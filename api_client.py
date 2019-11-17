import datetime as dt
import requests
import os

API_ROOT = 'padkp.net'


def get_headers(token):
    return {'Authorization':  'Token {}'.format(token)}


def charge_dkp(character, item_name, value, time, notes, token):
    request = {
        "character": character,
        "item_name": item_name,
        "value": value,
        "time": str(time),
        "notes": notes
    }
    return requests.post('http://{}/api/charge_dkp/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_dkp_from_dump(filepath, reason, value, counts_for_attendance, notes, token):
    filename = os.path.split(filepath)[-1]
    dump_contents = open(filepath).read()
    request = {"filename": filename,
                "dump_contents": dump_contents,
                "award_type": reason,
                "value": value,
                "counts_for_attendance": counts_for_attendance,
                "notes": notes
               }
    return requests.post('http://{}/api/upload_dump/'.format(API_ROOT), json=request, headers=get_headers(token))


def create_character(name, character_class, status, token):
    request = {'name': name, 'status': status, 'character_class': character_class}
    return requests.post('http://{}/api/characters/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_dkp(character, value, attendance_value, notes, token):
    time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    request = {'character': character, 'value': value, 'attendance_value': attendance_value, 'time': time, 'notes': notes}
    return requests.post('http://{}/api/awards/'.format(API_ROOT), json=request, headers=get_headers(token))
