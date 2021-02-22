// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (c) 2021 Scipp contributors (https://github.com/scipp)
/// @file
/// @author Simon Heybrock
#include "scipp/neutron/beamline.h"
#include "scipp/neutron/convert.h"

#include "pybind11.h"

using namespace scipp;
using namespace scipp::neutron;

namespace py = pybind11;

template <class T> void bind_positions(py::module &m) {
  m.def("position", py::overload_cast<T>(position), R"(
    Extract the detector pixel positions from a data array or a dataset.

    :return: A variable containing the detector pixel positions.
    :rtype: Variable)");

  m.def("source_position", py::overload_cast<T>(source_position), R"(
    Extract the neutron source position from a data array or a dataset.

    :return: A scalar variable containing the source position.
    :rtype: Variable)");

  m.def("sample_position", py::overload_cast<T>(sample_position), R"(
    Extract the sample position from a data array or a dataset.

    :return: A scalar variable containing the sample position.
    :rtype: Variable)");
}

template <class T> void bind_beamline(py::module &m) {
  using ConstView = const typename T::const_view_type &;
  using View = const typename T::view_type &;

  bind_positions<View>(m);
  bind_positions<ConstView>(m);

  m.def("flight_path_length", py::overload_cast<ConstView>(flight_path_length),
        R"(
    Compute the length of the total flight path from a data array or a dataset.

    If a sample position is found this is the sum of `l1` and `l2`, otherwise the distance from the source.

    :return: A scalar variable containing the total length of the flight path.
    :rtype: Variable)");

  m.def("l1", py::overload_cast<ConstView>(l1), R"(
    Compute L1, the length of the primary flight path (distance between neutron source and sample) from a data array or a dataset.

    :return: A scalar variable containing L1.
    :rtype: Variable)");

  m.def("l2", py::overload_cast<ConstView>(l2), R"(
    Compute L2, the length of the secondary flight paths (distances between sample and detector pixels) from a data array or a dataset.

    :return: A variable containing L2 for all detector pixels.
    :rtype: Variable)");

  m.def("scattering_angle", py::overload_cast<ConstView>(scattering_angle), R"(
    Compute :math:`\theta`, the scattering angle in Bragg's law, from a data array or a dataset.

    :return: A variable containing :math:`\theta` for all detector pixels.
    :rtype: Variable)");

  m.def("two_theta", py::overload_cast<ConstView>(two_theta), R"(
    Compute :math:`2\theta`, twice the scattering angle in Bragg's law, from a data array or a dataset.

    :return: A variable containing :math:`2\theta` for all detector pixels.
    :rtype: Variable)");
}

template <class T> void bind_convert(py::module &m) {
  using ConstView = const typename T::const_view_type &;
  const char *doc = R"(
    Convert dimension (unit) into another.

    Currently only conversion from time-of-flight (Dim.Tof) to other time-of-flight-derived units such as d-spacing (Dim.DSpacing) is supported.

    :param data: Input data with time-of-flight dimension (Dim.Tof)
    :param origin: Dimension to convert from
    :param target: Dimension to convert into
    :param out: Optional output container
    :return: New data array or dataset with converted dimension (dimension labels, coordinate values, and units)
    :rtype: DataArray or Dataset)";
  m.def(
      "convert",
      [](ConstView data, const Dim origin, const Dim target) {
        return py::cast(convert(data, origin, target));
      },
      py::arg("data"), py::arg("origin"), py::arg("target"),
      py::call_guard<py::gil_scoped_release>(), doc);
  m.def(
      "convert",
      [](py::object &obj, const Dim origin, const Dim target, T &out) {
        auto &data = obj.cast<T &>();
        if (&data != &out)
          throw std::runtime_error("Currently only out=<input> is supported");
        data = convert(std::move(data), origin, target);
        return obj;
      },
      py::arg("data"), py::arg("origin"), py::arg("target"), py::arg("out"),
      py::call_guard<py::gil_scoped_release>(), doc);
}

void init_neutron(py::module &m) {
  bind_convert<dataset::DataArray>(m);
  bind_convert<dataset::Dataset>(m);
  bind_beamline<dataset::DataArray>(m);
  bind_beamline<dataset::Dataset>(m);
}