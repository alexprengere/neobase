from typing import Any, assert_type

from neobase import NeoBase


def test_get_types() -> None:
    G = NeoBase()
    G.set("CDG", city_code="PAR")

    assert_type(G.get("CDG"), dict[str, Any])
    assert_type(G.get("CDG", "name"), str)
    assert_type(G.get("CDG", "page_rank"), float | None)
    assert_type(G.get("CDG", "city_code_list"), list[str])
    assert_type(G.get("___", "name", default=None), str | None)
    assert_type(G.get("___", "page_rank", default=0.0), float | None)
    assert_type(G.get("___", "page_rank", default=None), float | None)
    assert_type(G.get("CDG", "__dup__"), Any)
