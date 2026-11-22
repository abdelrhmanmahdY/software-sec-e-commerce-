# Checkout Consistency Investigation

**Investigation date:** 2026-11-22  
**Purpose:** Reconcile the discrepancy between two consecutive audit reports about four Naive Shop/Red Team files.  
**Boundary:** Read-only investigation. No file, commit, branch, index, database, or evidence was changed.

## 1. Conclusion

The inconsistency was real at the time of the audits, but it is not explained by a rename or duplicate inside the current workspace. The current working tree contains all four files.

The most likely explanation is that the workspace was in an older or incomplete checkout state when the latest missing-file audit ran. The repository was then updated/pulled to commit `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`, which is explicitly named `Restore files from previous commit` and adds `naive_shop/app.py` and the Red Team evidence/report assets.

No current evidence suggests that the files were renamed or moved.

## 2. Current repository identity

- **Absolute repository root:** `D:\software-sec-e-commerce-`
- **Repository `.git` directory:** `D:\software-sec-e-commerce-\.git`
- **Current branch from `.git\HEAD`:** `main`
- **Current local `main` commit:** `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`
- **Current `origin/main` commit:** `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`
- **Remote:** `https://github.com/abdelrhmanmahdY/software-sec-e-commerce-.git`

Git CLI was not available on `PATH`, so branch and commit state were read from the local `.git/HEAD`, refs and reflog, and verified against GitHub API.

## 3. Working-directory timeline

Local `.git/logs/HEAD` shows:

- Clone initialized at commit `993c4c0b9dfbbd467d3a0685ab09bd08a1babdd6`.
- Repeated pulls and branch checkouts through `944f9a761a0c99acb2d4293ad05c86e3525427b7`.
- A final fast-forward pull reached `7846452007ffd63abbd8d72ef6376274ef7ce613`.
- A subsequent fast-forward pull reached `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`.

The restore commit was timestamped `2026-11-22T01:39:02Z`. The local file timestamps for the four recovered files are `2026-11-22 3:39:37 AM` local time, consistent with the restore commit.

The current branch and remote branch both point to the restore commit.

## 4. Exact current-file locations

| File | Current absolute path | Exists now | Local timestamp |
|---|---|---|---|
| `naive_shop/app.py` | `D:\software-sec-e-commerce-\naive_shop\app.py` | Yes | 2026-11-22 3:39:37 AM |
| `red_team/live_tests/attack_naive.py` | `D:\software-sec-e-commerce-\red_team\live_tests\attack_naive.py` | Yes | 2026-11-22 3:39:37 AM |
| `red_team/evidence/naive_shop/attack_results.md` | `D:\software-sec-e-commerce-\red_team\evidence\naive_shop\attack_results.md` | Yes | 2026-11-22 3:39:37 AM |
| `red_team/reports/naive_vs_secureshop_comparison.md` | `D:\software-sec-e-commerce-\red_team\reports\naive_vs_secureshop_comparison.md` | Yes | 2026-11-22 3:39:37 AM |

## 5. Workspace search locations

An accessible-workspace filename search was run across:

- `D:\`
- `C:\Users\jun69`

Within these locations, the exact project copies found were:

- `D:\software-sec-e-commerce-\naive_shop\app.py`
- `D:\software-sec-e-commerce-\red_team\live_tests\attack_naive.py`
- `D:\software-sec-e-commerce-\red_team\evidence\naive_shop\attack_results.md`
- `D:\software-sec-e-commerce-\red_team\reports\naive_vs_secureshop_comparison.md`

No separate project copy or alternate Red Team location for these exact paths was found.

The broad search also found many unrelated Python `app.py` files, but no second copy of the four CET431-specific files.

## 6. Git history and branches

GitHub API and local `.git` refs were used because no Git CLI executable was available.

### `main`

All four paths exist at commit `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`.

The commit `6dc3f28278` has the message:

`Restore files from previous commit`

The commit's file patch confirms:

- `naive_shop/app.py` was **added**.
- The restore commit also restored a number of Red Team/report files.

The commit's parent is `7846452007ffd63abbd8d72ef6376274ef7ce613`.

### `password`

Local remote ref: `012af4f964edcad0c1f94406248d0e02d8c6752a`.

GitHub API content checks for all four paths on `password` returned 404. Therefore, the password branch is not a location containing these files.

### Other local refs

- Local `totp` ref: `944f9a761a0c99acb2d4293ad05c86e3525427b7`.
- GitHub API currently reports the active public branches as `main` and `password`; no active `totp` branch was reported.
- A content check for `naive_shop/app.py` on `totp` returned 404.

## 7. Rename, move, ignore, delete, or alternate directory

### Rename

No evidence of a rename was found. All four names appear exactly under their earlier documented paths.

### Move

No alternate copy or moved path was found in the accessible workspace.

### Ignore

No evidence was found that the files are ignored. They are present in the working tree and in the GitHub `main` tree.

### Delete

The files were absent during the earlier audit checks, but the Git history shows them restored later by commit `6dc3f28278d0f680b63a20a32f169d0fa6b5854a`.

The fact that they are now present and share the same 3:39:37 timestamp strongly supports a checkout/update event, not deletion followed by a separate manual recreation.

### Alternate directory

No alternate CET431 copy was found. A nested `D:\software-sec-e-commerce-\software-sec-e-commerce-` directory exists but contains only `.gitignore`, not a project copy.

## 8. Previous audit root references

The previous audit reports use the same repository root:

- `D:\software-sec-e-commerce-`

The earlier report text refers to paths such as:

- `naive_shop/app.py`
- `red_team/live_tests/attack_naive.py`
- `red_team/evidence/naive_shop/attack_results.md`
- `red_team/reports/naive_vs_secureshop_comparison.md`

These were repository-relative paths and did not point to another root.

No evidence was found that a different repository root was used by the two earlier audits.

## 9. Most likely explanation

The latest missing-file result was stale relative to the workspace that was subsequently restored or updated.

Evidence supporting this explanation:

1. The files are now present at the exact four absolute paths previously reported.
2. All four have the same local timestamp.
3. Commit `6dc3f28278d0f680b63a20a32f169d0fa6b5854a` explicitly restores files.
4. The commit adds `naive_shop/app.py` and restored Red Team assets.
5. The local `main` ref and `origin/main` both now point to that restore commit.
6. No rename, alternate copy, ignored location, or separate repository root was found.

## 10. Safe to proceed

It is safe to proceed with read-only Naive Shop verification and gap analysis.

Before implementation or recovery work:

- Verify that the current branch and commit are intentionally the submission state.
- Decide whether a new commit or workspace backup is required before any implementation.
- Do not restore or overwrite files solely to prove they existed; they are now present.
- Start Naive Shop and execute the existing attack script only if a separate implementation/execution phase is approved.

Current red_team report [red_team_final_deliverables_checklist.md](/D:/software-sec-e-commerce-/red_team/reports/red_team_final_deliverables_checklist.md) contains statements that the four files are missing. Those statements are now outdated and should not be used as current evidence until reconciled.
