import requests
import os
import datetime as dt

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
    return requests.post('http://{}/api/purchases/'.format(API_ROOT), json=request, headers=get_headers(token))


def award_dkp(characters, reason, value, attendance_value, time, notes, token):
    request = {'items': [{"character": character,
                          "time": str(time),
                          "award_type": reason,
                          "value": value,
                          "attendance_value": attendance_value,
                          "notes": notes}
                         for character in characters]
               }
    return requests.post('http://{}/api/awards/'.format(API_ROOT), json=request, headers=get_headers(token))


def create_character(character, token, status='REC'):
    request = {'items': [{"name": character,
                          "status": status}]
               }
    return requests.post('http://{}/api/characters/'.format(API_ROOT), json=request, headers=get_headers(token))


def known_characters(token):
    q = requests.get('http://{}/api/characters/'.format(API_ROOT), headers=get_headers(token))
    return [doc['name'] for doc in q.json()]


def parse_dump(dumpfile):
    characters = []
    for line in dumpfile:
        characters.append(line.split()[1])
    return characters


def award_dkp_from_dump(filepath, type, value, attendance_value, notes, token):
    with open(filepath) as f:
        characters = parse_dump(f.readlines())
    create_characters_if_needed(characters, token)
    filename = os.path.split(filepath)[-1]
    time = dt.datetime.strptime(filename, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')
    result = award_dkp(characters, type, value, attendance_value, time, notes, token=token)
    return result


def create_characters_if_needed(characters, token):
    _known_characters = set(known_characters(token))
    for character in characters:
        if character not in _known_characters:
            create_character(character, token, status='REC')

