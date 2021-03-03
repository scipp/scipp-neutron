from ..mantid_data_helper import MantidDataHelper
import scipp as sc
import scippneutron.mantid as mantid
import time
from abc import ABC, abstractmethod
import numpy as np


class MantidScippComparison(ABC):
    def __init__(self, test_description=None):
        self._test_description = test_description

    def _execute_with_timing(self, op, input):
        start = time.time()
        result = op(input)
        stop = time.time()
        return result, (stop - start) * sc.Unit('s')

    def _fuzzy_compare(self, a, b, tol):
        same_data = sc.all(sc.is_approx(a.data, b.data, tol)).value

        if not len(a.meta) == len(b.meta):
            for k, v in a.meta.items():
                print(k)
            for k, v in b.meta.items():
                print(k)
            print('different length')
            return False
        for key, val in a.meta.items():
            if a.meta[key].shape != b.meta[key].shape:
                print('DIFFERENT META for', key, a.meta[key].shape,
                      b.meta[key].shape)
                return False
            if val.dtype == sc.dtype.vector_3_float64:
                continue
            if val.dtype not in [sc.dtype.float64, sc.dtype.float32]:
                continue
            vtol = np.abs(a.meta[key].values * 1e-9) + 1e-9
            print(key)
            print(vtol.shape, a.meta[key].values.shape,
                  b.meta[key].values.shape)
            x = a.meta[key].values
            y = b.meta[key].values
            atol = vtol
            rtol = 0
            np.less_equal(abs(x - y), atol + rtol * abs(y))
            print('a is finite', np.sum(np.isposinf(a.meta[key].values)))
            print('b is finite', np.sum(np.isposinf(b.meta[key].values)))
            if not np.all(
                    np.isclose(
                        a.meta[key].values, b.meta[key].values, atol=vtol)):
                print(key)
                print(a.meta[key].shape)
                print(b.meta[key].shape)
                print(a.meta[key])
                print(b.meta[key])
                diff = (a.meta[key] - b.meta[key]).values.ravel()
                imax = np.argmax(diff)
                print(np.max(diff), np.argmax(diff))
                print(a.meta[key].values.ravel()[imax])
                print(b.meta[key].values.ravel()[imax])
                print(vtol)
                print(np.max(vtol), np.min(vtol), np.argmax(vtol))
                return False
        print('Coord match')
        print(same_data)
        return same_data

    def _assert(self, a, b, allow_failure):
        try:
            if isinstance(a, sc.DataArray):
                tol = 1e-2 * a.data.unit + 1e-2 * sc.abs(a.data)
                assert self._fuzzy_compare(a, b, tol)
            else:
                tol = 1e-2 * a.unit + 1e-2 * sc.abs(a)
                assert sc.all(sc.is_approx(a, b, tol)).value
        except AssertionError as ae:
            if allow_failure:
                print(ae)
            else:
                raise (ae)

    def _run_from_workspace(self, in_ws, allow_failure):
        out_mantid, time_mantid = self._execute_with_timing(self._run_mantid,
                                                            input=in_ws)
        in_da = mantid.from_mantid(in_ws)
        if in_da.data.bins is not None:
            in_da = in_da.astype(
                sc.dtype.float64)  # Converters set weights float32
        out_scipp, time_scipp = self._execute_with_timing(self._run_scipp,
                                                          input=in_da)

        self._assert(out_scipp, out_mantid, allow_failure)

        return {'scipp': out_scipp, 'mantid': out_mantid}

    def _append_result(self, name, result, results):
        results[f'with_{name}' if self._test_description is None else
                f'{self._test_description}_with_{name}'] = result

    def run(self, allow_failure=False):
        import mantid.simpleapi as sapi
        results = {}
        if self._filenames == {} and self._workspaces == {}:
            raise RuntimeError(
                'No _files or _workspaces provided for testing ')
        for name, (hash, algorithm) in self._filenames.items():
            file = MantidDataHelper.find_file(hash, algorithm)
            print('Loading', name)
            in_ws = sapi.Load(Filename=file, StoreInADS=False)
            result = self._run_from_workspace(in_ws, allow_failure)
            self._append_result(name, result, results)
        for name, in_ws in self._workspaces.items():
            result = self._run_from_workspace(in_ws, allow_failure)
            self._append_result(name, result, results)

        return results

    @property
    def _filenames(self):
        return {}

    @property
    def _workspaces(self):
        return {}

    @abstractmethod
    def _run_mantid(self, in_ws):
        pass

    @abstractmethod
    def _run_scipp(self, in_da):
        pass
