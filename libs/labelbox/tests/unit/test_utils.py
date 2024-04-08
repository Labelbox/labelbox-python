import pytest
from labelbox.utils import format_iso_datetime, format_iso_from_string


@pytest.mark.parametrize('datetime_str, expected_datetime_str',
                         [('2011-11-04T00:05:23Z', '2011-11-04T00:05:23Z'),
                          ('2011-11-04T00:05:23+00:00', '2011-11-04T00:05:23Z'),
                          ('2011-11-04T00:05:23+05:00', '2011-11-03T19:05:23Z'),
                          ('2011-11-04T00:05:23', '2011-11-04T00:05:23Z')])
def test_datetime_parsing(datetime_str, expected_datetime_str):
    # NOTE I would normally not take 'expected' using another function from sdk code, but in this case this is exactly the usage in _validate_parse_datetime
    assert format_iso_datetime(
        format_iso_from_string(datetime_str)) == expected_datetime_str
