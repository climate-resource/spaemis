"""
Point source scaler

Split a timeseries of emissions across a number of points

"""
import logging
import os
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import scmdata
import xarray as xr
from attrs import define

from spaemis.config import PointSourceMethod
from spaemis.constants import RAW_DATA_DIR
from spaemis.inventory import EmissionsInventory
from spaemis.utils import clip_region

from .base import BaseScaler
from .timeseries import apply_amount, get_timeseries

logger = logging.getLogger(__name__)


@define
class Point:
    lat: float
    lon: float


@define
class PointSourceScaler(BaseScaler):
    """
    Split emissions across some point sources
    """

    point_sources: List[Point]
    source_timeseries: str
    source_filters: List[Dict[str, Any]]

    def __call__(
        self,
        *,
        data: xr.DataArray,
        inventory: EmissionsInventory,
        target_year: int,
        timeseries: Dict[str, scmdata.ScmRun],
        **kwargs,
    ) -> xr.DataArray:
        """
        Apply scaling

        Parameters
        ----------
        data
            Timeseries to scale
        inventory
        timeseries
            Timeseries data used by the proxy
        kwargs

        Returns
        -------
        Scaled data
        """
        ts = get_timeseries(
            timeseries,
            self.source_timeseries,
            self.source_filters,
            target_year=target_year,
        )

        scaled = data.copy()
        scaled[:, :] = 0
        scaled = clip_region(scaled, inventory.border_mask)
        print(scaled)

        num_points = len(self.point_sources)
        num_valid_points = 0
        d_lat = scaled.lat[1] - scaled.lat[0]
        for source in self.point_sources:
            try:
                field_location = scaled.sel(
                    lat=source.lat,
                    lon=source.lon,
                    method="nearest",
                    tolerance=np.abs(d_lat.values),
                )

                scaled.loc[field_location.lat, field_location.lon] += 1
                num_valid_points += 1
            except KeyError:
                # Value not in domain
                pass

        if num_valid_points == 0:
            raise ValueError("No point sources are present in domain")
        portion_in_domain = scaled.sum().values.squeeze() / num_points
        logger.info(
            f"{scaled.sum().values.squeeze()} / {num_points} points sources are in domain. {num_valid_points}"
        )

        amount = ts.values.squeeze() * portion_in_domain
        unit = ts.get_unique_meta("unit", True)
        return apply_amount(amount, unit, scaled)

    @classmethod
    def create_from_config(cls, method: PointSourceMethod) -> "PointSourceScaler":
        point_info = pd.read_csv(
            os.path.join(RAW_DATA_DIR, "configuration", method.point_sources)
        )
        points = [
            Point(lat=item["lat"], lon=item["lon"])
            for item in point_info.to_dict("records")
        ]

        return PointSourceScaler(
            point_sources=points,
            source_timeseries=method.source_timeseries,
            source_filters=method.source_filters,
        )
