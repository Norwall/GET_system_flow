from __future__ import annotations

import argparse
from pathlib import Path

from co2_function_matrix import (
    DEFAULT_CLOSURES,
    MatrixConfig,
    default_worker_count,
    run_analysis,
    smoke_config,
)


OUTDIR = Path(__file__).resolve().parent / "artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the distributed CO2 functioning matrix and report artifacts.",
    )
    parser.add_argument(
        "--grid",
        choices=("wide", "smoke"),
        default="wide",
        help="Use the full planned wide grid or a tiny smoke grid.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=OUTDIR,
        help="Directory for CSV, PNG, and Markdown artifacts.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=default_worker_count(),
        help="Parallel worker count. Use 1 for a sequential run.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Limit pending cases for trial runs; omitted means all cases.",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Recompute from scratch instead of reusing existing matrix rows.",
    )
    parser.add_argument(
        "--closures",
        nargs="+",
        default=list(DEFAULT_CLOSURES),
        help="Closure models to calculate.",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip PNG generation and write only CSV/report artifacts.",
    )
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> MatrixConfig:
    if args.grid == "smoke":
        base = smoke_config()
        return MatrixConfig(
            li_values_m=base.li_values_m,
            h_values_m=base.h_values_m,
            qtr_values_w_m=base.qtr_values_w_m,
            closure_models=tuple(args.closures),
            tcon_C=base.tcon_C,
            mode=base.mode,
        )
    return MatrixConfig(closure_models=tuple(args.closures))


def main() -> None:
    args = parse_args()
    config = config_from_args(args)
    outputs = run_analysis(
        config=config,
        outdir=args.outdir,
        workers=args.workers,
        resume=not args.no_resume,
        max_cases=args.max_cases,
        make_plots=not args.no_plots,
    )
    print(f"[OK] configured cases: {config.n_cases}")
    if args.max_cases is not None:
        print(f"[OK] max pending cases this run: {args.max_cases}")
    for key, path in sorted(outputs.items()):
        print(f"[OK] {key}: {path}")


if __name__ == "__main__":
    main()
