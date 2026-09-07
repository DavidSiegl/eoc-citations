"""Quote selection: slicing, weighting, filtering, repeat avoidance."""

import json

from hyprmuse import config, library, select
from hyprmuse.sources.base import Item
from tests.conftest import make_subject


def cfg(**over):
    base = config.load_config()
    base.update(over)
    return base


def test_sliceable_item_yields_a_contiguous_window():
    item = Item(lines=[f"l{i}" for i in range(10)], atomic=False)
    import random
    lines = select._extract(item, 3, random.Random(0))
    assert len(lines) == 3
    start = item.lines.index(lines[0])
    assert item.lines[start:start + 3] == lines


def test_atomic_item_is_returned_whole():
    item = Item(lines=[f"l{i}" for i in range(10)], atomic=True)
    import random
    assert select._extract(item, 3, random.Random(0)) == item.lines


def test_short_item_returns_all_its_lines():
    item = Item(lines=["only", "two"], atomic=False)
    import random
    assert select._extract(item, 5, random.Random(0)) == ["only", "two"]


def test_pick_returns_none_on_empty_library():
    assert select.pick(cfg(), num_lines=3) is None


def test_pick_returns_a_quote():
    library.save(make_subject())
    chosen = select.pick(cfg(), num_lines=3)
    assert chosen is not None
    assert chosen.lines
    assert chosen.subject.name == "Test Subject"


def test_seed_makes_selection_deterministic():
    library.save(make_subject(n_items=8))
    a = select.pick(cfg(), num_lines=3, seed=11)
    b = select.pick(cfg(), num_lines=3, seed=11)
    assert a.lines == b.lines and a.item.work == b.item.work


def test_domain_and_source_filters():
    library.save(make_subject(source="genius", source_id="1", domain="music"))
    library.save(make_subject(source="poetrydb", source_id="2", domain="poetry",
                              name="A Poet"))
    assert select.pick(cfg(), num_lines=2, domain="poetry").subject.domain == "poetry"
    assert select.pick(cfg(), num_lines=2, source="genius").subject.source == "genius"


def test_subject_filter_matches_on_name():
    library.save(make_subject(source_id="1", name="Alpha Band"))
    library.save(make_subject(source="poetrydb", source_id="2", name="Beta Poet"))
    assert select.pick(cfg(), num_lines=2, subject="beta").subject.name == "Beta Poet"


def test_disabled_subject_is_excluded():
    library.save(make_subject(source="genius", source_id="1"))
    conf = cfg()
    conf["subjects"] = {"genius:1": {"enabled": False}}
    assert select.candidates(conf) == []


def test_subject_weighting_balances_unequal_libraries():
    """A huge subject must not swamp a small one under the default weighting."""
    library.save(make_subject(source="genius", source_id="1", name="Big",
                              n_items=200))
    library.save(make_subject(source="poetrydb", source_id="2", name="Small",
                              n_items=2))
    picks = [select.pick(cfg(avoid_repeats=0), num_lines=2).subject.name
             for _ in range(300)]
    assert 0.3 < picks.count("Small") / len(picks) < 0.7


def test_quote_weighting_favours_the_larger_subject():
    library.save(make_subject(source="genius", source_id="1", name="Big",
                              n_items=200))
    library.save(make_subject(source="poetrydb", source_id="2", name="Small",
                              n_items=2))
    picks = [select.pick(cfg(weighting="quote", avoid_repeats=0),
                         num_lines=2).subject.name for _ in range(300)]
    assert picks.count("Big") > picks.count("Small") * 5


def test_explicit_weight_zero_excludes_a_subject():
    library.save(make_subject(source="genius", source_id="1", name="Muted"))
    library.save(make_subject(source="poetrydb", source_id="2", name="Heard"))
    conf = cfg(avoid_repeats=0)
    conf["subjects"] = {"genius:1": {"weight": 0}}
    names = {select.pick(conf, num_lines=2).subject.name for _ in range(60)}
    assert names == {"Heard"}


def test_recent_history_is_written_and_capped():
    library.save(make_subject(n_items=30))
    for _ in range(15):
        select.pick(cfg(avoid_repeats=5), num_lines=2)
    recent = json.loads(config.RECENT_FILE.read_text(encoding="utf-8"))
    assert len(recent) == 5


def test_seeded_pick_does_not_pollute_history():
    library.save(make_subject())
    select.pick(cfg(), num_lines=2, seed=3)
    assert not config.RECENT_FILE.exists()


def test_repeats_avoided_within_the_window():
    library.save(make_subject(n_items=40, n_lines=3, atomic=True))
    seen = [select.pick(cfg(avoid_repeats=20), num_lines=3).fingerprint()
            for _ in range(20)]
    assert len(set(seen)) == len(seen)


def test_fingerprint_is_stable_and_content_dependent():
    library.save(make_subject())
    a = select.pick(cfg(), num_lines=3, seed=5)
    b = select.pick(cfg(), num_lines=3, seed=5)
    assert a.fingerprint() == b.fingerprint()


def test_unreadable_recent_file_is_tolerated():
    library.save(make_subject())
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.RECENT_FILE.write_text("garbage", encoding="utf-8")
    assert select.pick(cfg(), num_lines=2) is not None


def test_subjects_with_no_items_are_skipped():
    library.save(make_subject(items=[]))
    assert select.pick(cfg(), num_lines=2) is None
