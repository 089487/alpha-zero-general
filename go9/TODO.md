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

## Later Work

Do these only after all staged evals above pass:

- Terminal detection.
- Scoring.
- Two-pass ending.
- Ko or superko.
- Stronger residual network and richer input planes.
