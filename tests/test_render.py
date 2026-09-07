"""Wrapping, capping and attribution."""

from hyprmuse import render
from hyprmuse.select import Pick
from hyprmuse.sources.base import Item, Subject


def pick(lines, work="", name="Some Name", note=""):
    return Pick(
        subject=Subject(source="s", source_id="1", name=name, domain="d"),
        item=Item(lines=lines, work=work, note=note),
        lines=lines,
    )


def test_short_lines_are_left_alone():
    assert render.wrap(["short", "also short"], 40) == ["short", "also short"]


def test_long_line_is_folded_to_width():
    long_line = "word " * 40
    out = render.wrap([long_line.strip()], 30)
    assert len(out) > 1
    assert all(len(l) <= 30 for l in out)


def test_existing_line_breaks_are_preserved():
    """Verse and lyric breaks carry meaning and must survive wrapping."""
    lines = ["first line", "second line", "third line"]
    assert render.wrap(lines, 80) == lines


def test_width_zero_disables_wrapping():
    long_line = "x" * 200
    assert render.wrap([long_line], 0) == [long_line]


def test_attribution_with_and_without_work():
    assert render.attribution(pick(["a"], work="A Song")) == "— Some Name: A Song"
    assert render.attribution(pick(["a"])) == "— Some Name"


def test_render_puts_attribution_last():
    out = render.render(pick(["one", "two"], work="W"), width=40)
    assert out.splitlines()[-1] == "— Some Name: W"


def test_render_separates_body_and_attribution_by_blank_line():
    out = render.render(pick(["one"], work="W"), width=40)
    assert out.split("\n") == ["one", "", "— Some Name: W"]


def test_max_lines_caps_the_body():
    out = render.render(pick([f"line {i}" for i in range(20)]),
                        width=40, max_lines=3)
    body = out.split("\n\n")[0]
    assert len(body.splitlines()) == 3


def test_max_lines_zero_means_no_cap():
    out = render.render(pick([f"line {i}" for i in range(10)]),
                        width=40, max_lines=0)
    assert len(out.split("\n\n")[0].splitlines()) == 10


def test_note_included_only_when_requested():
    p = pick(["quote"], note="A Book, 1920")
    assert "A Book, 1920" not in render.render(p, width=40)
    assert "A Book, 1920" in render.render(p, width=40, show_note=True)


def test_wrapped_output_never_exceeds_width():
    p = pick(["A considerably longer sentence that will certainly need to be "
              "folded across several lines to fit."])
    body = render.render(p, width=25, max_lines=0).split("\n\n")[0]
    assert all(len(l) <= 25 for l in body.splitlines())
