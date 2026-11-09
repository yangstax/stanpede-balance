# STANPEDE balance

This repository controls the live balance of STANPEDE, a K-pop survivors game. The game code and artwork live separately in `yangstax/ksurvivor`.

## Make a change

1. Pull latest main, then read `v6/balance.json` and `v6/balance.schema.json`. Fetch the live v5 snapshot with a fresh query parameter before editing. Versions 1–5 are archived for older builds: preserve their values unless the user explicitly requests an older-client change.
2. Change only the requested values. Preserve the existing unrelated balance. Keep names short, clear and affectionate; use Charm power, faint, health, and Chart Topper. Never introduce violent wording.
3. Keep upgrade keys and fan kind IDs stable. Change `abilityText[].name` to rename an upgrade; update its descriptions when needed. Fan kind IDs: 0 ordinary, 1 filmer, 2 banner, 3 dad, 4 grandma, 5 rival fans, 6 rival idol, 7 headphones, 8 plush tosser.
4. Install `requirements.txt`, then run `python3 -m unittest test_validation.py` and `python3 validate.py`.
5. Commit and push to **main** as `yangstax` when the user requests a completed change. These instructions authorize routine config publication for a requested balance change; no game build or local Mac is needed.
6. Watch the GitHub Actions result, then fetch the live URL with a fresh query parameter and verify the changed values. Report the actual published revision and exact changes. A successful push alone does not prove publication.

Current live URL: https://yangstax.github.io/stanpede-balance/v6/balance.json

Version 6 contains 312 settings, nine fan kinds, twenty ability texts and eighteen persistent ability unlock rows. Use schemaVersion 6. Names and five-rank descriptions are configurable; IDs and array sizes are the app contract. The stable `FancamFlash` key now means Selfie Drone. `BubblePop` and `PhotoStandee` are new keys. `LaserLight` and `BoomBox` remain retired.

The workflow validates the entire snapshot, publishes only JSON/schema files, and uses the source commit as the served revision. Existing matches keep their snapshot. The game downloads changes on launch/resume and about once a minute, applying them between matches. It keeps the last valid config for offline play.

## Ability unlocks and featured rewards

- `abilityUnlocks`: one row for each of the seventeen persistent abilities, identified by its stable `key`; `tour` is 1–6. Tour 1 means immediately available. Tour 2 means clearing Tour 1. This uses career unlock progress, so earned abilities remain available when replaying earlier tours. Instant cash/healing are always available and have no unlock rows.
- `tourAbilityRewards`: five stable keys, respectively featured after clearing Tours 1–5. The matching ability must newly unlock at tour 2/3/4/5/6. Update both tables atomically when swapping unlocks. Reward icons, Home tour descriptions and first choices use this mapping.
- Selfie Drone (`FancamFlash`) is available immediately in Tour 1. Photo Standee stays at tour 3 and Bubble Pop at tour 4. The Tour 1 clear features Photocard Ricochet, which newly unlocks at tour 2. When changing gates, keep each featured clear reward consistent with the following tour's new unlocks. Do not change stable IDs, art or power unless requested.
- Validators require complete unique supported keys, valid tours and rewards, at least four starting attacks (starter plus three choices), and each idol's starter available by that idol's unlock tour. Featured base moves get first-menu priority; passive rewards keep normal offer rules and evolutions still require their gameplay recipe. New Era follows the sixth clear rather than an ability reward.
- These existing-ability progression edits now publish from this repository with no app rebuild. The game update that first adds v6 support is required once. It preserves career v4 progress; invalid snapshots retain the last valid config.

## Fan progression

`fanArrivals` has exactly one row for each of classes 1/2/3/4/7/8. Row order is free. Ordinary fans use
`basicFanWeight`; rival fans/bosses retain their required encounter rules. Every regular or scripted arrival
uses the same class weights, active limits and budget costs. Required fan introductions use the reveal count.

| Field | Meaning |
|---|---|
| `introductionCount` | Fans in the held first reveal; 1–8, at most the initial active limit |
| `initialWeight`, `commonWeight` | Relative odds alongside basic weight 1; weights grow linearly, and capped classes temporarily leave the draw |
| `levelsToCommon` | Earned levels after that class's reveal until common odds/limit; 1–100 |
| `initialMaxActive`, `commonMaxActive` | Shared class limits for regular/swarm arrivals, growing with the same ramp |
| `arrivalCost` | Budget spent by one fan; ordinary fans cost 1. A Banner costing 3 replaces three ordinary arrivals |

`fans[kind=2].charm` is Banner's base endurance; `followerValue` is XP per faint, while `moneyValue` stays
Training cash. Current Banner values are endurance 64, XP 120, cash 2, speed 2.2 and contact 6. Its reveal
count is 1, weights 0.20 → 0.32, ramp 6 levels, limits 6 → 18 and cost 3. Each newly introduced class
should increase pressure while keeping its distinct behavior. Current endurance and budget costs are:

| Class, in reveal order | Base HP | Arrival cost |
|---|---:|---:|
| Banner Squad | 64 | 3 |
| Filmer | 96 | 4 |
| Dad | 144 | 5 |
| Grandma | 176 | 6 |
| Headphone Crew | 224 | 7 |
| Plush Tosser | 288 | 8 |

Both individual endurance and endurance per arrival-budget unit rise along this ladder. Higher costs
reduce body arrivals at the same pressure budget. Movement, contact strength and XP/cash rewards are
unchanged. Other classes keep their weights, active limits and twelve-level ramps. Banner uses the faster six-level ramp
and six-active starting limit above. Each class still reveals alone. This is a tuning
target for a noticeable difficulty increase, not a substitute for a human playtest. Do not reintroduce
elapsed-time stat growth. Later tours start with previous classes established; their next class reveals rare.

Basic fans start fading at `retireBasicLevel` on `retireBasicTour` or later, over `basicFanFadeLevels` earned
levels. Current values are tour 1, level 32 and 20 levels, so basics are gone at 52. Swarm count settings now
mean ordinary-fan budget units: durable members buy fewer bodies. Saturated arrivals discard unused budget;
class caps and the global `maxHostiles = 90` never queue a release flood. A repeated late beat at a full
class allowance advances without adding more of that type.

Future Banner retunes need only this config: edit its `fans` row and/or `fanArrivals` row, preserve every
other row and unrelated field, run validation, publish and verify v5. The one update adding these profiles is required;
subsequent health/count/rarity/ramp/retirement changes need no rebuild. Do not copy v4 values onto v1–3.

## Shooting Star and Sound Wave

`Wink` now displays as Shooting Star: it automatically aims at tough visible fans and bursts around its
chosen target. `sparklePower` is total volley power, shared across `sparkleShots`; added stars spread the
volley or focus the same elite. `sparkleCooldown`, `sparkleSpeed` and `sparkleLifetime` keep their units.
`starBurstRadius` has five ranks, `starTurnDegrees` is steering degrees/second, `starTargetRange` excludes
hidden/HUD-covered fans, `starHitRadius` sets impact reach, `starVisualScale` sets size and `starFirstDelay`
sets the first cast. The legacy `sparklePierce`, `sparkleAimDegrees` and `sparkleSpreadDegrees` fields are
retained for compatibility but do not control the v5 homing star.

Sound Wave uses `soundWaveDamage`, `soundWaveCooldown`, `soundWaveRadius`, `soundWaveKnockback` and
`soundWaveSeconds`. The short pulse follows the idol in v5. Its three existing nonvocal ElevenLabs takes
play once on cast; `sfxPulseVolume`/`sfxPulseGap` control the mix. Preserve the Drone, fans, XP, Training,
arrival profiles and all unrelated values during ability retunes.

Orbit’s rank-one contact is 10 (was 8); higher ranks stay 10/12/15/18, retaining the closer-positioning payoff.
V4 receives the supported Wave numeric/text/mix and rank-one Orbit edits, so the currently installed older app can benefit
between matches. V1–3 values stay unchanged. V5 adds the new star mechanics/knobs and requires one app
update; subsequent supported power/cooldown/radius/steering/audio edits remain config-only. Career v4 is
preserved, and v5 uses its own balance cache.

## Useful settings

- `tourFanLevels`, `tourSingleLevels`, `tourRivalLevels`, `tourCycleLevels`: fan → single → rival phases. Current phases are 10/14/18, 20/24/28, then every ten levels.
- `spawnRateStart/End`, `spawnCurve`, `regularGroupSize`, `openingMaxHostiles`, `openingCrowdGraceSeconds`, `lateSwarmTimes/Fans`: arrival pacing. The opening limit applies to regular arrivals during its grace window; scripted swarms still use the shared global cap. Keep crowds readable and slow enough to steer through.
- `fans`: health/charm, speed, contact health loss, XP/cash rewards and collision radius per fan type. Fan endurance and contact strength do not grow with elapsed time: `charmGrowthLinear`, `charmGrowthQuadratic` and `damageGrowthPerMinute` are zero. Preserve that rule; difficulty progresses through tour slopes and the earned-level fan-arrival profiles.
- `fanScalingSecondsPerLevel`, `fanScalingOverflowFraction`: legacy limits for time-based fan stat scaling. They have no effect while the three growth coefficients remain zero.
- `crowdAreaQuietRate`: how much arrival pressure remains on cleared ground. Preserve time to collect loot, while preventing stationary safety.
- `firstLevelFollowers`, `openingLevelFollowers`, `levelGrowth`: XP requirements. Filling a bar must still earn its choice; rival battles hold choices until won.
- Ability arrays have five ranks. `fingerHeartPower`, `sparklePower`, `lightstickDamage`, `soundWaveDamage`, `photocardDamage`, `confettiDamage`, `fancamDamage` are internal values; cards show power ×10. Cooldowns are seconds.
- Shooting Star uses the stable `Wink` key. `sparklePower` is total volley power, divided across its shot count; see the v5 star fields above. The old spread/aim/pierce fields no longer control its behavior.
- `powerPerRank`, `protectionPerRank`, `cooldownReductionPerRank`, `areaPerRank`: match passive effects, written as fractions (0.15 means 15%).
- `training*`, signature settings and `careerGoalRewards`: permanent progression. Costs are twenty entries per track.
- `tourCashMultipliers`: six repeatable Training-cash rates, currently 1 / 1.25 / 1.5 / 1.75 / 2 / 2.25. Applies to bills and follower support, including Exit to Home; match XP, career goals and first-clear bonuses stay separate. Each run locks its rate and preserves fractional earnings.
- `tourHealthPerStop`, `tourArrivalsPerStop`, `rivalHealthPerStop`: linear increases per tour after Tour 1. Current increments are 20% fan endurance, 12% regular arrival pressure and 30% rival endurance. Do not infer an hours-to-progress target from these values.
- `maxHostiles`: strict shared active cap across ordinary arrivals, swarms, reveals and rival summons. Preserve 90 unless a requested change and testing justify otherwise. Required encounters make room; rejected arrivals do not queue.
- `selfiePhotos`, `selfiePhotoInterval`, `fancam*`: group-photo drone. `fancamDamage` is total burst power, divided across its photos; The frame half-width is 1.2 × `fancamRadius`; half-height is 0.9 × it. Existing follow-camera appearance values are legacy compatibility fields.
- `bubble*`: power, cooldown, radius, capture limit, lifetime, speed and range for one active hold-and-pop bubble. Rivals resist the hold.
- `standee*`: photo power/tick, cooldown, duration, attraction radius and fan limit for one cardboard photo prop. Rivals ignore the distraction.
- Hype, recovery, gifts, pickup ranges, camera/readability and audio mix are also in this snapshot.

Changes to mechanics, new IDs, art, audio recordings, pool sizes or code require a game update. Keep schema version 5 stable for supported value/text/unlock changes; incompatible changes require a new versioned endpoint. Run validation for all five versions before publication. Never add secrets, authentication tokens or personal data to this public repository.

## Health Regen and health gifts

`HealthRegen` is a passive available from Tour 1. `healthRegenFraction` contains five maximum-health
fractions per tick (currently 0.01/0.02/0.03/0.04/0.05); `healthRegenSeconds` is the gameplay interval
(currently 5 seconds). It uses the existing healing multiplier. Pauses, reveals and menus freeze the timer;
full-health ticks expire, and it cannot revive an overwhelmed idol. The passive uses one existing passive
slot. Its unlock/name/descriptions use `abilityUnlocks` and `abilityText` like the other abilities.

Health gifts keep `giftHealth = 8` maximum health plus healing. `giftHealFraction = 0.1` now controls the
previously fixed healing fraction of the new maximum. Feedback separately shows the cap increase and
actual extra healing; the world popup shows actual health gained. V6 adds this passive/config support and
requires a new app build once. Existing career v4 progress and v1–5 config values are preserved.
