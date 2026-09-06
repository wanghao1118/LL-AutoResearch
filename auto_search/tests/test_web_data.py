import json
import tempfile
import unittest
from pathlib import Path

from web.build_data import (
    DEFAULT_MANIFEST,
    DEFAULT_RUN_DIR,
    build_dataset,
    parse_dataset_benchmark,
    parse_idea,
    write_dataset,
)


class WebDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = build_dataset(DEFAULT_RUN_DIR, DEFAULT_MANIFEST)

    @unittest.skipUnless(DEFAULT_RUN_DIR.is_dir(), "default research folder was deleted")
    def test_builds_all_medical_vlm_ideas(self):
        self.assertEqual(self.dataset["summary"]["total"], 10)
        self.assertEqual(len(self.dataset["ideas"]), 10)
        self.assertEqual(self.dataset["summary"]["verdicts"], {"strong": 3, "promising": 5, "weak": 2})

    @unittest.skipUnless(DEFAULT_RUN_DIR.is_dir(), "default research folder was deleted")
    def test_every_idea_has_expected_sections(self):
        for idea in self.dataset["ideas"]:
            with self.subTest(idea=idea["id"]):
                self.assertTrue(idea["weakness"])
                self.assertEqual(len(idea["causes"]), 3)
                self.assertEqual(len(idea["contributions"]), 3)
                self.assertEqual(len(idea["method_sections"]), 5)
                self.assertIn("Contribution (1) 的实现", [section["title"] for section in idea["method_sections"]])
                self.assertIn("完整实现流程", [section["title"] for section in idea["method_sections"]])
                self.assertNotIn("资源预算", [section["title"] for section in idea["method_sections"]])

    @unittest.skipUnless(DEFAULT_RUN_DIR.is_dir(), "default research folder was deleted")
    def test_review_is_joined_by_paper_id(self):
        first = self.dataset["ideas"][0]
        self.assertEqual(first["id"], "cytomorphology_grounding_2026")
        self.assertEqual(first["review"]["verdict"], "strong")
        self.assertEqual(first["review"]["scores"]["problem_grounding"], 5)

    @unittest.skipUnless(DEFAULT_RUN_DIR.is_dir(), "default research folder was deleted")
    def test_dataset_can_be_serialized(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "ideas.json"
            write_dataset(self.dataset, output)
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["summary"]["total"], 10)

    def test_pass_document_is_available_to_the_browser(self):
        markdown = """# PASS: 缺少公开定位标注

## Weakness

现有公开数据不足以验证核心机制。

## Benchmark 审计

**已检查：** PublicBench

**直接支持：** 不支持。

## PASS 判定

**阻塞项：** 缺少发布标签。

**结论：** PASS
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "idea.md"
            path.write_text(markdown, encoding="utf-8")
            parsed = parse_idea(path)
        self.assertTrue(parsed["is_pass"])
        self.assertEqual(parsed["contributions"], [])
        self.assertEqual([section["title"] for section in parsed["method_sections"]], ["Benchmark 审计", "PASS 判定"])

    def test_structured_dataset_and_benchmark_cards_are_parsed(self):
        body = """**数据集**

#### 数据集 (1)：[训练集](https://example.org/train)
**使用阶段：** 训练。
**发布内容：** 图像与掩膜。
**使用方法：** 使用发布掩膜监督。

**Benchmark**

#### Benchmark (1)：[基准一](https://example.org/b1)
**任务类型：** 分割。
**使用方式：** 直接使用原协议。
**评测方法：** Dice。
**对应贡献：** Contribution (1)。

#### Benchmark (2)：[基准二](https://example.org/b2)
**任务类型：** 检测。
**使用方式：** 直接使用原协议。
**评测方法：** AP。
**对应贡献：** Contribution (2)。

#### Benchmark (3)：[基准三](https://example.org/b3)
**任务类型：** 鲁棒分类。
**使用方式：** 改造后使用固定缩放。
**评测方法：** Balanced accuracy。
**对应贡献：** Contribution (3)。

**下游任务：**
1. 分割。
2. 检测。

**标注来源：** 只使用发布标注。

**缺口与处理：** 不外推到其他模态。
"""
        parsed = parse_dataset_benchmark(body)
        self.assertTrue(parsed["structured"])
        self.assertEqual(parsed["datasets"][0]["name"], "训练集")
        self.assertEqual(parsed["datasets"][0]["url"], "https://example.org/train")
        self.assertEqual(len(parsed["benchmarks"]), 3)
        self.assertEqual(parsed["benchmarks"][2]["fields"][0]["label"], "任务类型")
        self.assertIn("分割", parsed["downstream_tasks"])


if __name__ == "__main__":
    unittest.main()
