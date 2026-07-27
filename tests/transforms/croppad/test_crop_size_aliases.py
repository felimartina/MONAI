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
import warnings

from parameterized import parameterized

from monai.transforms import (
    CenterSpatialCrop,
    CenterSpatialCropd,
    RandCropByLabelClasses,
    RandCropByLabelClassesd,
    RandCropByPosNegLabel,
    RandCropByPosNegLabeld,
    RandSpatialCrop,
    RandSpatialCropd,
    RandSpatialCropSamples,
    RandSpatialCropSamplesd,
    RandWeightedCrop,
    RandWeightedCropd,
)

ARRAY_CASES = [
    (CenterSpatialCrop, {"roi_size": [2, 2]}, {"spatial_size": [2, 2]}, "roi_size"),
    (RandSpatialCrop, {"roi_size": [2, 2]}, {"spatial_size": [2, 2]}, "roi_size"),
    (
        RandSpatialCropSamples,
        {"roi_size": [2, 2], "num_samples": 1},
        {"spatial_size": [2, 2], "num_samples": 1},
        "roi_size",
    ),
    (
        RandWeightedCrop,
        {"roi_size": [2, 2], "num_samples": 1},
        {"spatial_size": [2, 2], "num_samples": 1},
        "roi_size",
    ),
    (
        RandCropByPosNegLabel,
        {"roi_size": [2, 2], "num_samples": 1},
        {"spatial_size": [2, 2], "num_samples": 1},
        "roi_size",
    ),
    (
        RandCropByLabelClasses,
        {"roi_size": [2, 2], "num_classes": 2, "num_samples": 1},
        {"spatial_size": [2, 2], "num_classes": 2, "num_samples": 1},
        "roi_size",
    ),
]

DICT_CASES = [
    (
        CenterSpatialCropd,
        {"keys": "img", "roi_size": [2, 2]},
        {"keys": "img", "spatial_size": [2, 2]},
        "roi_size",
    ),
    (
        RandSpatialCropd,
        {"keys": "img", "roi_size": [2, 2]},
        {"keys": "img", "spatial_size": [2, 2]},
        "roi_size",
    ),
    (
        RandSpatialCropSamplesd,
        {"keys": "img", "roi_size": [2, 2], "num_samples": 1},
        {"keys": "img", "spatial_size": [2, 2], "num_samples": 1},
        "roi_size",
    ),
    (
        RandWeightedCropd,
        {"keys": "img", "w_key": "w", "roi_size": [2, 2], "num_samples": 1},
        {"keys": "img", "w_key": "w", "spatial_size": [2, 2], "num_samples": 1},
        "spatial_size",
    ),
    (
        RandCropByPosNegLabeld,
        {"keys": "img", "label_key": "label", "roi_size": [2, 2], "num_samples": 1},
        {"keys": "img", "label_key": "label", "spatial_size": [2, 2], "num_samples": 1},
        "spatial_size",
    ),
    (
        RandCropByLabelClassesd,
        {"keys": "img", "label_key": "label", "roi_size": [2, 2], "num_classes": 2, "num_samples": 1},
        {"keys": "img", "label_key": "label", "spatial_size": [2, 2], "num_classes": 2, "num_samples": 1},
        "spatial_size",
    ),
]


def _cropper_size(obj, attr: str):
    cropper = getattr(obj, "cropper", obj)
    if hasattr(cropper, "cropper"):
        cropper = cropper.cropper
    return getattr(cropper, attr)


class TestCropSizeAliases(unittest.TestCase):
    @parameterized.expand(ARRAY_CASES)
    def test_array_alias_equivalence(self, cls, preferred, deprecated, attr):
        preferred_obj = cls(**preferred)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            deprecated_obj = cls(**deprecated)
        self.assertTrue(any(issubclass(w.category, FutureWarning) for w in caught))
        self.assertEqual(getattr(preferred_obj, attr), getattr(deprecated_obj, attr))
        if hasattr(preferred_obj, "spatial_size"):
            self.assertEqual(preferred_obj.spatial_size, deprecated_obj.spatial_size)

    @parameterized.expand(DICT_CASES)
    def test_dict_alias_equivalence(self, cls, preferred, deprecated, attr):
        preferred_obj = cls(**preferred)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            deprecated_obj = cls(**deprecated)
        self.assertTrue(any(issubclass(w.category, FutureWarning) for w in caught))
        self.assertEqual(_cropper_size(preferred_obj, attr), _cropper_size(deprecated_obj, attr))

    def test_missing_size_raises(self):
        with self.assertRaises(ValueError):
            CenterSpatialCrop()
        with self.assertRaises(ValueError):
            RandCropByPosNegLabel()
        with self.assertRaises(ValueError):
            CenterSpatialCropd(keys="img")

    def test_conflicting_sizes_raise(self):
        with self.assertRaises(ValueError):
            CenterSpatialCrop(roi_size=[2, 2], spatial_size=[3, 3])
        with self.assertRaises(ValueError):
            RandCropByPosNegLabel(roi_size=[2, 2], spatial_size=[3, 3])


if __name__ == "__main__":
    unittest.main()
