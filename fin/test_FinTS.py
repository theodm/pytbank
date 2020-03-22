import pytest

from fin.Caml52Parser import parseCaml52


def test_answer():
    with open("test/example_camt_52.xml") as fp:
        parseCaml52(fp)
