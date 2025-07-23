# main.py
from typing import Optional

import typer
from typing_extensions import Annotated

from src.config import OCREngine
from src.utils.logging import setup_logging
from src.workflows.gps_extraction import run_gps_extraction_workflow
from src.workflows.kmz_generation import run_kmz_generation_workflow

# --- Setup Typer App and Logging ---
app = typer.Typer(
    help="Geo Photo Toolkit: A tool for extracting, processing, and visualizing geospatial photo data."
)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose (DEBUG level) logging."
    ),
):
    """
    Main callback to set up shared resources like the logger.
    """
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)
    ctx.obj = logger


# --- GPS Extraction Command ---
@app.command(name="gps-extract")
def gps_extract_command(
    ctx: typer.Context,
    input_dir: Annotated[
        str,
        typer.Option("--input-dir", "-i", help="Input directory containing photos."),
    ],
    output_file: Annotated[
        str,
        typer.Option("--output-file", "-o", help="Output file path (.csv or .xlsx)."),
    ],
    # --- NEW OPTION ---
    ocr_disabled: Annotated[
        bool,
        typer.Option(
            "--ocr-disabled",
            help="Run in EXIF-only mode, completely disabling the OCR fallback.",
            is_flag=True,
        ),
    ] = False,
    # --- END OF NEW OPTION ---
    ocr_engine: Annotated[
        OCREngine,
        typer.Option(
            "--ocr-engine",
            help="The primary OCR engine to use (if OCR is not disabled).",
            case_sensitive=False,
        ),
    ] = OCREngine.EASYOCR,
    gcv_fallback: Annotated[
        bool,
        typer.Option(
            "--gcv-fallback",
            help="If using EasyOCR, fallback to Google Vision if it fails.",
            is_flag=True,
        ),
    ] = False,
    gcv_limit: Annotated[
        int,
        typer.Option(
            "--gcv-limit",
            help="Limit the number of images sent to Google Vision API to control costs.",
        ),
    ] = -1,
    no_ocr_on_invalid_gps: Annotated[
        bool,
        typer.Option(
            "--no-ocr-on-invalid-gps",
            help="Disable OCR fallback if EXIF GPS data is present but invalid/corrupt.",
            is_flag=True,
        ),
    ] = False,
    include_full_path: Annotated[
        bool, typer.Option(help="Include the full photo path in the output.")
    ] = True,
    config_path: Annotated[
        Optional[str], typer.Option(help="Path to a custom config.toml file.")
    ] = None,
):
    """
    Extracts EXIF metadata from images, with powerful, configurable OCR fallback.
    """
    logger = ctx.obj
    logger.info("Invoking GPS Extraction command.")
    run_gps_extraction_workflow(
        input_dir=input_dir,
        output_file=output_file,
        include_full_path=include_full_path,
        config_path=config_path,
        ocr_disabled=ocr_disabled,
        ocr_engine=ocr_engine,
        gcv_fallback=gcv_fallback,
        gcv_limit=gcv_limit,
        no_ocr_on_invalid_gps=no_ocr_on_invalid_gps,
    )


# --- KMZ Generation Command ---
@app.command(name="kmz-generate")
def kmz_generate_command(
    ctx: typer.Context,
    input_file: Annotated[
        str,
        typer.Option(
            "--input-file", "-i", help="Input CSV or Excel file with GPS data."
        ),
    ],
    output_file: Annotated[
        str, typer.Option("--output-file", "-o", help="Output KMZ file path.")
    ],
    config_path: Annotated[
        Optional[str], typer.Option(help="Path to a custom config.toml file.")
    ] = None,
):
    """Generates a KMZ file from a CSV or Excel file."""
    logger = ctx.obj
    logger.info("Invoking KMZ Generation command.")
    run_kmz_generation_workflow(
        input_file=input_file, output_file=output_file, config_path=config_path
    )


if __name__ == "__main__":
    app()
