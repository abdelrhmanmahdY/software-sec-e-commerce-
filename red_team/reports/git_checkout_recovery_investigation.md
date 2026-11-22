# Git Checkout and Naive Shop Recovery Investigation

Investigation date: 2026-11-22  
Scope: read-only Git/workspace inspection, plus creation of this report only.

## Executive summary

The repository is at `D:\software-sec-e-commerce-`, on branch `main`, at
`c9776b750677c942410572d1afbf3c786f336b9d`. The previous HEAD is recoverable
from the reflog as `e01fa0dad933fc30d04b4160f0fbd089ef2d3f99`.

The HEAD change was a commit named `update` at 2026-11-22 06:53:21 +02:00,
whose parent is the previous HEAD. The reflog records no checkout, reset, or
pull between those two commits. The commit did not modify
`naive_shop/app.py`; its app blob is identical at the previous and current
HEADs. The current app is the older, minimal API/demo implementation, not the
responsive UI that was browser-tested earlier.

All four listed uncommitted Red Team files are present. The only modified
tracked file is `red_team/live_tests/attack_naive.py`; the other three are
untracked. No uncommitted Blue Team file appears in `git status` or the
worktree diff. No recovery, branch switch, restore, database operation, or
Docker operation was performed.

The earlier UI source is not present in the current worktree, any reachable
branch/commit, the reflog, or the unreachable Git objects inspected. The exact
operation that removed the transient UI source is not recorded by Git and
cannot be established from available evidence.

## Current Git state

| Item | Observed value |
|---|---|
| Absolute repository path | `D:\software-sec-e-commerce-` |
| Branch | `main` |
| HEAD | `c9776b750677c942410572d1afbf3c786f336b9d` |
| Upstream | `origin/main` at the same commit |
| Previous HEAD | `e01fa0dad933fc30d04b4160f0fbd089ef2d3f99` |
| Staged changes | None |
| Modified tracked files | `red_team/live_tests/attack_naive.py` |
| Untracked files | The two Naive Shop evidence files and `red_team/live_tests/verify_inmemory_security.py` |

The full uncommitted status is:

```text
 M red_team/live_tests/attack_naive.py
?? red_team/evidence/naive_shop/naive_attack_20261122T045547Z.md
?? red_team/evidence/naive_shop/naive_attack_live_20261122_e01fa0.md
?? red_team/live_tests/verify_inmemory_security.py
```

The tracked-file diff summary is 195 insertions and 72 deletions in
`attack_naive.py`. There is no staged diff.

## Reflog and commit history

Relevant local reflog entries:

| Local time (+02:00) | HEAD | Reflog action |
|---|---|---|
| 2026-11-22 06:28:01 | `e01fa0d` | `commit: update` |
| 2026-11-22 06:53:21 | `c9776b7` | `commit: update` |

The `c9776b7` commit has `e01fa0d` as its parent. The reflog shows `origin/main`
updated by push at 06:53:28 and remote HEAD metadata updated at 06:53:30.
There is no checkout/reset entry between the two HEAD commits. Therefore the
observed HEAD change was a new commit on `main`, not a branch switch.

The latest commit touches 24 paths, including Blue Team files and Red Team
reports/evidence. Its changed-path list does not include `naive_shop/app.py`.
It removes two metadata lines from the tracked summary
`red_team/evidence/naive_shop/attack_results.md` and adds
`red_team/evidence/naive_shop/naive_attack_20261122T043606Z.md`; this is a
committed change, separate from the four current uncommitted files.

## Naive Shop UI location and history

### Current checkout

`naive_shop/` contains only `app.py`; no separate HTML, CSS, or JavaScript
frontend assets were found there. The current [app.py](../../naive_shop/app.py)
serves a simple home page and the V1-V7 demonstration routes. It is not the
responsive catalogue/cart/profile UI previously observed in the browser.

The file's Git blob ID is `9b32f259c6f662f07412879ac25a21c44bb8d8cc` in both
the current worktree and current HEAD. The same blob ID is present at the
previous HEAD and at commits `6dc3f28` and `60f305f`. The current and previous
HEADs have no diff for `naive_shop/app.py`.

### Historical revisions and branches

The path history found by `git log --all --follow` is:

| Commit | Path action |
|---|---|
| `60f305f` | Added `naive_shop/app.py` |
| `9da6ca5` | Deleted `naive_shop/app.py` |
| `6dc3f28` | Added/restored `naive_shop/app.py` |

No reachable commit on the listed local or remote branches contains the
responsive UI version. The latest commit did not delete, move, or replace the
app path. The earlier browser-tested UI therefore appears to have existed
only as a transient working-tree version, or in a source location not found
in the accessible repository history.

`git fsck --full --no-reflogs --unreachable` found eight unreachable trees and
two unreachable blobs, with no unreachable commit. The tree entries that
reference `naive_shop/app.py` reference the same current app blob. The two
unreachable blobs inspected are a JSON backend-results snapshot and a
regression-results Markdown file, not the UI source. These objects do not
provide a recoverable copy of the responsive UI.

### Running service

At investigation time, there was no listener on `127.0.0.1:8010`. No browser
request was made, and the shared browser tab was not treated as proof that a
server or a particular source revision was still running.

## Status of the four uncommitted Red Team files

| File | Worktree status | Size | SHA-256 | Assessment |
|---|---|---:|---|---|
| [attack_naive.py](../live_tests/attack_naive.py) | Modified tracked file | 9,954 bytes | `C7259EA69E24AB176DDC12FF13D104C5F76B172A7FD32755586C55DF2E95160A` | Present; diff inspected. The uncommitted version constrains the target to loopback, writes dated evidence without overwriting existing files, and records sanitized HTTP exchanges. |
| [verify_inmemory_security.py](../live_tests/verify_inmemory_security.py) | Untracked | 7,904 bytes | `CCAD9EF10A121890155A8647AB2D760158D7F4B5384C724E873E75AD11E17979` | Present and readable; not part of Git history. |
| [naive_attack_20261122T045547Z.md](../evidence/naive_shop/naive_attack_20261122T045547Z.md) | Untracked | 13,820 bytes | `B38AC75DA2EACF33C7EB5D421E34DFDC1E766E3D7402EC2D49A63E6FB5E2D4F6` | Present; contains timestamped, sanitized request/response evidence for V1-V7. |
| [naive_attack_live_20261122_e01fa0.md](../evidence/naive_shop/naive_attack_live_20261122_e01fa0.md) | Untracked | 1,014 bytes | `E9D73104F1817423DB5F57AA12EC95B796E18040BC7DB9CC054F1FCA39671F81` | Present; short run summary, not equivalent to the raw exchange evidence above. |

No missing or truncated condition was observed for these four files. The
report does not classify the summary-only file as complete raw evidence.

## Blue Team file check

The only modified tracked path in the current worktree is under
`red_team/live_tests/`. All untracked paths are also under `red_team/`.
Therefore, no Blue Team file appears in the current uncommitted changes.

The `c9776b7` commit itself includes committed changes to Blue Team paths such
as `audit/`, `config/`, `dashboard/`, `users/`, and Docker configuration.
Those are committed changes, not uncommitted changes from this investigation.

## Potential data loss and limits

- The prior responsive UI code is absent from the current `naive_shop/app.py`,
  all reachable Git revisions/branches, the reflog, and the unreachable Git
  objects inspected.
- The previous UI was reported as browser-tested, but that browser result
  does not preserve its source. No source backup was found in the repository.
- The reflog records ref movements and commits, not ordinary edits or
  overwrites of a tracked working-tree file. Since `c9776b7` does not touch
  `naive_shop/app.py`, Git evidence does not explain when or how its transient
  UI changes disappeared.
- The four listed Red Team files are intact in the current worktree. No
  database or Docker state was inspected or changed.

## Safe recommended recovery procedure

No recovery has been performed. Before attempting any recovery:

1. Preserve the current worktree, especially the modified `attack_naive.py`
   and all three untracked Red Team files. Do not run checkout, restore,
   reset, clean, stash, or another pull against this state.
2. Inspect VS Code Local History/Timeline, session snapshots, and any
   explicitly configured file backups for an earlier `naive_shop/app.py`.
   Compare candidate versions without replacing the current file.
3. If a candidate is found, copy it to a separate review location and verify
   its content and hash before considering restoration.
4. If no source copy exists, coordinate with the project owner and rebuild
   the UI as a separate, reviewed Red Team change, preserving the existing
   V1-V7 routes and local-only isolation.
5. After any separately authorized recovery, rerun the documented local
   browser checks and attack tests, and record new evidence under a new
   filename rather than overwriting historical evidence.

This investigation stops without recovering or modifying any existing file.
