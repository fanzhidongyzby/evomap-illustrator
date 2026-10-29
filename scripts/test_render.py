#!/usr/bin/env python3
"""Run with Python's standard library; PNG smoke test needs rsvg-convert."""

import importlib.util
import itertools
import json
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

script = Path(__file__).resolve().with_name("render.py")
spec = importlib.util.spec_from_file_location("evomap_render", script)
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)


class AlgorithmTests(unittest.TestCase):
    def check_tree(self, node):
        self.assertEqual(node["output"], sorted(node["input"]))
        if node["leaf"]:
            self.assertLessEqual(len(node["input"]), 1)
            return
        p, lo, hi = node["p"], node["lo"], node["hi"]
        state, pivot = node["after_partition"], node["pivot"]
        self.assertTrue(node["invariant"])
        self.assertEqual(state[p - lo], pivot)
        self.assertTrue(all(x <= pivot for x in state[:p - lo]))
        self.assertTrue(all(x > pivot for x in state[p - lo + 1:]))
        self.assertEqual((node["left"]["lo"], node["left"]["hi"]), (lo, p - 1))
        self.assertEqual((node["right"]["lo"], node["right"]["hi"]), (p + 1, hi))
        self.check_tree(node["left"])
        self.check_tree(node["right"])

    def test_demo_snapshots(self):
        trace = render.quicksort_trace([6, 3, 8, 1, 7, 2, 5])
        tree = trace["tree"]
        swaps = [step["array"] for step in tree["comparisons"] if step["swap"] and step["swap"][0] != step["swap"][1]]
        self.assertEqual(swaps, [[3, 6, 8, 1, 7, 2, 5], [3, 1, 8, 6, 7, 2, 5], [3, 1, 2, 6, 7, 8, 5]])
        self.assertEqual(tree["after_partition"], [3, 1, 2, 5, 7, 8, 6])
        self.assertEqual(tree["p"], 3)
        self.assertEqual(trace["output"], [1, 2, 3, 5, 6, 7, 8])
        self.check_tree(tree)

    def test_exhaustive_short_inputs(self):
        for length in range(8):
            for values in itertools.permutations(range(length)):
                trace = render.quicksort_trace(values)
                self.assertEqual(trace["output"], sorted(values))
                self.check_tree(trace["tree"])
        for length in range(7):
            for values in itertools.product((-1, 0, 1), repeat=length):
                trace = render.quicksort_trace(values)
                self.assertEqual(trace["output"], sorted(values))
                self.check_tree(trace["tree"])

    def test_input_not_mutated(self):
        values = [3, 1, 2]
        render.quicksort_trace(values)
        self.assertEqual(values, [3, 1, 2])

    def test_template_limits(self):
        for values in ([], [1], list(range(8)), [1000, 2], [1.5, 2]):
            with self.assertRaises(ValueError):
                render.quicksort_figure(values)

    def test_supported_template_cases(self):
        for values in ([1, 2], [2, 1], [1] * 7, list(range(7)), list(range(6, -1, -1)), [-1, -2, 0, -1, 2]):
            figure, trace = render.quicksort_figure(values)
            ET.fromstring(figure.svg())
            self.assertEqual(trace["output"], sorted(values))


class DrawingTests(unittest.TestCase):
    def test_svg_is_white_and_accessible(self):
        figure, _ = render.quicksort_figure([6, 3, 8, 1, 7, 2, 5])
        root = ET.fromstring(figure.svg())
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.attrib["viewBox"], "0 0 1600 1536")
        background = root.find("s:rect", ns)
        self.assertEqual(background.attrib["fill"], "#FFFFFF")
        self.assertEqual(background.attrib["height"], "1536")
        self.assertIsNotNone(root.find("s:title", ns))
        self.assertIsNotNone(root.find("s:desc", ns))

    def test_text_is_escaped(self):
        figure = render.Figure(100, 100, "A&B")
        figure.text(0, 20, '<script>alert("x")</script> &')
        root = ET.fromstring(figure.svg())
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.find("s:text", ns).text, '<script>alert("x")</script> &')
        self.assertIsNone(root.find("s:script", ns))

    def test_tokens_only(self):
        with self.assertRaises(ValueError):
            render.Figure(100, 100, "demo").rect(1, 1, 20, 20, fill="#ff00ff")

    def test_template_spec(self):
        path = render.SKILL_DIR / "templates/node-flow.json"
        figure = render.from_spec(json.loads(path.read_text()))
        ET.fromstring(figure.svg())
        with self.assertRaises(ValueError):
            render.from_spec({"width": 100, "height": 100, "elements": [{"type": "script"}]})

    def test_rounded_connectors(self):
        self.assertIn("Q", render.rounded_path([(0, 0), (0, 40), (40, 40)]))
        with self.assertRaises(ValueError):
            render.rounded_path([(0, 0)])

    def test_export_refuses_overwrite(self):
        figure = render.Figure(100, 100, "demo")
        with tempfile.TemporaryDirectory() as temp:
            outputs = render.export(figure, temp, "test", svg_only=True)
            self.assertTrue(outputs[0].exists())
            with self.assertRaises(FileExistsError):
                render.export(figure, temp, "test", svg_only=True)
            with self.assertRaises(ValueError):
                render.export(figure, temp, "../escape", svg_only=True)
            with self.assertRaises(ValueError):
                render.export(figure, temp, "too-large", scale=10, svg_only=True)

    def test_custom_theme_does_not_change_defaults(self):
        custom = render.Figure(100, 100, 'custom', theme={'colors':{'ink':'#1F2937','blue':'#2563EB'}})
        standard = render.Figure(100, 100, 'standard')
        self.assertEqual(custom.color('ink'), '#1F2937')
        self.assertEqual(standard.color('ink'), '#000000')
        self.assertEqual(custom.color('yellow'), render.THEME['colors']['yellow'])

    def test_spec_embedded_theme(self):
        figure = render.from_spec({'width':100,'height':100,'theme':{'colors':{'paper':'#F8FAFC'}},'elements':[]})
        root = ET.fromstring(figure.svg())
        self.assertEqual(root.find('{http://www.w3.org/2000/svg}rect').get('fill'), '#F8FAFC')

    def test_invalid_theme_rejected(self):
        for theme in ({'colors':{'ink':'not-a-color'}},{'colors':{'bad-token':'#000000'}},{'unknown':{}},{'geometry':{'corner':float('nan')}}):
            with self.assertRaises(ValueError): render.load_theme(theme)

    def test_unicode_output_name(self):
        with tempfile.TemporaryDirectory() as temp:
            output = render.export(render.Figure(100,100,'demo'),temp,'任务流程',svg_only=True)
            self.assertTrue(output[0].is_file())

    def test_canvas_must_be_finite(self):
        for dimension in (float('nan'), float('inf'), -1):
            with self.assertRaises(ValueError): render.Figure(dimension,100,'bad')

    def test_teaching_furniture_is_optional(self):
        main, _ = render.quicksort_figure([3,1,2])
        teaching, _ = render.quicksort_figure([3,1,2],teaching_page=True)
        self.assertNotIn('DOCUMENT FIGURE',main.svg())
        self.assertIn('DOCUMENT FIGURE',teaching.svg())

    def test_custom_theme_on_quicksort(self):
        figure, trace = render.quicksort_figure([3,1,2],theme={'colors':{'ink':'#1F2937'}})
        self.assertIn('#1F2937',figure.svg())
        self.assertEqual(trace['output'],[1,2,3])

    @unittest.skipUnless(shutil.which("rsvg-convert"), "PNG export requires rsvg-convert")
    def test_png_export(self):
        figure = render.Figure(120, 80, "demo")
        figure.text(20, 40, "PNG")
        with tempfile.TemporaryDirectory() as temp:
            render.export(figure, temp, "test", scale=2)
            data = (Path(temp) / "test.png").read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", data[16:24]), (240, 160))


if __name__ == "__main__":
    unittest.main(verbosity=2)
