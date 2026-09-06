# DNA MIDI Studio 9.01 — Factory Style Family Calibration

## Purpose
Use direct Factory Style evidence for 6/8, Rock, Techno/Dance, Ballad and Beat families rather than treating all non-GOLD meters/styles as generic 4/4 fallback.

## Authority
- Factory: family groove skeleton, density/gate/tempo evidence, velocity authority.
- GOLD: live/Balkan performance character where evidence exists; not used to manufacture Factory family profiles.
- Candidate calibration remains velocity-free; velocity rendering remains Factory-only.

## Corpus evidence
| Family | Factory segments | Distinct styles | Median tempo | Median density/bar | Median gate @96 PPQ |
|---|---:|---:|---:|---:|---:|
| 6/8 | 628 | 5 | 85 | 5.2915 | 17.0 |
| Rock | 447 | 4 | 68 | 9.0 | 23.0 |
| Techno/Dance | 2051 | 20 | 116 | 10.333 | 19.0 |
| Ballad | 2743 | 26 | 76 | 8.0 | 23.5 |
| Beat | 1938 | 24 | 95 | 7.75 | 23.5 |

## 6/8 correction
9.00 marked 6/8 as a conservative fallback because direct GOLD coverage was weak. 9.01 correctly promotes 6/8 to a learned profile backed by Factory Style segments. The public meter calibration API now returns a direct learned 6/8 profile.

## Safety
This layer does not mutate MIDI by itself. It supplies evidence to scoring/selection. It does not use GOLD velocity and does not override the Factory-only velocity rule.

## Tests
Targeted Factory family + meter + 8.80 corpus + full-song regression: 13/13 PASS.
