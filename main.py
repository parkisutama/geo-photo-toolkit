# src/main.py
from typing import Optional

import typer
from typing_extensions import Annotated

from src.utils.logging import setup_logger
from src.workflows.gps_extraction import run_gps_extraction_workflow
from src.workflows.kmz_generation import run_kmz_generation_workflow

app = typer.Typer(
    name="Geo Photo Toolkit",
    help="A CLI for processing geotagged photos and creating map files.",
    add_completion=False,
)


# --- Common callback to setup logging for all commands ---
@app.callback()
def main(
    ctx: typer.Context,
    log_dir: Annotated[
        str, typer.Option(help="Directory to store the log file.")
    ] = "logs",
):
    ctx.obj = setup_logger(log_dir)


# --- GPS Extraction Command ---
@app.command(name="gps-extract")
def gps_extract_command(
    ctx: typer.Context,
    input_dir: Annotated[
        str,
        typer.Option("--input-dir", "-i", help="Directory containing the image files."),
    ],
    output_file: Annotated[
        str,
        typer.Option(
            "--output-file", "-o", help="Path for the output file (.csv or .xlsx)."
        ),
    ],
    config_path: Annotated[
        Optional[str],
        typer.Option("--config", "-c", help="Path to a TOML config file."),
    ] = None,
    include_full_path: Annotated[
        bool,
        typer.Option(
            "--include-full-path", help="Include the full, absolute path to each image."
        ),
    ] = False,
):
    """Extracts EXIF metadata from images based on a configuration file."""
    logger = ctx.obj
    logger.info("Invoking GPS Extraction command.")
    run_gps_extraction_workflow(input_dir, output_file, include_full_path, config_path)


# --- KMZ Generation Command ---
@app.command(name="kmz-generate")
def kmz_generate_command(
    ctx: typer.Context,
    input_file: Annotated[
        str, typer.Option("--input-file", "-f", help="Input data file (.csv or .xlsx).")
    ],
    output_dir: Annotated[
        str, typer.Option("--output-dir", "-d", help="Directory to save the KMZ file.")
    ],
    config_path: Annotated[
        Optional[str],
        typer.Option(
            "--config",
            "-c",
            help="Path to a TOML config file for description formatting.",
        ),
    ] = None,
):
    """Generates a KMZ file from a CSV or Excel file."""
    logger = ctx.obj
    logger.info("Invoking KMZ Generation command.")
    run_kmz_generation_workflow(input_file, output_dir, config_path)


if __name__ == "__main__":
    app()
