"""rio_stac.scripts.cli."""

import json

import click
import rasterio
from pystac import MediaType
from pystac.utils import datetime_to_str, str_to_datetime
from rasterio.rio import options

from rio_stac import create_stac_item


def _cb_key_val(ctx, param, value):
    if not value:
        return {}
    else:
        out = {}
        for pair in value:
            if "=" not in pair:
                raise click.BadParameter(
                    "Invalid syntax for KEY=VAL arg: {}".format(pair)
                )
            else:
                k, v = pair.split("=", 1)
                out[k] = v
        return out


@click.command()
# @options.file_in_arg
@click.argument(
    "inputs",
    nargs=-1
)
@click.option(
    "--datetime",
    "-d",
    "input_datetime",
    type=str,
    help="The date and time of the assets, in UTC (e.g 2020-01-01, 2020-01-01T01:01:01).",
)
@click.option(
    "--extension",
    "-e",
    type=str,
    multiple=True,
    help="STAC extension URL the Item implements.",
)
@click.option(
    "--collection", "-c", type=str, help="The Collection ID that this item belongs to."
)
@click.option("--collection-url", type=str, help="Link to the STAC Collection.")
@click.option(
    "--property",
    "-p",
    metavar="NAME=VALUE",
    multiple=True,
    callback=_cb_key_val,
    help="Additional property to add.",
)
@click.option("--id", type=str, help="Item id.")
@click.option(
    "--asset-names",
    "-n",
    type=str,
    default=["asset"],
    help="The asset names. A comma separated list. The list must be ordered based on the file paths provided.",
    show_default=True,
)
@click.option(
    "--asset-hrefs",
    type=str,
    help="Overwrite asset hrefs. A comma separated list. The list must be ordered based on the file paths provided.",
)
@click.option(
    "--asset-mediatype",
    type=click.Choice([it.name for it in MediaType] + ["auto"]),
    help="Asset media-type.",
)
@click.option(
    "--with-proj/--without-proj",
    default=True,
    help="Add the 'projection' extension and properties.",
    show_default=True,
)
@click.option(
    "--with-raster/--without-raster",
    default=True,
    help="Add the 'raster' extension and properties.",
    show_default=True,
)
@click.option(
    "--with-eo/--without-eo",
    default=True,
    help="Add the 'eo' extension and properties.",
    show_default=True,
)
@click.option("--output", "-o", type=click.Path(exists=False), help="Output file name")
@click.option(
    "--config",
    "config",
    metavar="NAME=VALUE",
    multiple=True,
    callback=options._cb_key_val,
    help="GDAL configuration options.",
)
def stac(
    inputs,
    input_datetime,
    extension,
    collection,
    collection_url,
    property,
    id,
    asset_names,
    asset_hrefs,
    asset_mediatype,
    with_proj,
    with_raster,
    with_eo,
    output,
    config,
):
    """Rasterio STAC plugin: Create a STAC Item for raster dataset."""
    property = property or {}

    asset_names = asset_names.split(",") if asset_names else []
    if len(inputs) < len(asset_names):
        raise Exception("asset_names if specified map to items in 1:1 way")
    asset_hrefs = asset_hrefs.split(",") if asset_hrefs else []
    if len(inputs) < len(asset_hrefs):
        raise Exception("asset_hrefs if specified map to items in 1:1 way")

    if input_datetime:
        if "/" in input_datetime:
            start_datetime, end_datetime = input_datetime.split("/")
            property["start_datetime"] = datetime_to_str(
                str_to_datetime(start_datetime)
            )
            property["end_datetime"] = datetime_to_str(str_to_datetime(end_datetime))
            input_datetime = None
        else:
            input_datetime = str_to_datetime(input_datetime)

    if asset_mediatype and asset_mediatype != "auto":
        asset_mediatype = MediaType[asset_mediatype]

    extensions = [e for e in extension if e]

    with rasterio.Env(**config):
        item = create_stac_item(
            inputs,
            input_datetime=input_datetime,
            extensions=extensions,
            collection=collection,
            collection_url=collection_url,
            properties=property,
            id=id,
            asset_names=asset_names,
            asset_hrefs=asset_hrefs,
            asset_media_type=asset_mediatype,
            with_proj=with_proj,
            with_raster=with_raster,
            with_eo=with_eo,
        )

    if output:
        with open(output, "w") as f:
            f.write(json.dumps(item.to_dict(), separators=(",", ":")))
    else:
        click.echo(json.dumps(item.to_dict(), separators=(",", ":")))
