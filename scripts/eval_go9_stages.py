import argparse
import math
import signal
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[OK] {message}")


def check_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")
    print(f"[OK] {message}: {expected!r}")


def fresh_board(n=9):
    from go9.Go9Logic import Board

    return Board(n)


def legal_set(board, color):
    return set(board.get_legal_moves(color))


def fill_board(board, color=1):
    for y in range(board.n):
        for x in range(board.n):
            board.pieces[x][y] = color


def eval_empty():
    print("\n== Stage 1: Empty Board ==")
    board = fresh_board()
    arr = np.array(board.pieces)

    check_equal(arr.shape, (9, 9), "Board(9) shape")
    check_equal(int(np.abs(arr).sum()), 0, "initial stone count")
    check(all(board.pieces[x][y] == 0 for y in range(9) for x in range(9)), "all intersections are empty")


def eval_moves():
    print("\n== Stage 2: Basic Moves ==")
    board = fresh_board()

    moves = legal_set(board, 1)
    check_equal(len(moves), 81, "empty board legal board moves")
    check((0, 0) in moves and (8, 8) in moves and (4, 4) in moves, "corners and center are legal")

    board.execute_move((4, 4), 1)
    check_equal(board.pieces[4][4], 1, "execute_move places current player's stone")
    moves_after = legal_set(board, -1)
    check((4, 4) not in moves_after, "occupied point is not legal")
    check_equal(len(moves_after), 80, "one occupied point leaves 80 legal board moves")

    fill_board(board, 1)
    check_equal(len(legal_set(board, -1)), 0, "full board has no board moves")
    check_equal(board.has_legal_moves(-1), False, "full board has no legal board moves")


def eval_groups():
    print("\n== Stage 3: Groups And Liberties ==")
    board = fresh_board()

    check_equal(set(board._neighbors(0, 0)), {(1, 0), (0, 1)}, "corner neighbors")
    check_equal(set(board._neighbors(4, 4)), {(5, 4), (3, 4), (4, 5), (4, 3)}, "center neighbors")

    board.pieces[0][0] = 1
    group = board._get_group(0, 0)
    check_equal(group, {(0, 0)}, "single corner stone group")
    check_equal(board._get_liberties(group), {(1, 0), (0, 1)}, "single corner stone liberties")

    board = fresh_board()
    board.pieces[4][4] = 1
    group = board._get_group(4, 4)
    check_equal(len(group), 1, "single center stone group size")
    check_equal(len(board._get_liberties(group)), 4, "single center stone liberty count")

    board.pieces[4][5] = 1
    group = board._get_group(4, 4)
    check_equal(group, {(4, 4), (4, 5)}, "two connected vertical stones group")
    check_equal(len(board._get_liberties(group)), 6, "two connected stones liberty count")

    board.pieces[5][5] = -1
    check_equal(board._get_group(5, 5), {(5, 5)}, "opponent stone is separate group")


def eval_capture():
    print("\n== Stage 4: Capture ==")
    board = fresh_board()

    board.pieces[1][1] = 1
    board.pieces[0][1] = -1
    board.pieces[1][0] = -1
    board.pieces[2][1] = -1
    board.execute_move((1, 2), -1)
    check_equal(board.pieces[1][1], 0, "single surrounded stone is captured")
    check_equal(board.pieces[1][2], -1, "capturing stone is placed")

    board = fresh_board()
    board.pieces[1][1] = 1
    board.pieces[1][2] = 1
    for move in [(0, 1), (0, 2), (1, 0), (2, 1), (2, 2)]:
        board.pieces[move[0]][move[1]] = -1
    board.execute_move((1, 3), -1)
    check_equal(board.pieces[1][1], 0, "captured group first stone removed")
    check_equal(board.pieces[1][2], 0, "captured group second stone removed")


def eval_suicide():
    print("\n== Stage 5: Suicide Rule ==")
    board = fresh_board()

    board.pieces[0][1] = -1
    board.pieces[1][0] = -1
    moves = legal_set(board, 1)
    check((0, 0) not in moves, "pure suicide corner move is illegal")

    board = fresh_board()
    board.pieces[0][1] = -1
    board.pieces[1][0] = -1
    board.pieces[1][1] = 1
    board.pieces[2][0] = 1
    moves = legal_set(board, 1)
    check((0, 0) in moves, "capture-that-saves-self is legal")
    board.execute_move((0, 0), 1)
    check_equal(board.pieces[1][0], 0, "captured adjacent opponent stone at (1, 0) removed after saving move")


def eval_game():
    print("\n== Stage 6: Game Interface ==")
    from go9.Go9Game import Go9Game

    game = Go9Game(9)
    board = game.getInitBoard()
    valids = game.getValidMoves(board, 1)

    check_equal(board.shape, (9, 9), "initial game board shape")
    check_equal(valids.shape, (82,), "valid move vector shape")
    check_equal(int(valids[-1]), 1, "pass action is valid")
    check(np.all((valids == 0) | (valids == 1)), "valid move vector is binary")

    next_board, next_player = game.getNextState(board, 1, 0)
    check_equal(next_board.shape, (9, 9), "next board shape")
    check_equal(next_player, -1, "next player flips")
    check_equal(next_board[0][0], 1, "action 0 places at board coordinate (0, 0)")

    pi = np.ones(game.getActionSize(), dtype=np.float64) / game.getActionSize()
    syms = game.getSymmetries(board, pi)
    check_equal(len(syms), 8, "symmetry count")
    for sym_board, sym_pi in syms:
        check_equal(sym_board.shape, (9, 9), "symmetry board shape")
        check_equal(len(sym_pi), 82, "symmetry policy length")
        check_equal(sym_pi[-1], pi[-1], "pass probability is unchanged by symmetry")


def eval_model():
    print("\n== Stage 7: Model Smoke ==")
    from go9.Go9Game import Go9Game
    from go9.pytorch.NNet import NNetWrapper

    game = Go9Game(9)
    nnet = NNetWrapper(game)
    board = game.getCanonicalForm(game.getInitBoard(), 1)
    pi, value = nnet.predict(board)

    check_equal(pi.shape, (82,), "policy shape")
    check(math.isclose(float(pi.sum()), 1.0, rel_tol=1e-5, abs_tol=1e-5), f"policy sums to 1, got {pi.sum()}")
    scalar_value = float(np.asarray(value).reshape(-1)[0])
    check(-1.0001 <= scalar_value <= 1.0001, f"value is in [-1, 1], got {scalar_value}")


def eval_mcts():
    print("\n== Stage 8: MCTS Smoke ==")
    from MCTS import MCTS
    from go9.Go9Game import Go9Game
    from go9.pytorch.NNet import NNetWrapper
    from utils import dotdict

    game = Go9Game(9)
    nnet = NNetWrapper(game)
    mcts = MCTS(game, nnet, dotdict({"numMCTSSims": 2, "cpuct": 1}))
    board = game.getCanonicalForm(game.getInitBoard(), 1)
    pi = mcts.getActionProb(board, temp=1)

    check_equal(len(pi), 82, "MCTS policy length")
    check(math.isclose(float(sum(pi)), 1.0, rel_tol=1e-5, abs_tol=1e-5), f"MCTS policy sums to 1, got {sum(pi)}")


def eval_terminal():
    print("\n== Stage 9: Terminal Safety ==")
    from go9.Go9Game import Go9Game

    game = Go9Game(9)
    board = game.getInitBoard()
    check_equal(game.getGameEnded(board, 1), 0, "empty board is not terminal")

    full = np.ones((9, 9), dtype=int)
    full[0][0] = -1
    result_for_black = game.getGameEnded(full, 1)
    result_for_white = game.getGameEnded(full, -1)
    check(result_for_black != 0, f"full board is terminal for player 1, got {result_for_black}")
    check(result_for_white != 0, f"full board is terminal for player -1, got {result_for_white}")
    check_equal(result_for_black, -result_for_white, "terminal result changes sign by player perspective")


def eval_scoring():
    print("\n== Stage 10: Scoring ==")
    from go9.Go9Game import Go9Game

    game = Go9Game(9)

    board = np.zeros((9, 9), dtype=int)
    board[0][0] = 1
    board[1][0] = 1
    board[8][8] = -1
    check(game.getScore(board, 1) > 0, "player with more stones has positive score")
    check(game.getScore(board, -1) < 0, "opponent perspective has negative score")

    territory = np.zeros((9, 9), dtype=int)
    territory[0][1] = 1
    territory[1][0] = 1
    territory[1][2] = 1
    territory[2][1] = 1
    check(game.getScore(territory, 1) >= 5, "surrounded point counts as player 1 area")

    neutral = np.zeros((9, 9), dtype=int)
    neutral[0][1] = 1
    neutral[1][0] = -1
    check_equal(game.getScore(neutral, 1), 0, "neutral/shared empty area is not counted")


def tiny_args(checkpoint="./temp/go9_eval/"):
    from utils import dotdict

    return dotdict(
        {
            "numIters": 1,
            "numEps": 1,
            "tempThreshold": 15,
            "updateThreshold": 0.6,
            "maxlenOfQueue": 200000,
            "numMCTSSims": 2,
            "arenaCompare": 2,
            "cpuct": 1,
            "checkpoint": checkpoint,
            "load_model": False,
            "load_folder_file": (checkpoint, "best.pth.tar"),
            "numItersForTrainExamplesHistory": 20,
        }
    )


def run_with_timeout(timeout_seconds, fn):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"operation timed out after {timeout_seconds}s")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        return fn()
    finally:
        signal.alarm(0)


def eval_episode():
    print("\n== Stage 11: Episode Smoke ==")
    from Coach import Coach
    from go9.Go9Game import Go9Game
    from go9.pytorch.NNet import NNetWrapper

    game = Go9Game(9)
    nnet = NNetWrapper(game)
    coach = Coach(game, nnet, tiny_args())
    examples = run_with_timeout(30, coach.executeEpisode)

    check(len(examples) > 0, f"episode produced examples, got {len(examples)}")
    board, pi, value = examples[0]
    check_equal(board.shape, (9, 9), "example board shape")
    check_equal(len(pi), 82, "example policy length")
    check(-1.0001 <= float(value) <= 1.0001, f"example value is in [-1, 1], got {value}")


def eval_tiny_train():
    print("\n== Stage 12: Tiny Training Smoke ==")
    from Coach import Coach
    from go9.Go9Game import Go9Game
    from go9.pytorch.NNet import NNetWrapper

    game = Go9Game(9)
    nnet = NNetWrapper(game)
    coach = Coach(game, nnet, tiny_args())
    run_with_timeout(90, coach.learn)
    checkpoint_dir = ROOT / "temp" / "go9_eval"
    check(checkpoint_dir.exists(), "tiny training checkpoint directory exists")
    check(any(checkpoint_dir.iterdir()), "tiny training checkpoint directory is not empty")


STAGES = {
    "empty": eval_empty,
    "moves": eval_moves,
    "groups": eval_groups,
    "capture": eval_capture,
    "suicide": eval_suicide,
    "game": eval_game,
    "model": eval_model,
    "mcts": eval_mcts,
    "terminal": eval_terminal,
    "scoring": eval_scoring,
    "episode": eval_episode,
    "tiny-train": eval_tiny_train,
}

ORDER = [
    "empty",
    "moves",
    "groups",
    "capture",
    "suicide",
    "game",
    "model",
    "mcts",
    "terminal",
    "scoring",
    "episode",
    "tiny-train",
]


def main():
    parser = argparse.ArgumentParser(description="Assignment-style staged evals for go9.")
    parser.add_argument("--stage", choices=ORDER + ["all"], default="empty")
    args = parser.parse_args()

    stages = ORDER if args.stage == "all" else [args.stage]
    for stage in stages:
        STAGES[stage]()

    print("\nEval finished.")


if __name__ == "__main__":
    main()
