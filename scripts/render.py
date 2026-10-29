#!/usr/bin/env python3
"""EvoMap-inspired SVG primitives, PNG export, and a verified quicksort figure."""

import argparse
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

SKILL_DIR = Path(__file__).resolve().parent.parent
THEME = json.loads((SKILL_DIR / "references/theme.json").read_text(encoding="utf-8"))


def load_theme(value=None):
    """Merge a user theme without executing source files or losing required tokens."""
    theme = {key: dict(items) for key, items in THEME.items()}
    if value is None:
        profile = SKILL_DIR / ".local/profile.json"
        if profile.is_file():
            config = json.loads(profile.read_text(encoding="utf-8"))
            value = config.get("theme_file")
            if value and not Path(value).is_absolute():
                value = SKILL_DIR / value
    if value is not None:
        overrides = value if isinstance(value, dict) else json.loads(Path(value).read_text(encoding="utf-8"))
        if not isinstance(overrides, dict):
            raise ValueError("Theme must be a JSON object")
        for key, items in overrides.items():
            if key not in theme or not isinstance(items, dict):
                raise ValueError("Theme sections must be colors, fonts or geometry")
            theme[key].update(items)
    for token, color in theme["colors"].items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", token) or not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            raise ValueError("Theme colors need safe token names and six-digit HEX values")
    if any(not isinstance(font, str) or not font.strip() for font in theme["fonts"].values()):
        raise ValueError("Theme fonts must be nonempty font-family strings")
    if any(type(n) not in (int, float) or not math.isfinite(n) or n < 0 for n in theme["geometry"].values()):
        raise ValueError("Theme geometry must contain finite nonnegative numbers")
    return theme


def attrs(**values):
    return " ".join(
        f'{key.replace("_", "-")}={quoteattr(str(value))}'
        for key, value in values.items() if value is not None
    )


def rounded_path(points, radius=12):
    if len(points) < 2:
        raise ValueError("An arrow needs at least two points")
    points = [(float(x), float(y)) for x, y in points]
    path = [f"M {points[0][0]:g} {points[0][1]:g}"]
    for before, corner, after in zip(points, points[1:], points[2:]):
        incoming = math.dist(before, corner)
        outgoing = math.dist(corner, after)
        if not incoming or not outgoing:
            continue
        r = min(radius, incoming / 2, outgoing / 2)
        start = tuple(corner[k] + (before[k] - corner[k]) * r / incoming for k in (0, 1))
        end = tuple(corner[k] + (after[k] - corner[k]) * r / outgoing for k in (0, 1))
        path.append(f"L {start[0]:g} {start[1]:g} Q {corner[0]:g} {corner[1]:g} {end[0]:g} {end[1]:g}")
    path.append(f"L {points[-1][0]:g} {points[-1][1]:g}")
    return " ".join(path)


class Figure:
    def __init__(self, width, height, title, description="", theme=None):
        if any(type(n) not in (int, float) or not math.isfinite(n) or n <= 0 for n in (width, height)):
            raise ValueError("Canvas dimensions must be finite and positive")
        self.theme = load_theme(theme)
        self.width, self.height = width, height
        self.title, self.description = title, description
        self.elements = []

    def color(self, token):
        if token == "none":
            return "none"
        if token not in self.theme["colors"]:
            raise ValueError(f"Unknown theme color: {token}")
        return self.theme["colors"][token]

    def text(self, x, y, value, size=20, weight=400, color="ink", align="start", font="body"):
        if font not in self.theme["fonts"] or align not in ("start", "middle", "end"):
            raise ValueError("Unknown font or text alignment")
        self.elements.append(
            f'<text {attrs(x=x, y=y, font_family=self.theme["fonts"][font], font_size=size, font_weight=weight, fill=self.color(color), text_anchor=align)}>{escape(str(value))}</text>'
        )

    def rect(self, x, y, w, h, fill="paper", stroke="line", radius=14, sw=1.5):
        if w <= 0 or h <= 0:
            raise ValueError("Rectangle dimensions must be positive")
        self.elements.append(
            f'<rect {attrs(x=x, y=y, width=w, height=h, rx=radius, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw)}/>'
        )

    def circle(self, x, y, r, fill="paper", stroke="none", sw=1.5):
        if r <= 0:
            raise ValueError("Circle radius must be positive")
        self.elements.append(
            f'<circle {attrs(cx=x, cy=y, r=r, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw)}/>'
        )

    def path(self, d, fill="none", stroke="secondary", sw=2, arrow=False):
        self.elements.append(
            f'<path {attrs(d=d, fill=self.color(fill), stroke=self.color(stroke), stroke_width=sw, stroke_linecap="round", stroke_linejoin="round", marker_end=f"url(#arrow-{stroke})" if arrow else None)}/>'
        )

    def arrow(self, points, color="secondary", sw=2):
        self.path(rounded_path(points), stroke=color, sw=sw, arrow=True)

    def line(self, x1, y1, x2, y2, color="line", sw=1.5):
        self.path(f"M {x1} {y1} L {x2} {y2}", stroke=color, sw=sw)

    def array(self, x, y, values, cell=62, gap=9, pivot=None, active=(), size=30, indices=False, pivot_marker=True):
        active = set(active)
        for index, value in enumerate(values):
            left = x + index * (cell + gap)
            fill = "yellow" if index == pivot else "blueTint" if index in active else "surface"
            self.rect(left, y, cell, cell, fill=fill, stroke="secondary" if index == pivot else "line", radius=10)
            self.text(left + cell / 2, y + cell * 0.64, value, size=size, align="middle", font="latin", weight=500)
            if index in active and index != pivot:
                self.rect(left + 10, y + cell - 5, cell - 20, 3, fill="blue", stroke="none", radius=1.5)
            if index == pivot and pivot_marker:
                cx = left + cell / 2
                self.path(f"M {cx-4} {y-11} L {cx+4} {y-11} L {cx} {y-5} Z", fill="ink", stroke="none")
            if indices:
                self.text(left + cell / 2, y + cell + 21, index, size=14, color="secondary", align="middle", font="latin")
        return len(values) * cell + max(0, len(values) - 1) * gap

    def section(self, x, y, number, title, subtitle=None):
        self.rect(x, y - 20, 6, 24, fill="blue", stroke="none", radius=3)
        self.text(x + 20, y, number, size=22, font="latin", color="secondary", weight=500)
        self.text(x + 62, y, title, size=26, weight=600)
        if subtitle:
            self.text(x, y + 34, subtitle, size=18, color="secondary")

    def svg(self):
        markers = "".join(
            f'<marker id="arrow-{token}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M 1 1 L 7 4 L 1 7" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker>'
            for token, color in self.theme["colors"].items()
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(self.title)}</title>\n'
            f'<desc id="desc">{escape(self.description)}</desc>\n'
            f'<defs>{markers}</defs>\n'
            f'<rect width="{self.width}" height="{self.height}" fill="{self.color("paper")}"/>\n'
            + "\n".join(self.elements) + "\n</svg>\n"
        )


def quicksort_trace(values):
    """Record actual Lomuto comparisons, swaps, recursive ranges, and invariants."""
    array = list(values)

    def visit(lo, hi):
        node = {"lo": lo, "hi": hi, "input": array[lo:hi + 1], "comparisons": []}
        if lo >= hi:
            node.update(leaf=True, output=array[lo:hi + 1])
            return node
        pivot, i = array[hi], lo - 1
        node.update(leaf=False, pivot=pivot)
        for j in range(lo, hi):
            accepted = array[j] <= pivot
            step = {"j": j, "value": array[j], "accepted": accepted, "swap": None}
            if accepted:
                i += 1
                array[i], array[j] = array[j], array[i]
                step["swap"] = [i, j]
            step.update(i=i, array=array[lo:hi + 1])
            node["comparisons"].append(step)
        p = i + 1
        array[p], array[hi] = array[hi], array[p]
        state = array[lo:hi + 1]
        node.update(p=p, pivot_swap=[p, hi], after_partition=state)
        node["invariant"] = (
            all(x <= pivot for x in array[lo:p])
            and array[p] == pivot
            and all(x > pivot for x in array[p + 1:hi + 1])
        )
        if not node["invariant"]:
            raise AssertionError("Partition invariant failed")
        node["left"] = visit(lo, p - 1)
        node["right"] = visit(p + 1, hi)
        node["output"] = array[lo:hi + 1]
        return node

    tree = visit(0, len(array) - 1)
    if array != sorted(values):
        raise AssertionError("Sorted result failed")
    return {"algorithm": "quicksort", "partition": "Lomuto", "pivot_rule": "a[hi]", "left_rule": "<= pivot", "right_rule": "> pivot", "input": list(values), "output": array, "tree": tree}


def flow_card(figure, y, title, code, height=94, accent=None):
    figure.rect(100, y, 294, height)
    if accent:
        figure.circle(122, y + 23, 4, fill=accent)
    figure.text(247, y + 36, title, size=23, weight=500, align="middle")
    figure.text(247, y + 67, code, size=17, font="code", color="secondary", align="middle")


def tree_weight(node):
    return 1 if node["leaf"] else tree_weight(node["left"]) + 1 + tree_weight(node["right"])


def tree_depth(node):
    return 1 if node["leaf"] else 1 + max(tree_depth(node["left"]), tree_depth(node["right"]))


def draw_recursion(figure, root):
    depth = max(tree_depth(root["left"]), tree_depth(root["right"]))
    gap_y = min(106, 294 / max(1, depth - 1))
    cell = 46 if gap_y >= 90 else 34
    gap_x = 6
    positions = []
    edges = []

    def place(node, left, right, level, parent):
        center = (left + right) / 2
        y = 960 + level * gap_y
        positions.append((node, center, y))
        edges.append((parent, (center, y - 15)))
        if node["leaf"]:
            return
        wl, wr = tree_weight(node["left"]), tree_weight(node["right"])
        unit = (right - left) / (wl + 1 + wr)
        place(node["left"], left, left + unit * wl, level + 1, (center, y + cell + 8))
        place(node["right"], right - unit * wr, right, level + 1, (center, y + cell + 8))

    left, right = 530, 1530
    wl, wr = tree_weight(root["left"]), tree_weight(root["right"])
    unit = (right - left) / (wl + 1 + wr)
    place(root["left"], left, left + wl * unit, 0, (1030, 915))
    place(root["right"], right - wr * unit, right, 0, (1030, 915))
    for (x1, y1), (x2, y2) in edges:
        mid = (y1 + y2) / 2
        figure.path(f"M {x1} {y1} C {x1} {mid} {x2} {mid} {x2} {y2}", arrow=True)
    for node, center, y in positions:
        values = node["output"] if node["leaf"] else node["after_partition"]
        if not values:
            figure.rect(center - 22, y, 44, cell, stroke="line", fill="paper", radius=cell / 2)
            figure.text(center, y + cell * 0.65, "∅", size=24, color="secondary", align="middle", font="latin")
        else:
            width = len(values) * cell + (len(values) - 1) * gap_x
            pivot = None if node["leaf"] else node["p"] - node["lo"]
            figure.array(center - width / 2, y, values, cell=cell, gap=gap_x, pivot=pivot, size=26 if cell == 46 else 21)
    figure.text(526, 907, "左区间", size=18, color="secondary")
    figure.text(1536, 907, "右区间", size=18, align="end", color="secondary")


def quicksort_figure(values, theme=None, teaching_page=False):
    if not 2 <= len(values) <= 7:
        raise ValueError("The single-page template accepts 2–7 integers; use a paged spec for larger arrays")
    if any(type(value) is not int for value in values):
        raise ValueError("Quicksort values must be integers")
    if any(len(str(value)) > 3 for value in values):
        raise ValueError("The template accepts at most three printed characters per integer")
    trace = quicksort_trace(values)
    root = trace["tree"]
    pivot, p = root["pivot"], root["p"]
    figure = Figure(1600, 1536, "快速排序：Lomuto 分区与递归流程", "以末尾元素为基准，展示算法控制流程、真实交换状态、递归分区树和最终有序数组。", theme=theme)
    if teaching_page:
        figure.text(64, 43, "ALGORITHMS / 01", size=14, font="latin", color="secondary", weight=500)
        figure.text(1536, 43, "EVOMAP-INSPIRED / DOCUMENT FIGURE", size=14, font="latin", color="secondary", align="end")
        figure.rect(64, 70, 30, 4, fill="blue", stroke="none", radius=2)
        figure.text(64, 134, "快速排序", size=54, weight=600)
        figure.text(332, 132, "QUICKSORT", size=32, font="latin", color="secondary", weight=500)
        figure.rect(1282, 91, 254, 44, fill="paper", radius=22)
        figure.text(1409, 119, "原地分区  /  递归排序", size=18, align="middle")
        figure.text(64, 176, "选定一个基准，把它放到正确位置；再对左右区间重复同一过程。", size=23, color="secondary")
        figure.line(64, 202, 1536, 202)
    figure.line(478, 231, 478, 1312)
    figure.section(64, 251, "01", "控制流程")
    figure.section(526, 251, "02", "一次分区")
    figure.text(810, 250, "Lomuto · 末尾元素作基准", size=18, color="secondary")
    figure.rect(1274, 229, 16, 16, fill="yellow", stroke="secondary", radius=4)
    figure.text(1302, 243, "基准值", size=16, color="secondary")
    figure.rect(1400, 229, 16, 16, fill="blueTint", stroke="line", radius=4)
    figure.rect(1404, 240, 8, 3, fill="blue", stroke="none", radius=1)
    figure.text(1428, 243, "本次交换", size=16, color="secondary")

    figure.rect(122, 299, 250, 70, radius=35)
    figure.text(247, 327, "开始 / 调用", size=20, align="middle", weight=500)
    figure.text(247, 353, "quickSort(a, lo, hi)", size=17, align="middle", font="code", color="secondary")
    figure.arrow([(247, 369), (247, 400)])
    figure.path("M 247 400 L 372 455 L 247 510 L 122 455 Z", fill="paper", stroke="secondary", sw=1.5)
    figure.text(247, 452, "lo ≥ hi ?", size=24, align="middle", font="code", weight=500)
    figure.text(247, 478, "空区间 / 单元素", size=16, align="middle", color="secondary")
    figure.arrow([(372, 455), (438, 455), (438, 1184), (348, 1184)])
    figure.rect(390, 430, 44, 28, stroke="none", radius=0)
    figure.text(412, 451, "是", size=18, align="middle", color="secondary")
    figure.arrow([(247, 510), (247, 552)])
    figure.rect(252, 513, 32, 25, stroke="none", radius=0)
    figure.text(267, 533, "否", size=18, align="middle", color="secondary")
    flow_card(figure, 552, "选择基准值", "pivot = a[hi]", accent="yellow")
    figure.arrow([(247, 646), (247, 692)])
    flow_card(figure, 692, "原地分区，得到下标 p", "左 ≤ pivot；右 > pivot", height=104, accent="blue")
    figure.arrow([(247, 796), (247, 838)])
    flow_card(figure, 838, "递归左区间", "quickSort(a, lo, p-1)")
    figure.arrow([(247, 932), (247, 978)])
    flow_card(figure, 978, "递归右区间", "quickSort(a, p+1, hi)")
    figure.arrow([(247, 1072), (247, 1149)])
    figure.rect(146, 1149, 202, 70, radius=35)
    figure.text(247, 1192, "返回", size=25, align="middle", weight=500)
    figure.text(64, 1263, "递归调用复用同一流程。", size=19, color="secondary")
    figure.text(64, 1295, "空区间 / 单元素：直接返回。", size=19, color="secondary")

    swaps = [step for step in root["comparisons"] if step["swap"] and step["swap"][0] != step["swap"][1]]
    row_count = len(swaps) + 2
    row_gap = 368 / (row_count - 1)
    cell = min(62, row_gap - 20)
    x, y0, array_gap = 636, 301, 9
    for row, step in enumerate([None] + swaps):
        y = y0 + row * row_gap
        state = values if step is None else step["array"]
        active = () if step is None else step["swap"]
        label = "输入" if step is None else f'j = {step["j"]}'
        figure.text(526, y + cell * 0.64, label, size=20, color="secondary", font="body" if step is None else "latin")
        figure.array(x, y, state, cell=cell, gap=array_gap, pivot=len(values) - 1, active=active, size=30 if cell >= 54 else 24, indices=step is None and row_gap >= 83, pivot_marker=step is None)
        if step is None:
            figure.text(1186, y + 25, f"pivot = {pivot}", size=22, font="code", weight=500)
            figure.text(1186, y + 53, "i = lo − 1，向右扫描 j", size=18, color="secondary")
        else:
            figure.text(1186, y + 25, f'{step["value"]} ≤ {pivot}，移入左区间', size=21)
            i, j = step["swap"]
            figure.text(1186, y + 53, f"交换 a[{i}] ↔ a[{j}]", size=18, color="secondary", font="code")
        if row < row_count - 2:
            figure.arrow([(591, y + cell + 3), (591, y + row_gap - 9)], color="blue")
    if swaps:
        previous_y = y0 + len(swaps) * row_gap
        figure.arrow([(591, previous_y + cell + 3), (591, y0 + 368 - 9)], color="blue")
    final_y = y0 + 368
    figure.text(526, final_y + cell * 0.64, "就位", size=20, color="secondary")
    figure.array(x, final_y, root["after_partition"], cell=cell, gap=array_gap, pivot=p, active=root["pivot_swap"], size=30 if cell >= 54 else 24)
    figure.text(1186, final_y + 25, f'交换 a[{p}] ↔ a[{len(values)-1}]', size=20, font="code")
    figure.text(1186, final_y + 53, f"基准 {pivot} 就位，p = {p}", size=20)
    bracket_y = final_y + cell + 13
    for lo, hi, caption in ((0, p - 1, f"≤ {pivot}"), (p, p, "pivot"), (p + 1, len(values) - 1, f"> {pivot}")):
        if lo > hi:
            continue
        left = x + lo * (cell + array_gap)
        right = x + hi * (cell + array_gap) + cell
        figure.path(f"M {left} {bracket_y} V {bracket_y+7} H {right} V {bracket_y}", stroke="secondary", sw=1)
        figure.text((left + right) / 2, bracket_y + 31, caption, size=17, color="secondary", align="middle", font="latin")
    figure.text(526, 800, "仅展示发生跨位置交换的扫描；其余扫描不改变数组顺序。", size=18, color="secondary")
    figure.line(526, 830, 1536, 830)
    figure.section(526, 875, "03", "递归分区")
    figure.text(1030, 907, f"首次分区的基准 {pivot} 已固定，不再进入子区间", size=19, align="middle", color="secondary")
    draw_recursion(figure, root)
    figure.text(526, 1310, "节点显示本次分区后的状态；黄色为本层基准，∅ / 单元素直接返回。", size=18, color="secondary")

    figure.line(64, 1343, 1536, 1343)
    figure.section(64, 1395, "04", "有序结果")
    figure.text(64, 1424, "所有递归调用结束", size=18, color="secondary")
    width = len(values) * 62 + (len(values) - 1) * 9
    figure.array(636 + (488 - width) / 2, 1368, trace["output"], cell=62, gap=9, size=32)
    figure.circle(1440, 1400, 17, fill="green")
    figure.path("M 1433 1400 L 1438 1405 L 1448 1394", stroke="ink", sw=2)
    figure.text(1470, 1407, "完成", size=20)
    if teaching_page:
        figure.line(64, 1460, 1536, 1460)
        figure.text(64, 1494, "时间：平均 O(n log n)，最坏 O(n²)  ·  递归栈：平均 O(log n)，最坏 O(n)", size=18, color="secondary")
        figure.text(1536, 1494, "LOMUTO / WHITE CANVAS", size=14, font="latin", align="end", color="secondary")
    return figure, trace


def from_spec(spec, theme=None):
    figure = Figure(spec["width"], spec["height"], spec.get("title", "文档插图"), spec.get("description", ""), theme=theme if theme is not None else spec.get("theme"))
    methods = {name: getattr(figure, name) for name in ("text", "rect", "circle", "path", "arrow", "array", "section", "line")}
    for element in spec["elements"]:
        element = dict(element)
        kind = element.pop("type")
        if kind not in methods:
            raise ValueError(f"Unsupported element type: {kind}")
        methods[kind](**element)
    return figure


def export(figure, output_dir, name, scale=2, svg_only=False, trace=None):
    if not name or len(name.encode("utf-8")) > 180 or any(not (char.isalnum() or char in "_-") for char in name):
        raise ValueError("Output name must use letters, numbers, underscores or hyphens, without path separators")
    if not math.isfinite(scale) or not 0 < scale <= 4:
        raise ValueError("Scale must be greater than 0 and no greater than 4")
    if figure.width * figure.height * scale * scale > 50_000_000:
        raise ValueError("PNG export is limited to 50 million pixels; split oversized figures")
    output_dir = Path(output_dir).resolve()
    outputs = [output_dir / f"{name}.svg"]
    if not svg_only:
        if not shutil.which("rsvg-convert"):
            raise RuntimeError("PNG export needs rsvg-convert. Install librsvg, or use --svg-only and report that PNG is not yet available.")
        outputs.append(output_dir / f"{name}.png")
    if trace is not None:
        outputs.append(output_dir / f"{name}.trace.json")
    for path in outputs:
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}; choose a new name")
    output_dir.mkdir(parents=True, exist_ok=True)
    svg = figure.svg()
    with outputs[0].open("x", encoding="utf-8") as stream:
        stream.write(svg)
    if trace is not None:
        with (output_dir / f"{name}.trace.json").open("x", encoding="utf-8") as stream:
            json.dump(trace, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    if not svg_only:
        width, height = round(figure.width * scale), round(figure.height * scale)
        with (output_dir / f"{name}.png").open("xb") as stream:
            subprocess.run(["rsvg-convert", "--format=png", "--width", str(width), "--height", str(height), str(outputs[0])], stdout=stream, check=True)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("quicksort", "spec"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--output-dir", type=Path, default=Path("illustrations"))
        subparser.add_argument("--name", default="quicksort-evomap" if command == "quicksort" else "evomap-figure")
        subparser.add_argument("--scale", type=float, default=2)
        subparser.add_argument("--svg-only", action="store_true")
        subparser.add_argument("--theme", type=Path, help="JSON color/font overrides; default theme stays available")
        if command == "quicksort":
            subparser.add_argument("--teaching-page", action="store_true", help="Include the optional visible title and page footer")
            subparser.add_argument("--values", default="6,3,8,1,7,2,5")
        else:
            subparser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "quicksort":
            values = [int(value.strip()) for value in args.values.split(",")]
            figure, trace = quicksort_figure(values, theme=args.theme, teaching_page=args.teaching_page)
        else:
            figure = from_spec(json.loads(args.input.read_text(encoding="utf-8")), theme=args.theme)
            trace = None
        outputs = export(figure, args.output_dir, args.name, args.scale, args.svg_only, trace)
    except (ValueError, KeyError, TypeError, RuntimeError, FileExistsError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
