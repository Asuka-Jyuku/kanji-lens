"""SVG path data to polylines: the shape of a KanjiVG stroke.

KanjiVG draws each stroke as one path of cubic Béziers (commands M, m, C, c, S and s; L and l
are read too). Curves become points along them; the first point gives the stroke's direction.
"""

import re

type Point = tuple[float, float]

# Points taken along each Bézier segment, after its start point.
SAMPLES_PER_CURVE = 8

_TOKEN = re.compile(r"[MmCcSsLl]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[A-Za-z]")
_ARGUMENTS = {"M": 2, "L": 2, "C": 6, "S": 4}


def path_to_polyline(data: str, samples_per_curve: int = SAMPLES_PER_CURVE) -> list[Point]:
    """The points of one SVG path, its curves sampled at samples_per_curve points each.

    Raises ValueError for a command outside M, C, S and L (either case), a missing number or
    a path that does not start with a move.
    """
    tokens = _TOKEN.findall(data)
    points: list[Point] = []
    current: Point = (0.0, 0.0)
    last_control: Point | None = None  # second control point of the last curve, for S
    command = ""
    position = 0
    while position < len(tokens):
        token = tokens[position]
        if token.isalpha():
            if token.upper() not in _ARGUMENTS:
                raise ValueError(f"unsupported path command {token!r}")
            command = token
            position += 1
        if not points and command.upper() != "M":
            raise ValueError("a path must start with a move (M or m)")
        count = _ARGUMENTS[command.upper()]
        numbers = tokens[position : position + count]
        if len(numbers) < count or any(n.isalpha() for n in numbers):
            raise ValueError(f"command {command!r} needs {count} numbers")
        position += count
        values = [float(n) for n in numbers]
        relative = command.islower()
        offset = current if relative else (0.0, 0.0)
        coordinates = [
            (offset[0] + values[i], offset[1] + values[i + 1]) for i in range(0, count, 2)
        ]
        match command.upper():
            case "M":
                if points:
                    raise ValueError("a stroke is one path: a second move is not supported")
                current = coordinates[0]
                points.append(current)
                last_control = None
                # Pairs after a move are lines (SVG 1.1, "moveto").
                command = "l" if relative else "L"
            case "L":
                current = coordinates[0]
                points.append(current)
                last_control = None
            case "C":
                first, second, end = coordinates
                points.extend(_cubic(current, first, second, end, samples_per_curve))
                current, last_control = end, second
            case "S":
                # The first control point mirrors the last one across the current point.
                if last_control is None:
                    first = current
                else:
                    first = (2 * current[0] - last_control[0], 2 * current[1] - last_control[1])
                second, end = coordinates
                points.extend(_cubic(current, first, second, end, samples_per_curve))
                current, last_control = end, second
    if not points:
        raise ValueError("the path has no points")
    return points


def _cubic(start: Point, first: Point, second: Point, end: Point, samples: int) -> list[Point]:
    curve: list[Point] = []
    for step in range(1, samples + 1):
        t = step / samples
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t**2, t**3
        curve.append(
            (
                a * start[0] + b * first[0] + c * second[0] + d * end[0],
                a * start[1] + b * first[1] + c * second[1] + d * end[1],
            )
        )
    return curve
