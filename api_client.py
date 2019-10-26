import requests
import os
import datetime as dt

API_ROOT = 'padkp:8000'


def charge_dkp(character, item_name, value, time, notes):
    request = {
        "character": character,
        "item_name": item_name,
        "value": value,
        "time": str(time),
        "notes": notes
    }
    return requests.post('http://{}/api/purchases/'.format(API_ROOT), json=request)


def award_dkp(characters, reason, value, time, notes):
    request = {'items': [{"character": character,
                          "time": str(time),
                          "award_type": reason,
                          "value": value,
                          "notes": notes}
                         for character in characters]
               }
    return requests.post('http://{}/api/awards/'.format(API_ROOT), json=request)


def create_character(character, status='REC'):
    request = {'items': [{"name": character,
                          "status": status}]
               }
    return requests.post('http://{}/api/characters/'.format(API_ROOT), json=request)


def known_characters():
    q = requests.get('http://{}/api/characters/'.format(API_ROOT))
    return [doc['name'] for doc in q.json()]


def parse_dump(dumpfile):
    characters = []
    for line in dumpfile:
        characters.append(line.split()[1])
    return characters


def award_dkp_from_dump(filepath, type, value, notes):
    with open(filepath) as f:
        characters = parse_dump(f.readlines())
    create_characters_if_needed(characters)
    filename = os.path.split(filepath)[-1]
    time = dt.datetime.strptime(filename, 'RaidRoster_mangler-%Y%m%d-%H%M%S.txt')
    result = award_dkp(characters, type, value, time, notes)
    return result


def create_characters_if_needed(characters):
    _known_characters = set(known_characters())
    for character in characters:
        if character not in _known_characters:
            create_character(character, status='REC')

