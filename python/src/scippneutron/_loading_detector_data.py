# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2021 Scipp contributors (https://github.com/scipp)
# @author Matthew Jones

from dataclasses import dataclass, astuple
import h5py
from typing import Optional, List
import numpy as np
from ._loading_common import BadSource, ensure_not_unsigned, load_dataset
import scipp as sc
from datetime import datetime
from warnings import warn
from itertools import groupby

_detector_dimension = "detector-id"
_event_dimension = "event"


def _all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def _check_for_missing_fields(group: h5py.Group) -> str:
    error_message = ""
    required_fields = (
        "event_time_zero",
        "event_index",
        "event_id",
        "event_time_offset",
    )
    for field in required_fields:
        if field not in group:
            error_message += f"Unable to load data from NXevent_data " \
                             f"at '{group.name}' due to missing '{field}'" \
                             f" field\n"
    return error_message


def _iso8601_to_datetime(iso8601: str) -> Optional[datetime]:
    try:
        return datetime.strptime(
            iso8601.translate(str.maketrans('', '', ':-Z')),
            "%Y%m%dT%H%M%S.%f")
    except ValueError:
        # Did not understand the format of the input string
        return None


def _load_positions(detector_group: h5py.Group,
                    detector_ids_size: int) -> Optional[sc.Variable]:
    try:
        x_positions = detector_group["x_pixel_offset"][...].flatten()
        y_positions = detector_group["y_pixel_offset"][...].flatten()
    except KeyError:
        return None
    try:
        z_positions = detector_group["z_pixel_offset"][...].flatten()
    except KeyError:
        z_positions = np.zeros_like(x_positions)

    if not _all_equal((x_positions.size, y_positions.size, z_positions.size,
                       detector_ids_size)):
        warn(f"Skipped loading pixel positions as pixel offset and id "
             f"dataset sizes do not match in {detector_group.name}")
        return None

    if "depends_on" in detector_group:
        warn(f"Loaded pixel positions for "
             f"{detector_group.name.split('/')[-1]} are relative to the "
             f"detector, not sample position, as parsing transformations "
             f"is not yet implemented")

    array = np.array([x_positions, y_positions, z_positions]).T
    return sc.Variable([_detector_dimension],
                       values=array,
                       dtype=sc.dtype.vector_3_float64)


@dataclass
class DetectorData:
    events: sc.Variable
    detector_ids: sc.Variable
    pixel_positions: Optional[sc.Variable] = None


def _load_event_group(group: h5py.Group, quiet: bool) -> DetectorData:
    error_msg = _check_for_missing_fields(group)
    if error_msg:
        raise BadSource(error_msg)

    # There is some variation in the last recorded event_index in files
    # from different institutions. We try to make sure here that it is what
    # would be the first index of the next pulse.
    # In other words, ensure that event_index includes the bin edge for
    # the last pulse.
    event_id_ds = group["event_id"]
    event_index = group["event_index"][...].astype(
        ensure_not_unsigned(group["event_index"].dtype.type))
    if event_index[-1] < event_id_ds.len():
        event_index = np.append(
            event_index,
            np.array([event_id_ds.len() - 1]).astype(event_index.dtype),
        )
    else:
        event_index[-1] = event_id_ds.len()

    number_of_events = event_index[-1]
    event_time_offset = load_dataset(group["event_time_offset"],
                                     [_event_dimension])
    event_id = load_dataset(event_id_ds, [_event_dimension], dtype=np.int32)

    # Weights are not stored in NeXus, so use 1s
    weights = sc.ones(dims=[_event_dimension],
                      shape=event_id.shape,
                      dtype=np.float32)

    detector_number_ds_name = "detector_number"
    if detector_number_ds_name in group.parent:
        # Hopefully the detector ids are recorded in the file
        detector_ids = group.parent[detector_number_ds_name][...].flatten()
    else:
        # Otherwise we'll just have to bin according to whatever
        # ids we have a events for (pixels with no recorded events
        # will not have a bin)
        detector_ids = np.unique(event_id.values)

    detector_ids = sc.Variable(dims=[_detector_dimension],
                               values=detector_ids,
                               dtype=np.int32)

    data_dict = {
        "data": weights,
        "coords": {
            "tof": event_time_offset,
            _detector_dimension: event_id
        }
    }
    data = sc.detail.move_to_data_array(**data_dict)

    detector_group = group.parent
    pixel_positions = None
    if "x_pixel_offset" in detector_group:
        pixel_positions = _load_positions(detector_group,
                                          detector_ids.shape[0])

    if not quiet:
        print(f"Loaded event data from {group.name} containing "
              f"{number_of_events} events")

    return DetectorData(data, detector_ids, pixel_positions)


def load_detector_data(event_data_groups: List[h5py.Group],
                       quiet: bool) -> Optional[sc.DataArray]:
    event_data = []
    for group in event_data_groups:
        try:
            new_event_data = _load_event_group(group, quiet)
            event_data.append(new_event_data)
        except BadSource as e:
            warn(f"Skipped loading {group.name} due to:\n{e}")

    if not event_data:
        return
    else:

        def get_detector_id(detector_data: DetectorData):
            # Assume different detector banks do not have
            # intersecting ranges of detector ids
            return detector_data.detector_ids.values[0]

        event_data.sort(key=get_detector_id)

        pixel_positions_loaded = all(
            [data.pixel_positions is not None for data in event_data])
        detector_data = event_data.pop(0)
        # Events in the NeXus file are effectively binned by pulse
        # (because they are recorded chronologically)
        # but for reduction it is more useful to bin by detector id
        events = sc.bin(detector_data.events,
                        groups=[detector_data.detector_ids])
        pixel_positions = detector_data.pixel_positions
        while event_data:
            detector_data = event_data.pop(0)
            events = sc.concatenate(events,
                                    sc.bin(detector_data.events,
                                           groups=[detector_data.detector_ids
                                                   ]),
                                    dim=_detector_dimension)
            if pixel_positions_loaded:
                pixel_positions = sc.concatenate(pixel_positions,
                                                 detector_data.pixel_positions,
                                                 dim=_detector_dimension)

        if pixel_positions_loaded:
            events.coords['position'] = pixel_positions

    return events
