import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training" / "dataset"))

from merge_taco_kaggle import remap_taco_category  # noqa: E402


class TacoMappingTests(unittest.TestCase):
    def test_material_variants_follow_project_policy(self) -> None:
        self.assertEqual(remap_taco_category("plastic bottle cap"), "PLASTIC")
        self.assertEqual(remap_taco_category("other_plastic_wrapper"), "PLASTIC")
        self.assertEqual(remap_taco_category("metal_bottle_cap"), "METAL")
        self.assertEqual(remap_taco_category("drink_can"), "METAL")
        self.assertEqual(remap_taco_category("normal_paper"), "BIODEGRADABLE")
        self.assertEqual(remap_taco_category("corrugated_carton"), "BIODEGRADABLE")
        self.assertEqual(remap_taco_category("glass_bottle"), "OTHER")
        self.assertEqual(remap_taco_category("unlabeled_litter"), "OTHER")
