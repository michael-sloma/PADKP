import datetime as dt
import requests
import timestamps
import os
import hashlib
import json

API_ROOT = 'padkp.net'
# API_ROOT = 'localhost:8000'


def get_headers(token):
    return {'Authorization':  'Token {}'.format(token)}

def check_offline(token):
    return token == "offline"

def charge_dkp(character, item_name, value, time, notes, token):
    is_alt = "'s alt" in character
    main_character = character.replace("'s alt", '')
    request = {
        "character": main_character,
        "item_name": item_name,
        "value": value,
        "time": str(time),
        "notes": notes,
        "is_alt": is_alt,
    }
    return requests.post('http://{}/api/charge_dkp/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_dkp_from_dump(filepath, reason, value, counts_for_attendance, waitlist, notes, timestamp, token):
    filename = os.path.split(filepath)[-1]
    dump_contents = open(filepath).read()
    if timestamp is None:
        timestamp = timestamps.time_from_raid_dump(filename)

    time_s = timestamps.time_to_django_repr(timestamp)

    request = {"filename": filename,
               "dump_contents": dump_contents,
               "award_type": reason,
               "value": value,
               "counts_for_attendance": counts_for_attendance,
               "time": time_s,
               "notes": notes,
               "waitlist": waitlist
               }
    return requests.post('http://{}/api/upload_dump/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_casual_dkp_from_dump(filepath, reason, value, counts_for_attendance, waitlist, notes, token):
    filename = os.path.split(filepath)[-1]
    dump_contents = open(filepath).read()

    time = timestamps.time_from_raid_dump(filename)
    time_s = timestamps.time_to_django_repr(time)

    request = {"filename": filename,
               "dump_contents": dump_contents,
               "award_type": reason,
               "value": value,
               "counts_for_attendance": counts_for_attendance,
               "time": time_s,
               "notes": notes,
               "waitlist": waitlist
               }
    return requests.post('http://{}/api/upload_casual_dump/'.format(API_ROOT), json=request, headers=get_headers(token))


def create_character(name, character_class, status, token):
    request = {'name': name, 'status': status,
               'character_class': character_class}
    return requests.post('http://{}/api/characters/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_dkp(character, value, attendance_value, notes, token):
    time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    request = {'character': character, 'value': value,
               'attendance_value': attendance_value, 'time': time, 'notes': notes}
    return requests.post('http://{}/api/awards/'.format(API_ROOT), json=request, headers=get_headers(token))


def tiebreak(characters, token):
    request = {'characters': characters}
    return requests.post('http://{}/api/tiebreak/'.format(API_ROOT), json=request, headers=get_headers(token))

def resolve_flags(players, item_name, item_count, token):
    data = {'players': players, 'item_count': item_count, 'item_name': item_name}

    return requests.post('http://{}/api/resolve_flags/'.format(API_ROOT), json=data, headers=get_headers(token))


def resolve_auction(bids, item_name, item_count, iid, token):
    if check_offline(token):
        return None
    time = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data = {'bids': bids, 'item_count': item_count, 'item_name': item_name,
            'fingerprint': iid, 'time': time}

    return requests.post('http://{}/api/resolve_auction/'.format(API_ROOT), json=data, headers=get_headers(token))


def cancel_auction(bids, item_name, item_count, iid, token):
    if check_offline(token):
        return None
    data = {'fingerprint': iid}

    return requests.post('http://{}/api/cancel_auction/'.format(API_ROOT), json=data, headers=get_headers(token))


def correct_auction(bids, item_name, item_count, winner_bids, iid, token):
    data = {'fingerprint': iid, 'bids': winner_bids}

    return requests.post('http://{}/api/correct_auction/'.format(API_ROOT), json=data, headers=get_headers(token))
