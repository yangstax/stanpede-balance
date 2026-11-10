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
        self.data = json.loads((ROOT / "v9/balance.json").read_text())
        self.schema = json.loads((ROOT / "v9/balance.schema.json").read_text())

    def test_filmer_volleys_have_bounded_readable_settings(self):
        for key, value in (("filmerShotCount", 6), ("filmerShotSpeed", 0),
                           ("filmerWarningSeconds", 0.1), ("filmerCooldown", -1),
                           ("filmerRange", 20), ("filmerSpreadDegrees", 90)):
            with self.subTest(setting=key):
                candidate = copy.deepcopy(self.data)
                candidate[key] = value
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)

    def test_lightstick_timing_accepts_fractional_seconds_and_zero_rest(self):
        self.data["abilityTiming"]["Lightstick"] = {"activeSeconds": 3.25, "restSeconds": 0}
        validate(self.data, self.schema)

    def test_lightstick_timing_is_required(self):
        for value in (None, {}, {"Lightstick": {"activeSeconds": 5}}, {"Lightstick": {"restSeconds": 2}}):
            with self.subTest(value=value):
                candidate = copy.deepcopy(self.data)
                if value is None:
                    candidate.pop("abilityTiming")
                else:
                    candidate["abilityTiming"] = value
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)

    def test_timing_rejects_unknown_or_unimplemented_ids(self):
        for key in ("LightstickOrbit", "FingerHeart", "Unknown"):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.data)
                candidate["abilityTiming"][key] = {"activeSeconds": 5, "restSeconds": 2}
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)

    def test_timing_rejects_invalid_seconds_and_misspelled_fields(self):
        for field, value in (("activeSeconds", 0), ("activeSeconds", 121), ("restSeconds", -1), ("restSeconds", 121), ("cooldown", 2)):
            with self.subTest(field=field, value=value):
                candidate = copy.deepcopy(self.data)
                candidate["abilityTiming"]["Lightstick"][field] = value
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)

    def test_wave_rows_need_a_starting_level_and_sorted_unique_thresholds(self):
        for levels in ([2, 10, 20], [1, 1, 20], [1, 20, 10]):
            with self.subTest(levels=levels):
                data = copy.deepcopy(self.data)
                data["levelPresets"] = data["levelPresets"][:len(levels)]
                for row, level in zip(data["levelPresets"], levels, strict=True):
                    row["fromLevel"] = level
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

    def test_wave_rows_must_be_complete_and_bounded(self):
        for field, value in (("waveDurationSeconds", 0), ("breatherDurationSeconds", -1),
                             ("waveSpawnRate", -1), ("breatherSpawnRate", 61)):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["levelPresets"][0][field] = value
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)
        self.data["levelPresets"][0].pop("waveDurationSeconds")
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_breather_cannot_spawn_faster_than_wave(self):
        self.data["levelPresets"][0]["breatherSpawnRate"] = 60
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_zero_rate_breather_is_valid(self):
        self.data["levelPresets"][0]["breatherSpawnRate"] = 0
        validate(self.data, self.schema)

    def test_missing_or_excessive_presets_are_rejected(self):
        for rows in ([], self.data["levelPresets"] * 3):
            with self.subTest(count=len(rows)):
                data = copy.deepcopy(self.data)
                data["levelPresets"] = rows
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

    def test_disengagement_needs_offscreen_distance_and_positive_timeout(self):
        for field, value in (("giveUpDistanceScreens", 0.1), ("giveUpAfterSecondsOffscreen", 0)):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = value
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

    def test_retired_pacing_knobs_cannot_silently_stack(self):
        for field in ("spawnRateStart", "openingWaveTime", "crowdAreaQuietRate", "charmGrowthLinear"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = 1
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

    def test_regeneration_has_five_ranks(self):
        self.data["healthRegenFraction"] = [0.01]
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_regeneration_rejects_instant_or_negative_healing(self):
        for field, value in (("healthRegenSeconds", 0), ("healthRegenFraction", [-0.01] * 5), ("giftHealFraction", -0.1)):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = value
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

    def test_regeneration_needs_text_and_unlock(self):
        for field in ("abilityText", "abilityUnlocks"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = [row for row in data[field] if row["key"] != "HealthRegen"]
                with self.assertRaises(ValidationError):
                    validate(data, self.schema)

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
        for version in (1, 2, 3, 4, 5, 6, 7):
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
            for version in range(1, 10):
                data = json.loads((Path(directory) / f"v{version}/balance.json").read_text())
                self.assertEqual(data["schemaVersion"], version)
                self.assertEqual(data["revision"], "published.test")
                original = json.loads((ROOT / f"v{version}/balance.json").read_text())
                original["revision"] = "published.test"
                self.assertEqual(data, original)
            self.assertEqual(len(list(Path(directory).rglob("*.json"))), 18)

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
            if entry["key"] in ("Wink", "HighNote"):
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

    def test_fan_progression_can_be_retuned_and_reordered(self):
        self.data["fanArrivals"].reverse()
        banner = next(row for row in self.data["fanArrivals"] if row["kind"] == 2)
        banner.update(introductionCount=2, initialMaxActive=3, commonMaxActive=12,
                      initialWeight=0.08, commonWeight=0.5, levelsToCommon=8, arrivalCost=4)
        validate(self.data, self.schema)

    def test_missing_fan_progression_is_rejected(self):
        self.data.pop("fanArrivals")
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_duplicate_arrival_classes_are_rejected(self):
        self.data["fanArrivals"][1] = copy.deepcopy(self.data["fanArrivals"][0])
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_rivals_cannot_enter_regular_arrival_profiles(self):
        self.data["fanArrivals"][0]["kind"] = 6
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_a_reveal_cannot_exceed_its_initial_active_limit(self):
        self.data["fanArrivals"][0].update(initialMaxActive=2, introductionCount=3)
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_common_caps_cannot_shrink(self):
        self.data["fanArrivals"][0]["commonMaxActive"] = 1
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_common_odds_cannot_be_less_than_introductory_odds(self):
        self.data["fanArrivals"][0]["commonWeight"] = 0.01
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_zero_cost_and_instant_ramps_are_rejected(self):
        for field in ("arrivalCost", "levelsToCommon"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.data)
                candidate["fanArrivals"][0][field] = 0
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)

    def test_star_requires_five_burst_radii(self):
        self.data["starBurstRadius"] = [1.05]
        with self.assertRaises(ValidationError):
            validate(self.data, self.schema)

    def test_star_cannot_have_zero_range_or_turn_rate(self):
        for field in ("starTargetRange", "starTurnDegrees"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.data)
                candidate[field] = 0
                with self.assertRaises(ValidationError):
                    validate(candidate, self.schema)


if __name__ == "__main__":
    unittest.main()
