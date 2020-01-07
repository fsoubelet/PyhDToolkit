import pytest

from pyhdtoolkit.utils.operations import StringOperations


def test_camel_case_from_snake_case():
    assert StringOperations.camel_case("a_snake_case_name") == "aSnakeCaseName"


def test_camel_case_from_title_case():
    assert StringOperations.camel_case("A Title Case Name") == "aTitleCaseName"


def test_camel_case_no_change():
    assert StringOperations.camel_case("thatshouldstaythesame") == "thatshouldstaythesame"


def test_capitalize_no_lower_rest():
    assert StringOperations.capitalize("astringtocapitalize") == "Astringtocapitalize"


def test_capitalize_with_lower_rest():
    assert StringOperations.capitalize("astRIngTocApItalizE", lower_rest=True) == "Astringtocapitalize"


def test_is_anagram_true():
    assert StringOperations.is_anagram("Justin Timberlake", "I'm a jerk but listen") is True


def test_is_anagram_harry_potter_true():
    assert StringOperations.is_anagram("Tom Marvolo Riddle", "I am Lord Voldemort") is True


def test_is_anagram_false():
    assert StringOperations.is_anagram("A first string", "Definitely not an anagram") is False


def test_is_palindrome_true():
    assert StringOperations.is_palindrome("racecar") is True


def test_is_palindrome_false():
    assert StringOperations.is_palindrome("definitelynot") is False


def test_kebab_case_from_camel_case():
    assert StringOperations.kebab_case("camel Case") == "camel-case"


def test_kebab_case_from_snake_case():
    assert StringOperations.kebab_case("snake_case") == "snake-case"


def test_snake_case_from_camel_case():
    assert StringOperations.snake_case("camelCase") == "camelcase"


def test_snake_case_from_a_sentence():
    assert StringOperations.snake_case("A bunch of words") == "a_bunch_of_words"
