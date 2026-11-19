# Sentinel Chess

A chess variant built with pygame. Each side gets two **Sentinels** (`S`) in place of the d- and e-pawns:

- A Sentinel steps one square in any direction, or two squares forward from its starting rank. It can also capture en passant.
- A piece standing next to a friendly Sentinel can't be captured by anything, including en passant. Pawns can't capture Sentinels at all.
- A Sentinel next to the enemy king gives check.

Everything else follows standard chess: castling, en passant, promotion to any piece, and draws by stalemate, threefold repetition, the 50-move rule (Sentinel moves reset the count, like pawn moves) and insufficient material.

## Setup

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # creates .venv and installs pygame-ce + pyyaml
uv run python src/ChessMain.py   # play
uv run pytest                    # rules, move generation and AI tests
```

Settings such as colours, human/AI players, the starting FEN and AI depth live in `src/config.yaml`.

## Engine

`src/ChessAI.py` (`version: "v4"`) uses these standard techniques:

- [Negamax](https://www.chessprogramming.org/Negamax) with [alpha-beta pruning](https://www.chessprogramming.org/Alpha-Beta)
- [Iterative deepening](https://www.chessprogramming.org/Iterative_Deepening)
- [Transposition table](https://www.chessprogramming.org/Transposition_Table) with exact/lower/upper bound entries, keyed by [Zobrist hashing](https://www.chessprogramming.org/Zobrist_Hashing)
- [Move ordering](https://www.chessprogramming.org/Move_Ordering): hash move first, then [MVV-LVA](https://www.chessprogramming.org/MVV-LVA) captures
- [Mate scores](https://www.chessprogramming.org/Mate_Scores) adjusted by distance, so faster mates are preferred
- [Piece-square tables](https://www.chessprogramming.org/Simplified_Evaluation_Function) for evaluation

Move generation is checked with [perft](https://www.chessprogramming.org/Perft) counts and seeded random-game snapshots (`tests/movegen_harness.py`). Regenerate the snapshot only after an intentional rules change.
