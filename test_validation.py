import copy
import json
import unittest

from jsonschema import ValidationError

from validate import ROOT, unique_properties, validate


class BalanceValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "v1/balance.json").read_text())
        self.schema = json.loads((ROOT / "v1/balance.schema.json").read_text())

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


if __name__ == "__main__":
    unittest.main()
