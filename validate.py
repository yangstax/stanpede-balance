"""Validate a balance snapshot and optionally stage the GitHub Pages artifact."""

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 131072
STARTER_TOURS = {"FingerHeart": 1, "PhotocardRicochet": 2, "Wink": 3, "Lightstick": 4,
                 "HighNote": 5, "FancamFlash": 6}
BASE_MOVES = {"FingerHeart", "Wink", "Lightstick", "HighNote", "PhotocardRicochet", "ConfettiTrail",
              "FancamFlash", "BubblePop", "PhotoStandee"}


def unique_properties(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"Duplicate property: {name}")
        result[name] = value
    return result


def load_document(path):
    body = path.read_bytes()
    if len(body) > MAX_BYTES:
        raise ValueError("Config exceeds the app's size limit.")
    return json.loads(body, object_pairs_hook=unique_properties, parse_constant=reject_nonfinite)


def reject_nonfinite(value):
    raise ValueError(f"Nonfinite JSON number: {value}")


def validate(data, schema):
    Draft202012Validator(schema).validate(data)
    if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", data["revision"]) is None:
        raise ValidationError("Invalid revision.")
    phases = zip(data["tourFanLevels"], data["tourSingleLevels"], data["tourRivalLevels"], strict=True)
    previous_rival = 0
    for fan, single, rival in phases:
        if not previous_rival < fan < single < rival:
            raise ValidationError("Milestones must follow fan, single, rival order.")
        previous_rival = rival
    if data["tourFanLevels"][-1] + data["tourCycleLevels"] <= previous_rival:
        raise ValidationError("The next fan phase must follow the previous rival.")
    if data["dropMinFans"] > data["dropMaxFans"] or data["hypeDropFansMin"] > data["hypeDropFansMax"]:
        raise ValidationError("A minimum exceeds its maximum.")
    if data["schemaVersion"] >= 7:
        previous_level = 0
        if data["levelPresets"][0]["fromLevel"] != 1:
            raise ValidationError("Wave presets must begin at level 1.")
        for row in data["levelPresets"]:
            if row["fromLevel"] <= previous_level:
                raise ValidationError("Wave preset levels must be strictly increasing.")
            if row["breatherSpawnRate"] > row["waveSpawnRate"]:
                raise ValidationError("A breather cannot have a higher arrival rate than its wave.")
            previous_level = row["fromLevel"]
    else:
        if data["openingMaxHostiles"] > data["maxHostiles"]:
            raise ValidationError("Opening crowd exceeds the crowd cap.")
        if data["openingWaveTime"] < data["swarmWarningSeconds"] or data["gateRushTime"] <= data["openingWaveTime"]:
            raise ValidationError("Opening swarm times are out of order.")
        if len(data["lateSwarmTimes"]) != len(data["lateSwarmFans"]):
            raise ValidationError("Each late swarm needs a time and count.")
        previous_time = data["gateRushTime"]
        for wave_time in data["lateSwarmTimes"]:
            if wave_time <= previous_time:
                raise ValidationError("Late swarm times must increase after the gate rush.")
            previous_time = wave_time
    if any(cooldown < data["soundWaveSeconds"] for cooldown in data["soundWaveCooldown"]):
        raise ValidationError("A sound wave must finish before the next cast.")
    if any(not ability["name"].strip() for ability in data["abilityText"]):
        raise ValidationError("Ability names cannot be blank.")
    if data["schemaVersion"] >= 2:
        rates = data["tourCashMultipliers"]
        if rates[0] != 1 or any(right < left for left, right in zip(rates, rates[1:])):
            raise ValidationError("Tour cash rates must start at one and never decrease.")
        if any(cooldown < data["bubbleLifetime"] for cooldown in data["bubbleCooldown"]):
            raise ValidationError("A bubble must pop before the next cast.")
    if data["schemaVersion"] >= 3:
        unlocks = {entry["key"]: entry["tour"] for entry in data["abilityUnlocks"]}
        if any(unlocks[key] > tour for key, tour in STARTER_TOURS.items()):
            raise ValidationError("An idol's starting move must be available when that idol unlocks.")
        if sum(unlocks[key] == 1 for key in BASE_MOVES) < 4:
            raise ValidationError("Tour 1 needs its starter plus three new attack choices.")
        for tour, key in enumerate(data["tourAbilityRewards"], start=2):
            if unlocks[key] != tour:
                raise ValidationError("Each featured reward must newly unlock on the following tour.")
    if data["schemaVersion"] >= 4:
        for row in data["fanArrivals"]:
            if row["commonWeight"] < row["initialWeight"]:
                raise ValidationError("A learned fan class cannot become rarer as its ramp completes.")
            if not row["introductionCount"] <= row["initialMaxActive"] <= row["commonMaxActive"]:
                raise ValidationError("Reveal size and active limits must grow in order.")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    paths = [args.file] if args.file else sorted(ROOT.glob("v*/balance.json"))
    for path in paths:
        data = load_document(path)
        version = f"v{data['schemaVersion']}"
        schema_path = ROOT / version / "balance.schema.json"
        schema = json.loads(schema_path.read_text())
        validate(data, schema)
        if args.revision:
            data["revision"] = args.revision
            validate(data, schema)
        if args.publish_dir:
            destination = args.publish_dir / version
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "balance.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            (destination / "balance.schema.json").write_text(schema_path.read_text())
        print(f"Balance {version} valid: {data['revision']} ({len(data)} settings)")
    if args.publish_dir:
        (args.publish_dir / ".nojekyll").touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
