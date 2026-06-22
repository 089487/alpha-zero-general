import argparse
import math
import signal
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Coach import Coach
from MCTS import MCTS
from go9.Go9Game import Go9Game
from go9.pytorch.NNet import NNetWrapper
from utils import dotdict


def ok(message):
    print(f"[OK] {message}")


def fail(message):
    raise AssertionError(message)


def check(condition, message):
    if not condition:
        fail(message)
    ok(message)


def make_args(num_mcts_sims):
    return dotdict(
        {
            "numIters": 1,
            "numEps": 1,
            "tempThreshold": 15,
            "updateThreshold": 0.6,
            "maxlenOfQueue": 200000,
            "numMCTSSims": num_mcts_sims,
            "arenaCompare": 2,
            "cpuct": 1,
            "checkpoint": "./temp/go9_smoke/",
            "load_model": False,
            "load_folder_file": ("./temp/go9_smoke/", "best.pth.tar"),
            "numItersForTrainExamplesHistory": 20,
        }
    )


def smoke_game_and_model():
    print("\n== Game + Model ==")
    game = Go9Game(9)
    board = game.getInitBoard()

    check(isinstance(board, np.ndarray), "initial board is a numpy array")
    check(board.shape == (9, 9), f"initial board shape is (9, 9), got {board.shape}")
    check(game.getBoardSize() == (9, 9), f"board size is (9, 9), got {game.getBoardSize()}")
    check(game.getActionSize() == 82, f"action size is 82, got {game.getActionSize()}")

    stone_count = int(np.abs(board).sum())
    if stone_count == 0:
        ok("initial board is empty")
    else:
        print(f"[WARN] initial board has {stone_count} stones; Go should start empty")

    canonical = game.getCanonicalForm(board, 1)
    check(canonical.shape == (9, 9), "canonical board shape is (9, 9)")

    nnet = NNetWrapper(game)
    pi, v = nnet.predict(canonical)
    check(pi.shape == (82,), f"policy shape is (82,), got {pi.shape}")
    check(math.isclose(float(pi.sum()), 1.0, rel_tol=1e-5, abs_tol=1e-5), f"policy sums to 1, got {pi.sum()}")
    check(np.asarray(v).shape in [(), (1,)], f"value has scalar-like shape, got {np.asarray(v).shape}")
    check(-1.0001 <= float(np.asarray(v).reshape(-1)[0]) <= 1.0001, f"value is in [-1, 1], got {v}")

    return game, nnet, board


def smoke_rules(game, board):
    print("\n== Basic Rules Interface ==")
    valids = game.getValidMoves(board, 1)
    check(valids.shape == (82,), f"valid move vector shape is (82,), got {valids.shape}")
    check(valids[-1] in [0, 1], f"pass action is binary, got {valids[-1]}")
    check(np.all((valids == 0) | (valids == 1)), "valid move vector is binary")
    print(f"[INFO] valid moves at start: {int(valids.sum())}")

    legal_actions = np.flatnonzero(valids)
    check(len(legal_actions) > 0, "there is at least one legal action")

    non_pass = [int(a) for a in legal_actions if a != game.getActionSize() - 1]
    action = non_pass[0] if non_pass else int(legal_actions[0])
    next_board, next_player = game.getNextState(board, 1, action)
    check(next_board.shape == (9, 9), "next board shape is (9, 9)")
    check(next_player == -1, f"next player flips to -1, got {next_player}")

    ended = game.getGameEnded(next_board, next_player)
    check(isinstance(ended, (int, float, np.integer, np.floating)), f"game ended returns numeric value, got {type(ended)}")
    print(f"[INFO] getGameEnded after one move: {ended}")

    pi = np.ones(game.getActionSize(), dtype=np.float64) / game.getActionSize()
    syms = game.getSymmetries(board, pi)
    check(len(syms) == 8, f"symmetry count is 8, got {len(syms)}")
    for sym_board, sym_pi in syms:
        check(sym_board.shape == (9, 9), "symmetry board shape is (9, 9)")
        check(len(sym_pi) == 82, f"symmetry policy length is 82, got {len(sym_pi)}")


def smoke_mcts(game, nnet, board, num_mcts_sims):
    print("\n== MCTS ==")
    args = dotdict({"numMCTSSims": num_mcts_sims, "cpuct": 1})
    mcts = MCTS(game, nnet, args)
    canonical = game.getCanonicalForm(board, 1)
    pi = mcts.getActionProb(canonical, temp=1)

    check(len(pi) == 82, f"MCTS policy length is 82, got {len(pi)}")
    check(math.isclose(float(sum(pi)), 1.0, rel_tol=1e-5, abs_tol=1e-5), f"MCTS policy sums to 1, got {sum(pi)}")
    print(f"[INFO] nonzero MCTS actions: {sum(x > 0 for x in pi)}")


def smoke_episode(game, nnet, num_mcts_sims, timeout_seconds):
    print("\n== executeEpisode ==")

    def timeout_handler(signum, frame):
        raise TimeoutError(f"executeEpisode timed out after {timeout_seconds}s")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        coach = Coach(game, nnet, make_args(num_mcts_sims))
        examples = coach.executeEpisode()
    finally:
        signal.alarm(0)

    check(len(examples) > 0, f"episode produced examples, got {len(examples)}")
    board, pi, value = examples[0]
    check(board.shape == (9, 9), "example board shape is (9, 9)")
    check(len(pi) == 82, f"example policy length is 82, got {len(pi)}")
    check(-1.0001 <= float(value) <= 1.0001, f"example value is in [-1, 1], got {value}")


def main():
    parser = argparse.ArgumentParser(description="Smoke test the go9 game and PyTorch model.")
    parser.add_argument(
        "--stage",
        choices=("model", "rules", "mcts", "episode", "all"),
        default="model",
        help="highest smoke-test stage to run",
    )
    parser.add_argument("--num-mcts-sims", type=int, default=2)
    parser.add_argument("--episode-timeout", type=int, default=20)
    args = parser.parse_args()

    game, nnet, board = smoke_game_and_model()

    if args.stage in ("rules", "mcts", "episode", "all"):
        smoke_rules(game, board)

    if args.stage in ("mcts", "episode", "all"):
        smoke_mcts(game, nnet, board, args.num_mcts_sims)

    if args.stage in ("episode", "all"):
        smoke_episode(game, nnet, args.num_mcts_sims, args.episode_timeout)

    print("\nSmoke test finished.")


if __name__ == "__main__":
    main()
