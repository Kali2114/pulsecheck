from app.domain.statistics import uptime_percentage
from tests.domain.utils import create_check_result


def test_uptime_percentage_returns_none_for_empty_list():
    assert uptime_percentage([]) is None


def test_uptime_percentage_returns_100_when_all_up():
    up_result = create_check_result()
    uptime = uptime_percentage([up_result])

    assert uptime == 100


def test_uptime_percentage_returns_0_when_all_down():
    down_result = create_check_result(is_up=False)
    uptime = uptime_percentage([down_result])

    assert uptime == 0


def test_uptime_percentage_returns_50_when_half_up():
    up_result = create_check_result()
    down_result = create_check_result(is_up=False)
    uptime = uptime_percentage([up_result, down_result])

    assert uptime == 50
