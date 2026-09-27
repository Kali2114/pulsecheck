import pytest

from app.domain.statistics import average_response_time, uptime_percentage
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


def test_average_response_time_returns_none_for_empty_list():
    assert average_response_time([]) is None


def test_average_response_time_uses_only_up_checks():
    fast_up_result = create_check_result(response_time_ms=200)
    slow_up_result = create_check_result(response_time_ms=300)
    timeout_result = create_check_result(is_up=False, response_time_ms=None)
    error_result = create_check_result(is_up=False, response_time_ms=200)
    average = average_response_time(
        [fast_up_result, slow_up_result, timeout_result, error_result]
    )

    assert average == 250


def test_average_response_time_returns_none_when_all_down():
    timeout_result = create_check_result(is_up=False, response_time_ms=None)
    error_result = create_check_result(is_up=False, response_time_ms=200)
    average = average_response_time([timeout_result, error_result])

    assert average is None


def test_average_response_time_returns_own_time_for_single_result():
    up_result = create_check_result(response_time_ms=180)
    average = average_response_time([up_result])

    assert average == 180


def test_average_response_time_returns_uneven_mean():
    first_result = create_check_result(response_time_ms=200)
    second_result = create_check_result(response_time_ms=200)
    third_result = create_check_result(response_time_ms=100)
    average = average_response_time([first_result, second_result, third_result])

    assert average == pytest.approx(500 / 3)
