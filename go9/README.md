# Go9

This folder is a work-in-progress 9x9 Go implementation for the
alpha-zero-general training loop.

The folder was copied from `othello/`, so the PyTorch wrapper is already in the
right shape, but the game rules are still Othello-like until `Go9Logic.py` and
`Go9Game.py` are rewritten.

## Current Structure

```text
Go9/
  Go9Game.py              # Game interface used by Coach and MCTS
  Go9Logic.py             # Board rules: legal moves, captures, terminal logic
  Go9Players.py           # Optional players for Arena / manual testing
  __init__.py
  pytorch/
    NNet.py               # Wrapper used by Coach: train, predict, save, load
    Go9NNet.py            # PyTorch model architecture
    __init__.py
```

`Coach.py` and `MCTS.py` do not need Go-specific changes. They only require:

```text
Game implementation:
  getInitBoard
  getBoardSize
  getActionSize
  getNextState
  getValidMoves
  getGameEnded
  getCanonicalForm
  getSymmetries
  stringRepresentation

NeuralNet wrapper:
  train
  predict
  save_checkpoint
  load_checkpoint
```

## PyTorch Model

The PyTorch path is:

```python
from Go9.pytorch.NNet import NNetWrapper as nn
```

`pytorch/NNet.py` is the wrapper. It should usually keep the name `NNet.py`,
because the rest of the repo imports wrappers with the same convention.

`pytorch/Go9NNet.py` is the actual neural network architecture. It currently
uses the Othello-style model:

```text
input: 9 x 9 board
Conv2d 1 -> 512
Conv2d 512 -> 512
Conv2d 512 -> 512
Conv2d 512 -> 512
Linear -> 1024
Linear -> 512
policy head: 512 -> action_size
value head: 512 -> 1
```

For 9x9 Go:

```text
action_size = 9 * 9 + 1 = 82
```

The extra action is pass.

This model is enough for a first smoke test. A stronger Go model should later
use more input feature planes and residual blocks.

## Migration Checklist

### 1. Fix `main.py`

Change the imports:

```python
from Coach import Coach
from Go9.Go9Game import Go9Game as Game
from Go9.pytorch.NNet import NNetWrapper as nn
from utils import *
```

Create the game as 9x9:

```python
g = Game(9)
```

Use a separate checkpoint folder:

```python
'checkpoint': './temp/go9/',
'load_folder_file': ('./temp/go9/', 'best.pth.tar'),
```

For the first smoke test, use small training settings:

```python
'numIters': 1,
'numEps': 2,
'numMCTSSims': 5,
'arenaCompare': 2,
```

After the rules work, increase these values.

### 2. Rewrite `Go9Logic.py`

This is the most important file. It still contains Othello rules.

Replace the Othello logic with Go logic:

```text
Board state:
  +1 = current player's stones in canonical form
  -1 = opponent stones
   0 = empty

Rules needed:
  place a stone
  find connected groups
  count liberties
  remove captured opponent groups
  reject suicide moves
  handle pass action
  track ko or superko state
```

Important note: the current board array alone is not enough to implement ko
perfectly, because ko needs previous-position history. The simplest first
version can ignore ko for a smoke test, then add history support later.

### 3. Update `Go9Game.py`

Keep the same public interface, but make the methods call Go rules.

Expected 9x9 values:

```python
def getBoardSize(self):
    return (9, 9)

def getActionSize(self):
    return 9 * 9 + 1
```

`getNextState` should:

```text
if action is pass:
  return board, -player
else:
  place stone
  capture opponent stones
  return next board, -player
```

`getValidMoves` should return a binary vector of length 82:

```text
1 for legal board moves
1 for pass
0 for illegal moves
```

`getGameEnded` should eventually detect:

```text
two consecutive passes
or a maximum move limit for early experiments
```

Then score the game.

For a first version, area scoring is simpler:

```text
score = stones + surrounded territory + komi adjustment
```

### 4. Keep `getCanonicalForm`

For a first version, keep:

```python
return player * board
```

This lets the network always see:

```text
+1 = side to move
-1 = opponent
 0 = empty
```

### 5. Keep `getSymmetries`

The Othello symmetry code is also useful for Go:

```text
4 rotations x 2 mirror choices = 8 symmetries
```

Make sure the policy vector is split as:

```text
pi[:-1] = 9x9 board actions
pi[-1]  = pass action
```

The pass probability should be appended unchanged after rotating/flipping the
board-action probabilities.

### 6. Check `Go9NNet.py`

The copied model should run for 9x9 because:

```python
self.fc1 = nn.Linear(
    args.num_channels * (self.board_x - 4) * (self.board_y - 4),
    1024
)
```

For 9x9 this becomes:

```text
512 * 5 * 5 = 12800
```

So no immediate dimension change is required.

Later improvements:

```text
use all conv layers with padding=1
replace the fully connected trunk with residual blocks
use multiple input planes for history, liberties, ko, and color
```

### 7. Smoke Test Before Training

Before running full training, test the interfaces:

```bash
python - <<'PY'
from Go9.Go9Game import Go9Game
from Go9.pytorch.NNet import NNetWrapper

g = Go9Game(9)
b = g.getInitBoard()
print("board", b.shape)
print("action size", g.getActionSize())
print("valid moves", g.getValidMoves(b, 1).sum())

n = NNetWrapper(g)
pi, v = n.predict(g.getCanonicalForm(b, 1))
print("pi", pi.shape, pi.sum())
print("v", v)
PY
```

Expected:

```text
board (9, 9)
action size 82
pi (82,)
```

### 8. Start Tiny Training

After the smoke test passes:

```bash
python main.py
```

Use tiny settings first:

```text
numIters = 1
numEps = 2
numMCTSSims = 5
arenaCompare = 2
```

Only scale up after:

```text
self-play finishes
training finishes
arena comparison finishes
checkpoint is saved
```

## Known TODOs

```text
[ ] Replace Othello setup in Go9Logic.Board.__init__
[ ] Replace Othello move generation with Go legal moves
[ ] Implement captures
[ ] Implement suicide rule
[ ] Add pass handling
[ ] Add terminal detection
[ ] Add scoring
[ ] Decide how to handle ko / superko
[ ] Update Go9Players.py or remove Othello-specific players
[ ] Run smoke test
[ ] Run tiny training
```
