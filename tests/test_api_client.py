import datetime as dt
import api_client
import responses


@responses.activate
def test_tiebreak_call():
    responses.add(responses.POST, 'http://padkp.net/api/tiebreak/',
                  match=[
                      responses.json_params_matcher(
                          {'characters': ['bob', 'ted', 'tom']})
                  ])

    resp = api_client.tiebreak(['bob', 'ted', 'tom'], '')

    assert resp.status_code == 200
