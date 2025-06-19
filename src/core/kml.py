# src/core/kml.py
import logging
import os
import zipfile

import pandas as pd
import simplekml

logger = logging.getLogger("GeoPhotoToolkitLogger")


def create_kml_file(
    df: pd.DataFrame,
    folder_name: str,
    output_kml_path: str,
    description_template: str | None,
) -> None:
    """
    Creates a KML file from a DataFrame, using a template for the description.
    """
    kml = simplekml.Kml(name=folder_name)
    folder = kml.newfolder(name=folder_name)

    # Use 'photo_path' for local files from gps-extract, fallback to 'local_photo_path' for downloaded files
    photo_col = "photo_path" if "photo_path" in df.columns else "local_photo_path"
    icon_col = "icon_url" if "icon_url" in df.columns else "local_icon_path"

    for _, row in df.iterrows():
        try:
            # Format the description using the template
            if description_template:
                description = description_template.format(**row.to_dict())
            else:
                description = row.get("description", "")

            point = folder.newpoint(
                name=row.get("name", ""),
                description=description,
                coords=[
                    (row["longitude"], row["latitude"])
                ],  # Assumes lon/lat columns exist
            )

            # Add photo if a local path is provided
            if photo_col in df.columns and pd.notna(row.get(photo_col)):
                photo_filename = os.path.basename(row[photo_col])
                point.description += (
                    f"<br/><img width='480' src='files/{photo_filename}'/>"
                )
                point.extendeddata.newdata(
                    name="photo", value=f"files/{photo_filename}"
                )

            # Add custom icon if a local path is provided
            if icon_col in df.columns and pd.notna(row.get(icon_col)):
                icon_filename = os.path.basename(row[icon_col])
                point.style.iconstyle.icon.href = f"files/{icon_filename}"

        except (KeyError, ValueError) as e:
            logger.warning(
                f"Skipping row due to missing required column or formatting error: {e} - Row: {row.get('name')}"
            )
            continue

    kml.save(output_kml_path)
    logger.info(f"KML file created at: {output_kml_path}")


def create_kmz_archive(
    kml_path: str, df_with_paths: pd.DataFrame, output_kmz_path: str
) -> None:
    # ... (This function does not need to change)
    with zipfile.ZipFile(output_kmz_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(kml_path, arcname="doc.kml")
        media_files_folder = "files"
        media_columns = [
            "photo_path",
            "local_photo_path",
            "icon_url",
            "local_icon_path",
        ]
        for col in media_columns:
            if col in df_with_paths:
                for file_path in df_with_paths[col].dropna().unique():
                    if os.path.exists(file_path):
                        arcname = os.path.join(
                            media_files_folder, os.path.basename(file_path)
                        )
                        zipf.write(file_path, arcname=arcname)
                    else:
                        if not str(file_path).startswith(("http", "https")):
                            logger.warning(
                                f"Media file not found, will not be included in KMZ: {file_path}"
                            )
    os.remove(kml_path)
    logger.info(f"KMZ archive created and KML file removed. Output: {output_kmz_path}")
