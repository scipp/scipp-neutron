// SPDX-License-Identifier: BSD-3-Clause
// Copyright (c) 2021 Scipp contributors (https://github.com/scipp)
/// @file
/// @author Simon Heybrock
#pragma once

#include <scipp/dataset/dataset.h>
#include <scipp/units/unit.h>

#include "scippneutron_export.h"

namespace scipp::neutron {

enum class ConvertMode { Scatter, NoScatter };

namespace NeutronDim {
SCIPPNEUTRON_EXPORT extern Dim DSpacing;
SCIPPNEUTRON_EXPORT extern Dim Energy;
SCIPPNEUTRON_EXPORT extern Dim EnergyTransfer;
SCIPPNEUTRON_EXPORT extern Dim FinalEnergy;
SCIPPNEUTRON_EXPORT extern Dim IncidentBeam;
SCIPPNEUTRON_EXPORT extern Dim IncidentEnergy;
SCIPPNEUTRON_EXPORT extern Dim L1;
SCIPPNEUTRON_EXPORT extern Dim L2;
SCIPPNEUTRON_EXPORT extern Dim Ltotal;
SCIPPNEUTRON_EXPORT extern Dim Position;
SCIPPNEUTRON_EXPORT extern Dim Q;
SCIPPNEUTRON_EXPORT extern Dim Qx;
SCIPPNEUTRON_EXPORT extern Dim Qy;
SCIPPNEUTRON_EXPORT extern Dim Qz;
SCIPPNEUTRON_EXPORT extern Dim SamplePosition;
SCIPPNEUTRON_EXPORT extern Dim ScatteredBeam;
SCIPPNEUTRON_EXPORT extern Dim SourcePosition;
SCIPPNEUTRON_EXPORT extern Dim Spectrum;
SCIPPNEUTRON_EXPORT extern Dim Tof;
SCIPPNEUTRON_EXPORT extern Dim TwoTheta;
SCIPPNEUTRON_EXPORT extern Dim Wavelength;
} // namespace NeutronDim

SCIPPNEUTRON_EXPORT Variable position(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable source_position(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable sample_position(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable Ltotal(const dataset::Coords &meta,
                                    const ConvertMode scatter);
SCIPPNEUTRON_EXPORT Variable L1(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable L2(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable scattering_angle(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable cos_two_theta(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable two_theta(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable incident_energy(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable final_energy(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable incident_beam(const dataset::Coords &meta);
SCIPPNEUTRON_EXPORT Variable scattered_beam(const dataset::Coords &meta);

} // namespace scipp::neutron
