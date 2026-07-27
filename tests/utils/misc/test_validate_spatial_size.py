# Copyright (c) MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import unittest

from parameterized import parameterized

from monai.utils.misc import validate_spatial_size

VALID_CASES = [
    [(1, 2, 3), (1, 2, 3)],
    [[10, 20], (10, 20)],
    [(5,), (5,)],
]

INVALID_CASES = [
    [(0, 2, 3), "roi_size", r"roi_size must have positive dimensions, got \(0, 2, 3\) with invalid dim 0=0"],
    [[10, 0, -1], "spatial_size", r"spatial_size must have positive dimensions, got \(10, 0, -1\) with invalid dim 1=0, dim 2=-1"],
    [(-5, 3), "max_roi_size", r"max_roi_size must have positive dimensions, got \(-5, 3\) with invalid dim 0=-5"],
]


class TestValidateSpatialSize(unittest.TestCase):

    @parameterized.expand(VALID_CASES)
    def test_valid(self, spatial_size, expected):
        self.assertTupleEqual(validate_spatial_size(spatial_size), expected)

    @parameterized.expand(INVALID_CASES)
    def test_invalid(self, spatial_size, name, pattern):
        with self.assertRaisesRegex(ValueError, pattern):
            validate_spatial_size(spatial_size, name=name)


if __name__ == "__main__":
    unittest.main()
