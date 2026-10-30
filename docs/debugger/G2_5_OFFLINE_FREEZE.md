# G2.5 Offline Debugger — Freeze Manifest

- UTC verification: `2026-10-29T18:44:48.975813+00:00`
- Baseline commit: `a15c446`
- Branch: `feature/z8f0822-hardware`
- Status: `OFFLINE VALIDATION PASSED`
- Hardware verified: `false`

## Evidence Classification

- Candidate protocol: `STATIC_DLL`
- Trace replay: `SYNTHETIC`
- Protocol bytes are not hardware-confirmed.
- Identity bytes are opaque and do not establish device model.

## Regression

- Pytest: `268 passed`
- Subtests: `24 passed`
- Offline CLI: exit code `0`
- CLI output: `MOCK ONLY: candidate handshake accepted; no hardware verified`

## Safety Boundary

- Offline debugger modules statically audited.
- No physical transport is authorized by this freeze.
- No serial I/O, MCU reset, flash, erase, or programming authorized.
- Static AST checks are not proof of whole-repository hardware isolation.
- `tools/` is pre-existing user-owned untracked content and excluded.

## Audited File SHA-256

- `ez8native/debugger/__init__.py`: `5ca06f58d4cdad0adc16fa44ea38d6fbf29462af3330687c94aa72608db6f94a`
- `ez8native/debugger/cable_protocol.py`: `7909e0377c6a02c7d4e35486ccc18182ddd6ef751cada86b48b1d468e3877bdf`
- `ez8native/debugger/cli.py`: `186fe666da5f37b0ac9a970238fd4d76c5fab06ae1d91ff133a1e3c65102dfd2`
- `ez8native/debugger/event_replay.py`: `29bb96997fbabc2f33448c4e856cf4e0b6f90fb5eb3325838aea600da6a19b9c`
- `ez8native/debugger/mock_transport.py`: `b1d6bbea5299ca89d8198db89b5edc6fcddb3b0dadc80847895d23a02c39e608`
- `ez8native/debugger/ocd.py`: `c0b84d7bceea111193424697977980182db4c47fe415b28586d6ba1568a65f95`
- `ez8native/debugger/offline_replay_session.py`: `c274e9ab6d6124303a6694f963172aaa2584a4c10148d7199f1fd0ebad6f8ff1`
- `ez8native/debugger/safety.py`: `c89bc7f1033ad19dbe989b6828bd5550161c086bbdb84127d7ebe751442ceab3`
- `ez8native/debugger/session.py`: `5606c6a8fb7a899ee2cd403b21a28b141232fa1ababc101dab58d6f84549db64`
- `ez8native/debugger/trace_replay.py`: `2e35723540d32aa4cd0d919088232542f4c5f21925fbbae12128ee5d20eea9da`
- `ez8native/debugger/transport.py`: `91f480708c27d7d106bd97a948f7c42faa927e1f30318a00fd9fa6871de147e1`
- `tests/fixtures/debugger/d52_synthetic_traces.json`: `05e6b6670725e2f43cc6cb960394a3a5fad2d275ae3d2c8431515998c826871a`

## Release Gates

- D49–D54: complete.
- D55: verification passed; formal commit and tag pending.
- G2.5: not formally frozen until final review and tag.
- G3: physical cable validation requires separate authorization.
- G4: target OCD validation remains blocked.
