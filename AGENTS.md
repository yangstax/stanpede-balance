# STANPEDE balance

This repository controls the live balance of STANPEDE, a K-pop survivors game. The game code and artwork live separately in `yangstax/ksurvivor`.

## Make a change

1. Pull latest main, then read `v3/balance.json` and `v3/balance.schema.json`. Fetch the live v3 snapshot with a fresh query parameter before editing. Versions 1 and 2 are archived for older builds: preserve its values unless the user explicitly requests an older-client change.
2. Change only the requested values. Preserve the existing unrelated balance. Keep names short, clear and affectionate; use Charm power, faint, health, and Chart Topper. Never introduce violent wording.
3. Keep upgrade keys and fan kind IDs stable. Change `abilityText[].name` to rename an upgrade; update its descriptions when needed. Fan kind IDs: 0 ordinary, 1 filmer, 2 banner, 3 dad, 4 grandma, 5 rival fans, 6 rival idol, 7 headphones, 8 plush tosser.
4. Install `requirements.txt`, then run `python3 -m unittest test_validation.py` and `python3 validate.py`.
5. Commit and push to **main** as `yangstax` when the user requests a completed change. These instructions authorize routine config publication for a requested balance change; no game build or local Mac is needed.
6. Watch the GitHub Actions result, then fetch the live URL with a fresh query parameter and verify the changed values. Report the actual published revision and exact changes. A successful push alone does not prove publication.

Current live URL: https://yangstax.github.io/stanpede-balance/v3/balance.json

Version 3 contains 300 settings, nine fan kinds, nineteen ability texts and seventeen persistent ability unlock rows. Use schemaVersion 3. Names and five-rank descriptions are configurable; IDs and array sizes are the app contract. The stable `FancamFlash` key now means Selfie Drone. `BubblePop` and `PhotoStandee` are new keys. `LaserLight` and `BoomBox` remain retired.

The workflow validates the entire snapshot, publishes only JSON/schema files, and uses the source commit as the served revision. Existing matches keep their snapshot. The game downloads changes on launch/resume and about once a minute, applying them between matches. It keeps the last valid config for offline play.

## Ability unlocks and featured rewards

- `abilityUnlocks`: one row for each of the seventeen persistent abilities, identified by its stable `key`; `tour` is 1–6. Tour 1 means immediately available. Tour 2 means clearing Tour 1. This uses career unlock progress, so earned abilities remain available when replaying earlier tours. Instant cash/healing are always available and have no unlock rows.
- `tourAbilityRewards`: five stable keys, respectively featured after clearing Tours 1–5. The matching ability must newly unlock at tour 2/3/4/5/6. Update both tables atomically when swapping unlocks. Reward icons, Home tour descriptions and first choices use this mapping.
- Selfie Drone (`FancamFlash`) is available immediately in Tour 1. Photo Standee stays at tour 3 and Bubble Pop at tour 4. The Tour 1 clear features Photocard Ricochet, which newly unlocks at tour 2. When changing gates, keep each featured clear reward consistent with the following tour's new unlocks. Do not change stable IDs, art or power unless requested.
- Validators require complete unique supported keys, valid tours and rewards, at least four starting attacks (starter plus three choices), and each idol's starter available by that idol's unlock tour. Featured base moves get first-menu priority; passive rewards keep normal offer rules and evolutions still require their gameplay recipe. New Era follows the sixth clear rather than an ability reward.
- These existing-ability progression edits now publish from this repository with no app rebuild. The game update that first adds v3 support is required once. It preserves career v4 progress; invalid snapshots retain the last valid config.

## Useful settings

- `tourFanLevels`, `tourSingleLevels`, `tourRivalLevels`, `tourCycleLevels`: fan → single → rival phases. Current phases are 14/16/20, 22/26/30, then every ten levels.
- `spawnRateStart/End`, `spawnCurve`, `regularGroupSize`, `openingMaxHostiles`, `openingCrowdGraceSeconds`, `lateSwarmTimes/Fans`: arrival pacing. The opening limit applies to regular arrivals during its grace window; scripted swarms still use the shared global cap. Keep crowds readable and slow enough to steer through.
- `fans`: health/charm, speed, contact health loss, XP/cash rewards and collision radius per fan type.
- `fanScalingSecondsPerLevel`, `fanScalingOverflowFraction`: the level-based soft ceiling and continued time scaling beyond it. Avoid freezing pressure when XP collection stops.
- `crowdAreaQuietRate`: how much arrival pressure remains on cleared ground. Preserve time to collect loot, while preventing stationary safety.
- `firstLevelFollowers`, `openingLevelFollowers`, `levelGrowth`: XP requirements. Filling a bar must still earn its choice; rival battles hold choices until won.
- Ability arrays have five ranks. `fingerHeartPower`, `sparklePower`, `lightstickDamage`, `soundWaveDamage`, `photocardDamage`, `confettiDamage`, `fancamDamage` are internal values; cards show power ×10. Cooldowns are seconds.
- Sparkle Burst uses the stable `Wink` key. `sparkleSpreadDegrees` is the total fan width; `sparkleAimDegrees` is the forward cone for assistance. Its reach follows `sparkleSpeed × sparkleLifetime`; power is per comet, so consider the shot count when tuning it.
- `powerPerRank`, `protectionPerRank`, `cooldownReductionPerRank`, `areaPerRank`: match passive effects, written as fractions (0.15 means 15%).
- `training*`, signature settings and `careerGoalRewards`: permanent progression. Costs are twenty entries per track.
- `tourCashMultipliers`: six repeatable Training-cash rates, currently 1 / 1.25 / 1.5 / 1.75 / 2 / 2.25. Applies to bills and follower support, including Exit to Home; match XP, career goals and first-clear bonuses stay separate. Each run locks its rate and preserves fractional earnings.
- `tourHealthPerStop`, `tourArrivalsPerStop`, `rivalHealthPerStop`: linear increases per tour after Tour 1. Current increments are 20% fan endurance, 12% regular arrival pressure and 30% rival endurance. Do not infer an hours-to-progress target from these values.
- `maxHostiles`: strict shared active cap across ordinary arrivals, swarms, reveals and rival summons. Preserve 180 unless a requested change and testing justify otherwise. Required encounters make room; rejected arrivals do not queue.
- `selfiePhotos`, `selfiePhotoInterval`, `fancam*`: group-photo drone. `fancamDamage` is total burst power, divided across its photos; The frame half-width is 1.2 × `fancamRadius`; half-height is 0.9 × it. Existing follow-camera appearance values are legacy compatibility fields.
- `bubble*`: power, cooldown, radius, capture limit, lifetime, speed and range for one active hold-and-pop bubble. Rivals resist the hold.
- `standee*`: photo power/tick, cooldown, duration, attraction radius and fan limit for one cardboard photo prop. Rivals ignore the distraction.
- Hype, recovery, gifts, pickup ranges, camera/readability and audio mix are also in this snapshot.

Changes to mechanics, new IDs, art, audio recordings, pool sizes or code require a game update. Keep schema version 3 stable for supported value/text/unlock changes; incompatible changes require a new versioned endpoint. Run validation for all three versions before publication. Never add secrets, authentication tokens or personal data to this public repository.
