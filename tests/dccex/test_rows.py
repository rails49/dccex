"""The five readers of the desired half and the fast clock's, a table per
reader: what each row reads as, and what reads as nothing.

The cases for the five are `control`'s for the same functions at 8950c92
(`tests/lib/test_payload.py`), where they were taken from.
"""

from tc49.lib.inventory import OFF, ON

from dccex.rows import (
    clock,
    commanded_power,
    desired_aspect,
    desired_function,
    desired_position,
    desired_speed,
)


def test_a_power_value_reads_as_the_value_it_asks_for() -> None:
    assert commanded_power({"power": "on"}) == ON
    assert commanded_power({"power": "off"}) == OFF


def test_a_power_value_that_cannot_be_read_reads_as_none() -> None:
    refused: list[object] = [
        "on",  # not an object at all
        ["on"],  # nor a list of its fields
        {},  # no power
        {"power": None},
        {"power": 1},  # not a string
        {"power": "ON"},  # a value outside the closed set
        {"power": "stopped"},  # an emergency stop is `off` (control ADR-0078)
    ]
    for payload in refused:
        assert commanded_power(payload) is None, payload


def test_a_desired_speed_reads_as_the_fraction_it_states() -> None:
    assert desired_speed({"addr": "3", "speed": 0.5}) == 0.5
    assert desired_speed({"addr": "3", "speed": -1.0}) == -1.0
    assert desired_speed({"addr": "3", "speed": 0}) == 0.0


def test_a_desired_speed_past_the_range_is_still_read() -> None:
    assert desired_speed({"addr": "3", "speed": 4.0}) == 4.0


def test_a_boolean_is_not_a_speed() -> None:
    assert desired_speed({"addr": "3", "speed": True}) is None
    assert desired_speed({"addr": "3", "speed": False}) is None


def test_a_desired_speed_that_cannot_be_read_reads_as_none() -> None:
    unreadable: list[object] = [
        "0.5",  # not an object at all
        {},  # no field
        {"speed": None},
        {"speed": "fast"},
    ]
    for payload in unreadable:
        assert desired_speed(payload) is None, payload


def test_a_position_and_an_aspect_read_as_the_names_they_carry() -> None:
    assert desired_position({"addr": "dccex/5", "position": "thrown"}) == "thrown"
    assert desired_aspect({"addr": "dccex/40", "aspect": "caution"}) == "caution"


def test_a_position_or_an_aspect_that_is_no_name_reads_as_none() -> None:
    unreadable: list[object] = ["thrown", {}, {"position": None}, {"position": 5}]
    for payload in unreadable:
        assert desired_position(payload) is None, payload
    assert desired_aspect({"addr": "dccex/40"}) is None
    assert desired_aspect({"addr": "dccex/40", "aspect": 1}) is None


def test_a_desired_function_is_a_boolean_and_a_word_is_no_value() -> None:
    assert desired_function({"addr": "3", "function": "2", "value": True}) is True
    assert desired_function({"addr": "3", "function": "2", "value": False}) is False
    unreadable: list[object] = [
        True,  # not an object at all
        {"addr": "3", "function": "2"},
        {"addr": "3", "function": "2", "value": "on"},
        {"addr": "3", "function": "2", "value": "off"},
        {"addr": "3", "function": "2", "value": 1},
        {"addr": "3", "function": "2", "value": None},
    ]
    for payload in unreadable:
        assert desired_function(payload) is None, payload


def test_a_clock_reads_as_its_time_and_its_speed_up() -> None:
    assert clock({"at": 1.0, "time": 23400, "speed_up": 4}) == (23400, 4)
    assert clock({"at": 1.0, "time": 86399, "speed_up": 0.5}) == (86399, 0.5)


def test_a_clock_that_is_no_time_of_day_or_no_speed_up_reads_as_none() -> None:
    unreadable: list[object] = [
        23400,
        {"speed_up": 4},
        {"time": 23400},
        {"time": 86400, "speed_up": 4},
        {"time": -1, "speed_up": 4},
        {"time": 23400.5, "speed_up": 4},
        {"time": True, "speed_up": 4},
        {"time": 23400, "speed_up": 0},
        {"time": 23400, "speed_up": True},
        {"time": 23400, "speed_up": "4"},
        {"time": 23400, "speed_up": float("inf")},
    ]
    for payload in unreadable:
        assert clock(payload) is None, payload
