import json
import pytest


@pytest.fixture
def ndjson_content():
    line = """{"uuid": "9fd9a92e-2560-4e77-81d4-b2e955800092", "schemaId": "ckaeasyfk004y0y7wyye5epgu", "dataRow": {"id": "ck7kftpan8ir008910yf07r9c"}, "bbox": {"top": 48, "left": 58, "height": 865, "width": 1512}}
{"uuid": "29b878f3-c2b4-4dbf-9f22-a795f0720125", "schemaId": "ckapgvrl7007q0y7ujkjkaaxt", "dataRow": {"id": "ck7kftpan8ir008910yf07r9c"}, "polygon": [{"x": 147.692, "y": 118.154}, {"x": 142.769, "y": 404.923}, {"x": 57.846, "y": 318.769}, {"x": 28.308, "y": 169.846}]}"""
    expected_objects = [{
        'uuid': '9fd9a92e-2560-4e77-81d4-b2e955800092',
        'schemaId': 'ckaeasyfk004y0y7wyye5epgu',
        'dataRow': {
            'id': 'ck7kftpan8ir008910yf07r9c'
        },
        'bbox': {
            'top': 48,
            'left': 58,
            'height': 865,
            'width': 1512
        }
    }, {
        'uuid':
            '29b878f3-c2b4-4dbf-9f22-a795f0720125',
        'schemaId':
            'ckapgvrl7007q0y7ujkjkaaxt',
        'dataRow': {
            'id': 'ck7kftpan8ir008910yf07r9c'
        },
        'polygon': [{
            'x': 147.692,
            'y': 118.154
        }, {
            'x': 142.769,
            'y': 404.923
        }, {
            'x': 57.846,
            'y': 318.769
        }, {
            'x': 28.308,
            'y': 169.846
        }]
    }]

    return line, expected_objects


@pytest.fixture
def ndjson_content_with_nonascii_and_line_breaks():
    line = '{"id": "2489651127", "type": "PushEvent", "actor": {"id": 1459915, "login": "xtuaok", "gravatar_id": "", "url": "https://api.github.com/users/xtuaok", "avatar_url": "https://avatars.githubusercontent.com/u/1459915?"}, "repo": {"id": 6719841, "name": "xtuaok/twitter_track_following", "url": "https://api.github.com/repos/xtuaok/twitter_track_following"}, "payload": {"push_id": 536864008, "size": 1, "distinct_size": 1, "ref": "refs/heads/xtuaok", "head": "afb8afe306c7893d93d383a06e4d9df53b41bf47", "before": "4671b4868f1a060f2ed64d8268cd22d514a84e63", "commits": [{"sha": "afb8afe306c7893d93d383a06e4d9df53b41bf47", "author": {"email": "47cb89439b2d6961b59dff4298e837f67aa77389@gmail.com", "name": "Tomonori Tamagawa"}, "message": "Update ID 949438177,, - screen_name: chomado, - name: ちょまど@初詣おみくじ凶, - description: ( *ﾟ▽ﾟ* っ)З腐女子！絵描き！| H26新卒文系SE (入社して4ヶ月目の8月にSIer(適応障害になった)を辞職し開発者に転職) | H26秋応用情報合格！| 自作bot (in PHP) chomado_bot | プログラミングガチ初心者, - location:", "distinct": true, "url": "https://api.github.com/repos/xtuaok/twitter_track_following/commits/afb8afe306c7893d93d383a06e4d9df53b41bf47"}]}, "public": true, "created_at": "2015-01-01T15:00:10Z"}'
    expected_objects = [{
        'id': '2489651127',
        'type': 'PushEvent',
        'actor': {
            'id': 1459915,
            'login': 'xtuaok',
            'gravatar_id': '',
            'url': 'https://api.github.com/users/xtuaok',
            'avatar_url': 'https://avatars.githubusercontent.com/u/1459915?'
        },
        'repo': {
            'id': 6719841,
            'name': 'xtuaok/twitter_track_following',
            'url': 'https://api.github.com/repos/xtuaok/twitter_track_following'
        },
        'payload': {
            'push_id':
                536864008,
            'size':
                1,
            'distinct_size':
                1,
            'ref':
                'refs/heads/xtuaok',
            'head':
                'afb8afe306c7893d93d383a06e4d9df53b41bf47',
            'before':
                '4671b4868f1a060f2ed64d8268cd22d514a84e63',
            'commits': [{
                'sha':
                    'afb8afe306c7893d93d383a06e4d9df53b41bf47',
                'author': {
                    'email':
                        '47cb89439b2d6961b59dff4298e837f67aa77389@gmail.com',
                    'name':
                        'Tomonori Tamagawa'
                },
                'message':
                    'Update ID 949438177,, - screen_name: chomado, - name: ちょまど@初詣おみくじ凶, - description: ( *ﾟ▽ﾟ* っ)З腐女子！絵描き！| H26新卒文系SE (入社して4ヶ月目の8月にSIer(適応障害になった)を辞職し開発者に転職) | H26秋応用情報合格！| 自作bot (in PHP) chomado_bot | プログラミングガチ初心者, - location:',
                'distinct':
                    True,
                'url':
                    'https://api.github.com/repos/xtuaok/twitter_track_following/commits/afb8afe306c7893d93d383a06e4d9df53b41bf47'
            }]
        },
        'public': True,
        'created_at': '2015-01-01T15:00:10Z'
    }]
    return line, expected_objects


@pytest.fixture
def generate_random_ndjson(rand_gen):

    def _generate_random_ndjson(lines: int = 10):
        return [
            json.dumps({"data_row": {
                "id": rand_gen(str)
            }}) for _ in range(lines)
        ]

    return _generate_random_ndjson


@pytest.fixture
def mock_response():

    class MockResponse:

        def __init__(self, text: str, exception: Exception = None) -> None:
            self._text = text
            self._exception = exception

        @property
        def text(self):
            return self._text

        @property
        def content(self):
            return self._text

        def raise_for_status(self):
            if self._exception:
                raise self._exception

    return MockResponse
