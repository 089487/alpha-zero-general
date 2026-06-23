# Go9 Assignment TODO

This file treats the 9x9 Go port as a staged assignment. Complete one stage at
a time, run the matching eval, inspect the output, then move on.

Run evals from the repository root:

```bash
python scripts/eval_go9_stages.py --stage empty
python scripts/eval_go9_stages.py --stage moves
python scripts/eval_go9_stages.py --stage groups
python scripts/eval_go9_stages.py --stage capture
python scripts/eval_go9_stages.py --stage suicide
python scripts/eval_go9_stages.py --stage game
python scripts/eval_go9_stages.py --stage model
python scripts/eval_go9_stages.py --stage mcts
python scripts/eval_go9_stages.py --stage terminal
python scripts/eval_go9_stages.py --stage scoring
python scripts/eval_go9_stages.py --stage episode
python scripts/eval_go9_stages.py --stage tiny-train
```

Use `--stage all` only after the earlier stages pass.

## Stage 1: Empty Board

Goal:

- `Board(9)` starts as a completely empty 9x9 board.
- No Othello starting stones remain.

What to implement:

- In `go9/Go9Logic.py`, `Board.__init__` should create a 9x9 grid of zeros.

Eval:

```bash
python scripts/eval_go9_stages.py --stage empty
```

Inspect:

- Board size is 9x9.
- Stone count is 0.

## Stage 2: Basic Moves

Goal:

- Empty intersections are legal.
- Occupied intersections are illegal.
- `execute_move` places a stone.
- `has_legal_moves` reflects whether any empty point exists.

What to implement:

- `Board.get_legal_moves(color)`
- `Board.has_legal_moves(color)`
- `Board.execute_move(move, color)` for simple stone placement.

Eval:

```bash
python scripts/eval_go9_stages.py --stage moves
```

Inspect:

- Empty board has 81 board moves.
- After one move, that point is no longer legal.
- A full board has no board moves.

## Stage 3: Groups And Liberties

Goal:

- Use 4-neighbor Go adjacency, not Othello diagonals.
- Connected same-color stones form one group.
- Liberties are unique empty neighboring points around the whole group.

What to implement:

- `Board._neighbors(x, y)`
- `Board._get_group(x, y)`
- `Board._get_liberties(group)`

Eval:

```bash
python scripts/eval_go9_stages.py --stage groups
```

Inspect:

- Corner stone has 2 liberties.
- Center stone has 4 liberties.
- Two connected stones form one group.

## Stage 4: Capture

Goal:

- After a move, adjacent opponent groups with zero liberties are removed.

What to implement:

- Extend `Board.execute_move(move, color)` to remove captured opponent groups.

Eval:

```bash
python scripts/eval_go9_stages.py --stage capture
```

Inspect:

- A surrounded single stone is removed.
- A surrounded multi-stone group is removed.

## Stage 5: Suicide Rule

Goal:

- Suicide moves are illegal.
- A move that has no liberties but captures opponent stones is legal.

What to implement:

- Add an internal legality helper, for example `_is_legal_move(move, color)`.
- Update `get_legal_moves` to use it.
- Keep `execute_move` assuming it is given a legal move.

Eval:

```bash
python scripts/eval_go9_stages.py --stage suicide
```

Inspect:

- Pure suicide is absent from legal moves.
- Capture-that-saves-self is present in legal moves.

## Stage 6: Game Interface

Goal:

- `Go9Game` maps board moves to an action vector of length 82.
- Action 81 is pass.
- Symmetries keep pass probability unchanged.

What to implement:

- `Go9Game.getValidMoves`
- `Go9Game.getNextState`
- Keep `Go9Game.getSymmetries` compatible with 9x9 board actions plus pass.

Eval:

```bash
python scripts/eval_go9_stages.py --stage game
```

Inspect:

- Initial valid vector has shape 82.
- Pass action is valid.
- Symmetry count is 8.

## Stage 7: Model Smoke

Goal:

- PyTorch wrapper and `Go9NNet` accept 9x9 boards.
- Policy output length is 82.
- Value output is in `[-1, 1]`.

Eval:

```bash
python scripts/eval_go9_stages.py --stage model
```

Inspect:

- Policy sums to 1.
- Value is scalar-like and bounded.

## Stage 8: MCTS Smoke

Goal:

- MCTS can run from the initial Go9 board without zero-division or invalid moves.

Eval:

```bash
python scripts/eval_go9_stages.py --stage mcts
```

Inspect:

- MCTS policy length is 82.
- MCTS policy sums to 1.

## Stage 9: Terminal Safety

Goal:

- Self-play episodes can terminate.
- Pass action is handled as a real move.
- Until two-pass state tracking exists, use a deterministic move-limit fallback.

What to implement:

- Add terminal handling in `Go9Game.getGameEnded`.
- Recommended v1 default: a board is terminal when it is full, or when a simple
  fallback move limit is reached if you add move-count state later.
- Keep `getGameEnded` returning:
  - `0` if the game continues.
  - `1` if the current `player` is ahead.
  - `-1` if the current `player` is behind.
  - a small non-zero draw value if tied.

Eval:

```bash
python scripts/eval_go9_stages.py --stage terminal
```

Inspect:

- Empty board is not terminal.
- Full board is terminal.
- A simple winning/losing board returns opposite signs for opposite players.

## Stage 10: Scoring

Goal:

- Scoring is Go-like enough for training smoke tests.
- For v1, use simple area-style scoring.

What to implement:

- Update `Go9Game.getScore(board, player)` or add Board-level helpers.
- Recommended v1 score:
  - player's stones
  - plus empty territory fully surrounded by that player
  - minus opponent's corresponding area
- Komi can be ignored in v1 unless you want a fixed white bonus.

Eval:

```bash
python scripts/eval_go9_stages.py --stage scoring
```

Inspect:

- More stones gives a higher score.
- Surrounded empty territory counts for the surrounding player.
- Neutral empty space is not counted as either player's territory.

## Stage 11: Two-Pass Ending

Goal:

- Pass remains a legal Go action.
- Two consecutive passes end the game.
- Pass tracking must be part of the game state, not mutable global state on
  `Go9Game`, so MCTS branches do not pollute each other.

What to implement:

- Extend the Go9 state representation so it can track at least:
  - the 9x9 stone board
  - consecutive pass count
- Update all methods that consume or produce state:
  - `getInitBoard`
  - `getNextState`
  - `getGameEnded`
  - `getCanonicalForm`
  - `getSymmetries`
  - `stringRepresentation`
  - model input preparation if the neural net still expects only 9x9 stones
- Do not implement pass count as `self.consecutive_passes` on `Go9Game`.
  MCTS explores many hypothetical branches with the same `game` object, so
  mutable game-level pass state will be wrong.
- After a non-pass move, reset consecutive pass count to 0.
- After a pass move, increment consecutive pass count.
- When consecutive pass count reaches 2, `getGameEnded` should return the
  scoring result.

Eval:

```bash
python scripts/eval_go9_stages.py --stage episode
```

Inspect:

- Initial state has pass count 0.
- One pass changes player and pass count becomes 1.
- A normal move resets pass count to 0.
- Two consecutive passes make `getGameEnded` return non-zero.
- `stringRepresentation` distinguishes the same stone board with different
  pass counts.

## Stage 12: Tiny Training Smoke

Goal:

- One tiny `Coach.learn()` run completes end to end.

What to implement:

- Keep `main.py` tiny settings or use the eval's built-in tiny args.
- Ensure checkpoints can be saved under `./temp/go9_eval/`.

Eval:

```bash
python scripts/eval_go9_stages.py --stage tiny-train
```

Inspect:

- Self-play finishes.
- Training finishes.
- Arena comparison finishes.
- `temp/go9_eval/` contains checkpoint/example output.

## Later Work

Do these only after all staged evals above pass:

- Ko or superko.
- Stronger residual network and richer input planes.
