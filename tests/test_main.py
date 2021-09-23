import pytest
from src.main import to_xml_name


def test_to_xml_name():
    assert (
        to_xml_name(
            "200500000021æ14/09/2021æ00000088èCorporate Bond Ratingsè14/09/2021"
        )
        == "200500000021-14092021-00000088-Corporate Bond Ratings-14092021.xml"
    )
    assert (
        to_xml_name(
            "200700000001æ14/09/2021æ00000082èGovernment Securities (Conventional) Newè14/09/2021"
        )
        == "200700000001-14092021-00000082-Government Securities (Conventional) New-14092021.xml"
    )
