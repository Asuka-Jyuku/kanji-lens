import pytest

from kanjilens_ml.stroke_order.svg_path import path_to_polyline


def approx(points: list[tuple[float, float]]) -> object:
    return [pytest.approx(point) for point in points]


def test_a_cubic_curve_is_sampled_from_its_start_to_its_end() -> None:
    # A straight "curve": control points on the line, so the samples are easy to check.
    points = path_to_polyline("M0,0C10,0,20,0,30,0", samples_per_curve=3)

    assert points == approx([(0, 0), (10, 0), (20, 0), (30, 0)])


def test_relative_commands_count_from_the_current_point() -> None:
    absolute = path_to_polyline("M10,10C10,20,10,30,10,40C20,40,30,40,40,40")
    relative = path_to_polyline("m10,10c0,10,0,20,0,30c10,0,20,0,30,0")

    assert relative == approx(absolute)


def test_numbers_glued_by_their_sign_and_repeated_commands_are_read() -> None:
    # KanjiVG writes "1.74,2.75-0.16" and repeats a command's numbers without the letter.
    glued = path_to_polyline("M0,0c0,1-0,2,0,3 0,1,0,2,0,3", samples_per_curve=1)

    assert glued == approx([(0, 0), (0, 3), (0, 6)])


def test_a_smooth_curve_mirrors_the_last_control_point() -> None:
    smooth = path_to_polyline("M0,0C0,10,10,10,10,0S20,-10,20,0", samples_per_curve=2)
    explicit = path_to_polyline("M0,0C0,10,10,10,10,0C10,-10,20,-10,20,0", samples_per_curve=2)

    assert smooth == approx(explicit)


def test_a_smooth_curve_with_no_curve_before_starts_at_the_current_point() -> None:
    smooth = path_to_polyline("M0,0s10,10,20,0", samples_per_curve=2)
    explicit = path_to_polyline("M0,0C0,0,10,10,20,0", samples_per_curve=2)

    assert smooth == approx(explicit)


def test_lines_and_the_pairs_after_a_move_are_straight_segments() -> None:
    assert path_to_polyline("M0,0 5,0L5,5l-5,0") == approx([(0, 0), (5, 0), (5, 5), (0, 5)])


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ("M0,0Z", "unsupported"),
        ("M0,0A1,1,0,0,1,5,5", "unsupported"),
        ("C0,0,1,1,2,2", "start with a move"),
        ("M0,0C1,1,2", "needs 6 numbers"),
        ("M0,0C1,1M5,5", "needs 6 numbers"),
        ("M0,0L1,1M5,5", "second move"),
        ("", "no points"),
    ],
)
def test_a_path_outside_what_kanjivg_uses_is_refused(data: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        path_to_polyline(data)
