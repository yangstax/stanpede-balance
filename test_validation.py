import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import ValidationError

from validate import ROOT, load_document, unique_properties, validate


class BalanceValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "v3/balance.json").read_text())
        self.schema = json.loads((ROOT / "v3/balance.schema.json").read_text())

    def test_current_snapshot_is_valid(self):
        validate(self.data, self.schema)

    def test_unknown_settings_are_rejected(self):
        self.data["spawnRateTypo"] = 3
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_empty_move_arrays_are_rejected(self):
        self.data["fingerHeartPower"] = []
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_duplicate_fan_ids_are_rejected(self):
        self.data["fans"][1] = copy.deepcopy(self.data["fans"][0])
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_duplicate_ability_keys_are_rejected(self):
        self.data["abilityText"][1]["key"] = self.data["abilityText"][0]["key"]
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_wrong_milestone_order_is_rejected(self):
        self.data["tourSingleLevels"][0] = self.data["tourRivalLevels"][0] + 1
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_unfinished_waves_are_rejected(self):
        self.data["soundWaveSeconds"] = 5
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_rich_text_names_are_rejected(self):
        self.data["abilityText"][0]["name"] = "<b>Heart</b>"
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_blank_names_are_rejected(self):
        self.data["abilityText"][0]["name"] = "   "
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_duplicate_json_properties_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"revision":"a","revision":"b"}', object_pairs_hook=unique_properties)

    def test_older_client_contract_remains_valid(self):
        for version in (1, 2):
            data = json.loads((ROOT / f"v{version}/balance.json").read_text())
            schema = json.loads((ROOT / f"v{version}/balance.schema.json").read_text())
            validate(data, schema)

    def test_six_tour_payouts_are_required(self):
        self.data["tourCashMultipliers"] = [1, 1.25]
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_decreasing_tour_payouts_are_rejected(self):
        self.data["tourCashMultipliers"][3] = 1.1
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_bubble_cannot_outlive_its_cooldown(self):
        self.data["bubbleLifetime"] = 5
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_new_abilities_require_complete_rank_text(self):
        self.data["abilityText"][-1]["descriptions"] = ["Only one"]
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_publication_stages_all_client_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(ROOT / "validate.py"), "--publish-dir", directory,
                            "--revision", "published.test"], check=True, capture_output=True)
            for version in (1, 2, 3):
                data = json.loads((Path(directory) / f"v{version}/balance.json").read_text())
                self.assertEqual(data["schemaVersion"], version)
                self.assertEqual(data["revision"], "published.test")
                original = json.loads((ROOT / f"v{version}/balance.json").read_text())
                original["revision"] = "published.test"
                self.assertEqual(data, original)
            self.assertEqual(len(list(Path(directory).rglob("*.json"))), 6)

    def test_unlocks_can_be_reordered_without_changing_ids(self):
        self.data["abilityUnlocks"].reverse()
        for entry in self.data["abilityUnlocks"]:
            if entry["key"] == "FancamFlash":
                entry["tour"] = 4
            elif entry["key"] == "BubblePop":
                entry["tour"] = 2
        self.data["tourAbilityRewards"][0] = "BubblePop"
        self.data["tourAbilityRewards"][2] = "FancamFlash"
        validate(self.data, self.schema)

    def test_missing_unlock_rows_are_rejected(self):
        self.data["abilityUnlocks"].pop()
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_duplicate_unlock_keys_are_rejected(self):
        self.data["abilityUnlocks"][1] = copy.deepcopy(self.data["abilityUnlocks"][0])
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_retired_unlock_keys_are_rejected(self):
        self.data["abilityUnlocks"][0]["key"] = "BoomBox"
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_invalid_unlock_tours_are_rejected(self):
        self.data["abilityUnlocks"][0]["tour"] = 7
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_incomplete_featured_rewards_are_rejected(self):
        self.data["tourAbilityRewards"].pop()
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_featured_reward_cannot_remain_locked(self):
        self.data["tourAbilityRewards"][0] = "BubblePop"
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_featured_reward_must_be_new(self):
        self.data["tourAbilityRewards"][2] = "PhotocardRicochet"
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_starter_cannot_unlock_after_its_idol(self):
        for entry in self.data["abilityUnlocks"]:
            if entry["key"] == "PhotocardRicochet":
                entry["tour"] = 3
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_opening_requires_three_new_attack_choices(self):
        for entry in self.data["abilityUnlocks"]:
            if entry["key"] == "Wink":
                entry["tour"] = 2
        self.data["tourAbilityRewards"][0] = "Wink"
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_nonfinite_cash_rates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "balance.json"
            path.write_text('{"tourCashMultipliers":[NaN]}')
            with self.assertRaises(ValueError):
                load_document(path)


if __name__ == "__main__":
    unittest.main()
