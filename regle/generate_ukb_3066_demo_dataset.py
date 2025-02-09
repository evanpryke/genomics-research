# Copyright 2023 Google LLC.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""Generates a SPINCs dataset consisting of a single spirometry blow.

The dataset contains parsed representations of the UKB demo spirometry blow
showcased in field
[3066](https://biobank.ctsu.ox.ac.uk/crystal/field.cgi?id=3066).

This spirometry exhalation volume curve example is publicly available and can
be downloaded following instructions on this page:
https://biobank.ndph.ox.ac.uk/ukb/refer.cgi?id=3

To install required packages:

```
$ pip3 install absl-py numpy pandas
```

To generate the demo dataset:

```
$ python3 generate_ukb_3066_demo_dataset.py --out_dir=/path/to/outputs
$ ls /path/to/outputs
ukb_3066_demo.flow_by_volume_one_channel.npy
ukb_3066_demo.flow_volume_in_channels.npy
ukb_3066_demo.three_curves_in_channels.npy
ukb_3066_demo.volume_by_time_one_channel.npy
```

These output files can then be used directly by the SPINCs modeling pipeline
(see generate_spincs.py).

To add additional blows, parse field 3066 values into a record dictionary and
add them to the `UKB_3066_RECORDS` list.
"""
import os
import pathlib
from typing import Any, Sequence

from absl import app
from absl import flags
import numpy as np
import pandas as pd

_OUT_DIR = flags.DEFINE_string(
    'out_dir',
    None,
    'The path of the output directory in which to write npy files.',
    short_name='o',
)

_DUPLICATES = flags.DEFINE_integer(
    'duplicates',
    1,
    'The number of duplicates of the example record to generate.',
)

flags.mark_flags_as_required(['out_dir'])

# The relative time scale, in seconds, associated with each series step; 0.01
# denotes that volume was sampled at 10 millisecond intervals.
TIME_SCALE = 0.01

# The volume scale applied to series points; series elements are recorded in ML,
# so a scale of 0.001 converts series elements to L.
VOLUME_SCALE = 0.001

# The number of points in the final ML input representation. Blows shorter than
# `MAX_NUM_POINTS` are right-padded to `MAX_NUM_POINTS` using the last value
# while blows londer than `MAX_NUM_POINTS` are truncated to `MAX_NUM_POINTS`.
MAX_NUM_POINTS = 1000

# The maximum volume value used when interpolating a flow-volume curve of length
# `MAX_NUM_POINTS`. The x-axis on this curve is evenly sampled points from
# `[0, MAX_INTERP_VOLUME]`.
MAX_INTERP_VOLUME = 6.58

# The publicly available spirometry demo curve from UKB from field 3066:
# https://biobank.ctsu.ox.ac.uk/crystal/field.cgi?id=3066
UKB_DEMO_SPIRO_3066_BLOW_ORDER = 2
UKB_DEMO_SPIRO_3066_BLOW_NUM_POINTS = 1224
UKB_DEMO_SPIRO_3066_SERIES = np.asarray([
    0,
    0,
    0,
    0,
    3,
    10,
    25,
    54,
    101,
    169,
    258,
    363,
    478,
    589,
    689,
    785,
    879,
    970,
    1059,
    1147,
    1234,
    1320,
    1403,
    1486,
    1569,
    1650,
    1730,
    1809,
    1888,
    1965,
    2040,
    2116,
    2188,
    2261,
    2331,
    2400,
    2465,
    2532,
    2595,
    2658,
    2720,
    2780,
    2838,
    2894,
    2948,
    3001,
    3052,
    3102,
    3151,
    3197,
    3243,
    3287,
    3329,
    3371,
    3412,
    3451,
    3490,
    3527,
    3564,
    3600,
    3635,
    3670,
    3703,
    3736,
    3769,
    3800,
    3831,
    3861,
    3890,
    3918,
    3947,
    3974,
    4001,
    4028,
    4054,
    4080,
    4105,
    4130,
    4154,
    4179,
    4202,
    4226,
    4249,
    4271,
    4292,
    4312,
    4332,
    4351,
    4371,
    4390,
    4408,
    4426,
    4444,
    4461,
    4478,
    4495,
    4512,
    4528,
    4544,
    4560,
    4575,
    4590,
    4604,
    4619,
    4633,
    4647,
    4661,
    4675,
    4689,
    4703,
    4716,
    4729,
    4742,
    4755,
    4767,
    4779,
    4791,
    4802,
    4812,
    4822,
    4831,
    4840,
    4849,
    4857,
    4866,
    4874,
    4882,
    4890,
    4898,
    4906,
    4914,
    4921,
    4929,
    4936,
    4944,
    4951,
    4958,
    4966,
    4973,
    4980,
    4987,
    4994,
    5000,
    5007,
    5013,
    5020,
    5026,
    5033,
    5039,
    5045,
    5051,
    5057,
    5063,
    5069,
    5075,
    5081,
    5087,
    5092,
    5098,
    5104,
    5109,
    5114,
    5119,
    5125,
    5130,
    5134,
    5139,
    5144,
    5148,
    5153,
    5157,
    5161,
    5166,
    5170,
    5174,
    5178,
    5182,
    5186,
    5190,
    5194,
    5198,
    5202,
    5205,
    5209,
    5213,
    5216,
    5220,
    5223,
    5226,
    5230,
    5233,
    5236,
    5240,
    5243,
    5246,
    5250,
    5253,
    5256,
    5259,
    5262,
    5264,
    5267,
    5270,
    5273,
    5276,
    5279,
    5283,
    5286,
    5289,
    5292,
    5295,
    5298,
    5300,
    5303,
    5306,
    5308,
    5311,
    5314,
    5316,
    5319,
    5321,
    5323,
    5326,
    5328,
    5331,
    5333,
    5335,
    5338,
    5340,
    5343,
    5345,
    5348,
    5350,
    5352,
    5355,
    5357,
    5360,
    5362,
    5365,
    5367,
    5369,
    5372,
    5374,
    5377,
    5379,
    5381,
    5384,
    5386,
    5388,
    5390,
    5391,
    5393,
    5395,
    5397,
    5399,
    5401,
    5403,
    5404,
    5406,
    5408,
    5410,
    5412,
    5413,
    5415,
    5417,
    5419,
    5420,
    5422,
    5424,
    5426,
    5427,
    5429,
    5431,
    5432,
    5434,
    5436,
    5438,
    5439,
    5441,
    5443,
    5444,
    5446,
    5447,
    5449,
    5450,
    5452,
    5453,
    5455,
    5456,
    5457,
    5459,
    5460,
    5461,
    5462,
    5463,
    5464,
    5466,
    5467,
    5468,
    5470,
    5471,
    5473,
    5474,
    5476,
    5477,
    5478,
    5480,
    5481,
    5482,
    5484,
    5485,
    5486,
    5487,
    5489,
    5490,
    5491,
    5492,
    5493,
    5494,
    5496,
    5497,
    5498,
    5499,
    5500,
    5501,
    5502,
    5503,
    5504,
    5505,
    5506,
    5507,
    5508,
    5509,
    5510,
    5510,
    5511,
    5512,
    5513,
    5514,
    5515,
    5515,
    5516,
    5517,
    5519,
    5520,
    5521,
    5523,
    5524,
    5525,
    5527,
    5529,
    5530,
    5532,
    5533,
    5535,
    5536,
    5537,
    5539,
    5540,
    5541,
    5543,
    5544,
    5545,
    5545,
    5546,
    5547,
    5548,
    5549,
    5549,
    5550,
    5551,
    5552,
    5552,
    5553,
    5554,
    5554,
    5555,
    5556,
    5557,
    5557,
    5558,
    5559,
    5560,
    5560,
    5561,
    5562,
    5562,
    5563,
    5564,
    5564,
    5565,
    5565,
    5566,
    5567,
    5567,
    5568,
    5569,
    5570,
    5571,
    5572,
    5573,
    5574,
    5576,
    5577,
    5578,
    5579,
    5580,
    5582,
    5583,
    5584,
    5585,
    5587,
    5588,
    5589,
    5590,
    5591,
    5591,
    5592,
    5593,
    5594,
    5595,
    5596,
    5596,
    5597,
    5598,
    5598,
    5599,
    5600,
    5601,
    5601,
    5602,
    5603,
    5603,
    5604,
    5605,
    5606,
    5606,
    5607,
    5608,
    5608,
    5609,
    5609,
    5609,
    5610,
    5611,
    5611,
    5612,
    5613,
    5613,
    5614,
    5615,
    5616,
    5616,
    5617,
    5618,
    5618,
    5619,
    5620,
    5621,
    5622,
    5623,
    5624,
    5624,
    5625,
    5626,
    5626,
    5627,
    5628,
    5628,
    5629,
    5629,
    5630,
    5630,
    5631,
    5632,
    5632,
    5633,
    5633,
    5634,
    5635,
    5635,
    5636,
    5637,
    5637,
    5638,
    5639,
    5639,
    5640,
    5641,
    5642,
    5642,
    5643,
    5644,
    5645,
    5645,
    5646,
    5647,
    5647,
    5648,
    5649,
    5649,
    5650,
    5651,
    5651,
    5652,
    5652,
    5653,
    5654,
    5654,
    5655,
    5656,
    5656,
    5657,
    5658,
    5658,
    5659,
    5660,
    5660,
    5661,
    5661,
    5662,
    5663,
    5663,
    5664,
    5664,
    5665,
    5665,
    5666,
    5666,
    5667,
    5667,
    5668,
    5668,
    5669,
    5669,
    5670,
    5670,
    5670,
    5671,
    5671,
    5672,
    5672,
    5672,
    5673,
    5673,
    5673,
    5673,
    5674,
    5674,
    5674,
    5675,
    5676,
    5676,
    5677,
    5677,
    5678,
    5678,
    5679,
    5679,
    5680,
    5681,
    5681,
    5682,
    5683,
    5683,
    5684,
    5684,
    5685,
    5686,
    5686,
    5687,
    5687,
    5688,
    5688,
    5688,
    5689,
    5689,
    5690,
    5690,
    5690,
    5691,
    5691,
    5692,
    5692,
    5692,
    5693,
    5693,
    5694,
    5694,
    5694,
    5695,
    5695,
    5695,
    5696,
    5696,
    5696,
    5696,
    5696,
    5696,
    5697,
    5697,
    5698,
    5698,
    5698,
    5699,
    5699,
    5699,
    5699,
    5700,
    5700,
    5700,
    5701,
    5701,
    5702,
    5702,
    5703,
    5703,
    5704,
    5704,
    5705,
    5705,
    5706,
    5706,
    5707,
    5707,
    5708,
    5709,
    5709,
    5710,
    5710,
    5711,
    5711,
    5712,
    5712,
    5712,
    5713,
    5713,
    5713,
    5714,
    5714,
    5714,
    5715,
    5715,
    5716,
    5716,
    5716,
    5717,
    5717,
    5717,
    5718,
    5718,
    5719,
    5719,
    5720,
    5720,
    5721,
    5721,
    5721,
    5722,
    5722,
    5722,
    5723,
    5723,
    5723,
    5723,
    5724,
    5724,
    5724,
    5725,
    5725,
    5725,
    5726,
    5726,
    5726,
    5727,
    5727,
    5728,
    5728,
    5729,
    5729,
    5729,
    5730,
    5730,
    5731,
    5732,
    5732,
    5733,
    5733,
    5734,
    5735,
    5735,
    5735,
    5736,
    5736,
    5736,
    5737,
    5737,
    5737,
    5738,
    5738,
    5738,
    5739,
    5739,
    5739,
    5739,
    5740,
    5740,
    5740,
    5741,
    5741,
    5741,
    5741,
    5741,
    5741,
    5742,
    5742,
    5742,
    5742,
    5742,
    5742,
    5742,
    5742,
    5742,
    5742,
    5741,
    5741,
    5740,
    5740,
    5740,
    5740,
    5739,
    5739,
    5739,
    5739,
    5739,
    5739,
    5740,
    5740,
    5740,
    5741,
    5742,
    5742,
    5743,
    5743,
    5744,
    5745,
    5745,
    5745,
    5746,
    5746,
    5747,
    5747,
    5748,
    5748,
    5748,
    5748,
    5748,
    5748,
    5749,
    5749,
    5749,
    5749,
    5749,
    5749,
    5749,
    5750,
    5750,
    5750,
    5750,
    5750,
    5751,
    5751,
    5751,
    5752,
    5752,
    5753,
    5753,
    5754,
    5754,
    5754,
    5755,
    5755,
    5756,
    5756,
    5756,
    5757,
    5757,
    5757,
    5758,
    5758,
    5758,
    5758,
    5759,
    5759,
    5759,
    5759,
    5759,
    5759,
    5759,
    5759,
    5759,
    5760,
    5760,
    5760,
    5761,
    5761,
    5761,
    5762,
    5762,
    5763,
    5763,
    5763,
    5764,
    5764,
    5764,
    5765,
    5765,
    5766,
    5766,
    5766,
    5767,
    5767,
    5767,
    5767,
    5767,
    5768,
    5768,
    5768,
    5768,
    5769,
    5769,
    5769,
    5770,
    5770,
    5770,
    5770,
    5770,
    5771,
    5771,
    5771,
    5771,
    5771,
    5772,
    5772,
    5772,
    5773,
    5773,
    5773,
    5774,
    5774,
    5774,
    5775,
    5775,
    5775,
    5776,
    5776,
    5777,
    5777,
    5777,
    5778,
    5778,
    5778,
    5778,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5780,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5779,
    5780,
    5780,
    5780,
    5780,
    5781,
    5781,
    5781,
    5782,
    5782,
    5782,
    5783,
    5783,
    5783,
    5784,
    5784,
    5784,
    5785,
    5785,
    5785,
    5785,
    5785,
    5786,
    5786,
    5786,
    5786,
    5786,
    5786,
    5786,
    5787,
    5787,
    5787,
    5788,
    5788,
    5788,
    5789,
    5789,
    5789,
    5790,
    5790,
    5790,
    5791,
    5791,
    5792,
    5792,
    5792,
    5793,
    5793,
    5793,
    5794,
    5794,
    5795,
    5795,
    5795,
    5796,
    5796,
    5796,
    5797,
    5797,
    5798,
    5798,
    5798,
    5798,
    5798,
    5799,
    5799,
    5799,
    5799,
    5800,
    5800,
    5800,
    5801,
    5801,
    5801,
    5801,
    5802,
    5802,
    5802,
    5802,
    5803,
    5803,
    5803,
    5803,
    5803,
    5803,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5804,
    5803,
    5804,
    5804,
    5804,
    5804,
    5804,
    5805,
    5805,
    5805,
    5805,
    5806,
    5806,
    5806,
    5806,
    5806,
    5806,
    5806,
    5806,
    5806,
    5806,
    5807,
    5807,
    5807,
    5807,
    5808,
    5808,
    5809,
    5809,
    5809,
    5810,
    5810,
    5810,
    5811,
    5811,
    5812,
    5812,
    5813,
    5813,
    5813,
    5814,
    5814,
    5815,
    5815,
    5815,
    5815,
    5816,
    5816,
    5816,
    5816,
    5817,
    5817,
    5817,
    5817,
    5817,
    5817,
    5817,
    5818,
    5818,
    5818,
    5818,
    5818,
    5818,
    5818,
    5819,
    5819,
    5819,
    5819,
    5819,
    5819,
    5819,
    5819,
    5819,
    5819,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5819,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5820,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5821,
    5820,
    5820,
    5820,
    5819,
    5819,
    5818,
    5818,
    5818,
    5817,
    5817,
    5817,
    5816,
    5816,
    5816,
    5816,
    5815,
    5815,
    5815,
    5816,
    5816,
    5816,
    5817,
    5817,
    5818,
    5819,
    5819,
    5820,
    5821,
    5822,
    5823,
    5823,
    5824,
    5825,
    5826,
    5827,
    5827,
    5828,
    5828,
    5829,
    5829,
    5829,
    5830,
    5830,
    5831,
    5831,
    5831,
    5831,
    5831,
    5832,
    5831,
    5832,
    5832,
    5832,
    5832,
    5832,
    5832,
    5832,
    5833,
    5833,
    5833,
    5833,
    5833,
    5833,
    5833,
    5834,
    5834,
    5834,
    5834,
    5834,
    5835,
    5835,
    5835,
    5835,
    5835,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5836,
    5835,
    5835,
    5835,
    5835,
    5834,
    5834,
    5834,
    5834,
    5833,
    5833,
    5833,
    5833,
    5833,
    5832,
    5832,
    5832,
    5832,
    5832,
    5832,
    5832,
    5832,
    5831,
])

# The expected keys used to define a spirometry blow record.
SPIRO_RECORD_EID_KEY = 'eid'
SPIRO_RECORD_VISIT_ID_KEY = 'visit_id'
SPIRO_RECORD_BLOW_ORDER_KEY = 'blow_order'
SPIRO_RECORD_BLOW_INDEX_KEY = 'blow_index'
SPIRO_RECORD_BLOW_NUM_POINTS_KEY = 'num_points'
SPIRO_RECORD_SERIES_KEY = 'series'

# A list of UKB spirometry blow records.
UKB_3066_RECORDS = [{
    SPIRO_RECORD_EID_KEY: 123456789,
    SPIRO_RECORD_VISIT_ID_KEY: 0,
    SPIRO_RECORD_BLOW_ORDER_KEY: UKB_DEMO_SPIRO_3066_BLOW_ORDER,
    SPIRO_RECORD_BLOW_INDEX_KEY: 0,
    SPIRO_RECORD_BLOW_NUM_POINTS_KEY: UKB_DEMO_SPIRO_3066_BLOW_NUM_POINTS,
    SPIRO_RECORD_SERIES_KEY: UKB_DEMO_SPIRO_3066_SERIES,
}]


def trim_records(records: list[dict[str, Any]]) -> pd.DataFrame:
  """Trims leading zeros from spirometry series to match blow length.

  Each blow is left-padded with a constant number of `num_zero` 0s where
  `len(series) = num_zeros + num_points`. We drop the first `num_zeros-1`
  zeros, keeping the final zero to capture the change in flow from time
  step `t=0` to time step `t=1`.

  Args:
    records: A list of record dictionaries representing individual blows.

  Returns:
    A dataframe containing each trimmed blow.
  """

  for record in records:
    series = record[SPIRO_RECORD_SERIES_KEY]
    num_points = record[SPIRO_RECORD_BLOW_NUM_POINTS_KEY]
    num_zeros = len(series) - num_points
    assert {0} == set(series[:num_zeros])
    trimmed_series = series[-(num_points + 1) :]
    assert 0 == trimmed_series[0]
    record[SPIRO_RECORD_SERIES_KEY] = trimmed_series
  return pd.DataFrame(records)


def compute_volume(series: np.ndarray, volume_scale: float) -> np.ndarray:
  """Rescale `series` to a liter-based volume curve."""
  return (series * volume_scale).astype(np.float32)


def compute_flow(volume: np.ndarray, time_scale: float) -> np.ndarray:
  """Computes flow for the given `volume` array and `time_scale`.

  Flow is the simple first derivative of volume. Note: This should be run before
  right padding to avoid large negative flow values if zero-padded.

  Args:
    volume: The volume-time curve.
    time_scale: The relative time scale, in seconds (i.e., input volume unit per
      second).

  Returns:
    A numpy array representing the corresponding flow curve.
  """
  return np.concatenate(([0.0], np.diff(volume) / time_scale))


def derive_base_curves(
    df: pd.DataFrame,
    volume_scale: float = VOLUME_SCALE,
    time_scale: float = TIME_SCALE,
) -> pd.DataFrame:
  """Derives the base time, volume, and flow curves from a blow series."""
  # Note: We copy the df so that we can rerun this function on the original df.
  df = df.copy()

  # Compute unpadded volume curve, max volume value, and last volume value.
  df['volume'] = df['series'].apply(
      lambda series: compute_volume(  # pylint: disable=g-long-lambda
          series,
          volume_scale,
      )
  )
  df['volume_max'] = df['volume'].apply(np.max)
  df['volume_last'] = df['volume'].apply(lambda volume: volume[-1])

  # Compute unpadded flow curve, max flow value, and last flow value.
  df['flow'] = df['volume'].apply(
      lambda volume: compute_flow(  # pylint: disable=g-long-lambda
          volume,
          time_scale,
      )
  )
  df['flow_max'] = df['flow'].apply(np.max)
  df['flow_last'] = df['flow'].apply(lambda flow: flow[-1])

  df = df.drop(columns=['series'])

  return df


def right_pad_array(
    array: np.ndarray,
    pad_value: float,
    max_num_points: int,
) -> np.ndarray:
  """Right pad the given array with `pad_value` up to `max_num_points`.

  Note: padding is only applied if the array's length is less than
  max_num_points. If the array's length is greater than `max_num_points`, its
  length is truncated to that value.

  Args:
    array: The target array to which padding is applied.
    pad_value: The padding value.
    max_num_points: The target length of the padded array.

  Returns:
    A padded array of length `max_num_points`.
  """
  array = array[: min(len(array), max_num_points)]
  array = np.pad(
      array,
      (0, max_num_points - len(array)),
      mode='constant',
      constant_values=pad_value,
  )
  return array


def compute_time(max_num_points: int, time_scale: float) -> np.ndarray:
  """Retruns a linear array containing `max_num_points` at `time_scale`."""
  return time_scale * np.linspace(
      0,
      max_num_points,
      num=max_num_points,
      endpoint=False,
      dtype=np.float32,
  )


def compute_flow_volume(
    flow: np.ndarray,
    volume: np.ndarray,
    min_volume: float,
    max_volume: float,
    num_points: int,
) -> np.ndarray:
  """Interpolates a flow_volume curve of `num_points`."""
  monotonic_volume = np.maximum.accumulate(volume)
  # Note: this guard ensures that the `xp` argument passed to np.interp is non-
  # increasing. From the documentation: "if the sequence `xp` is non-increasing,
  # interpolation results are meaningless." We relax the strict non-increasing
  # requirement to non-decreasing, as this gives extremely similar results to
  # breaking ties with a small amount of noise (i.e., adding the following to
  # the monotonic curve: `np.linspace(start=1e-4, stop=1e-3, num=num_points)`.
  assert np.all(np.diff(monotonic_volume) >= 0)

  volume_interp_intervals = np.linspace(
      start=min_volume, stop=max_volume, num=num_points
  )
  flow_interp = np.interp(
      volume_interp_intervals, xp=monotonic_volume, fp=flow, left=0, right=0
  )
  return flow_interp


def compute_fef(
    flow: np.ndarray, volume: np.ndarray, volume_max: float
) -> tuple[float, float, float, float]:
  """Computes FEF (forced expiratory flow) values.

  Computes FEF25%, FEF50%, FEF75%, and FEF25-75% values.
  See https://en.wikipedia.org/wiki/Spirometry#Forced_expiratory_flow_(FEF) for
  details.

  Args:
    flow: The flow series.
    volume: The volume series.
    volume_max: The maximum volume (FVC) value.

  Returns:
    A tuple (FEF25%, FEF50%, FEF75%, FEF25-75%).
  """
  flow_size = len(flow)
  assert flow_size == len(volume), 'Flow and Volume lengths do not match.'
  assert flow_size > 1, 'Flow should have more than one values'
  volumes_over_25 = volume >= (0.25 * volume_max)
  volumes_over_50 = volume >= (0.50 * volume_max)
  volumes_over_75 = volume >= (0.75 * volume_max)
  if not any(volumes_over_75):
    raise ValueError(f'Cannot find FEF75 in volume curve: {volume}')

  # Note np.argmax(..) finds the first True value in a boolean array.
  idx_25 = np.argmax(volumes_over_25)
  idx_50 = np.argmax(volumes_over_50)
  idx_75 = np.argmax(volumes_over_75)
  assert 0 <= idx_25 <= idx_50 <= idx_75 < flow_size

  fef25, fef50, fef75 = flow[[idx_25, idx_50, idx_75]]
  fef25_75 = flow[idx_25 : (idx_75 + 1)].mean()
  return fef25, fef50, fef75, fef25_75


def derive_input_representations(
    df: pd.DataFrame,
    max_num_points: int = MAX_NUM_POINTS,
    max_interp_volume: float = MAX_INTERP_VOLUME,
    time_scale: float = TIME_SCALE,
) -> pd.DataFrame:
  """Pads volume and flow to create ML model input representations.

  Note: Padding of both `0` or `row['volume_last']` is applied only when the
  length of the array is less than `max_num_points`. If the array's length is
  greater than `max_num_points`, the array is truncated to length
  `max_num_points`. This guarantees that, if padding is applied, the last value
  in the array is always the last value seen in the first `max_num_points`.

  Args:
    df: The dataframe containing the unpadded volume-time and flow-time curves.
    max_num_points: The length of the ML input representations. Curves larger
      than this value are truncated while curves shorter than this value are
      padded (volume is padded with either `0` or `volume_last`; flow is padded
      with `0`).
    max_interp_volume: The maximum volume value used when interpolating a
      flow-volume curve of length `max_num_points`. The x-axis on this curve is
      evenly sampled points from `[0, max_interp_volume]`.
    time_scale: The scale of each time step in seconds.

  Returns:
    A dataframe consisting of derived input representations.
  """
  # Note: We copy the df so that we can rerun this function on the original df.
  df = df.copy()

  # Compute time. Note: we use an empty apply so that we can get around pandas
  # trying to unpack the `time_curve`.
  df.loc[:, 'time'] = np.NaN
  time_curve = compute_time(max_num_points, time_scale)
  df['time'] = df['time'].apply(lambda _: time_curve)

  # Compute padded volume curves.
  df['volume_pad_zero'] = df.apply(
      lambda row: right_pad_array(  # pylint: disable=g-long-lambda
          row['volume'],
          pad_value=0,
          max_num_points=max_num_points,
      ),
      axis=1,
  )
  df['volume_pad_last'] = df.apply(
      lambda row: right_pad_array(  # pylint: disable=g-long-lambda
          row['volume'],
          pad_value=row['volume_last'],
          max_num_points=max_num_points,
      ),
      axis=1,
  )

  # Compute padded flow curve.
  df['flow_pad_zero'] = df.apply(
      lambda row: right_pad_array(  # pylint: disable=g-long-lambda
          row['flow'],
          pad_value=0,
          max_num_points=max_num_points,
      ),
      axis=1,
  )

  # Compute padded flow volume curves.
  df['flow_volume_pad_zero'] = df.apply(
      lambda row: compute_flow_volume(  # pylint: disable=g-long-lambda
          row['flow_pad_zero'],
          row['volume_pad_zero'],
          min_volume=0,
          max_volume=max_interp_volume,
          num_points=max_num_points,
      ),
      axis=1,
  )

  df['blow_fef25'], df['blow_fef50'], df['blow_fef75'], df['blow_fef25_75'] = (
      df.apply(
          lambda row: compute_fef(  # pylint: disable=g-long-lambda
              row['flow'], row['volume'], row['volume_max']
          ),
          axis=1,
          result_type='expand',
      ).T.values
  )

  df = df.drop(columns=['volume', 'flow'])
  return df


def get_time_flow_volume_np(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
  flow_np = np.array(df['flow_pad_zero'].to_list())
  volume_np = np.array(df['volume_pad_last'].to_list())
  return flow_np, volume_np


def join_flow_volume_in_channel(
    flow_np: np.ndarray,
    volume_np: np.ndarray,
) -> np.ndarray:
  flow_np_exp = np.expand_dims(flow_np, axis=2)
  volume_np_exp = np.expand_dims(volume_np, axis=2)
  return np.concatenate((flow_np_exp, volume_np_exp), axis=2)


def get_flow_by_volume_np(df: pd.DataFrame) -> np.ndarray:
  return np.expand_dims(np.array(df['flow_volume_pad_zero'].to_list()), axis=2)


def build_npy_files(df: pd.DataFrame, duplicates: int) -> dict[str, np.ndarray]:
  """Converts `df` into numpy arrays suitable for SPINCs `npy` dataset files."""
  assert duplicates >= 1
  # Stack the flow_by_time and volume_by_time curves along the last dimension.
  flow_np, volume_np = get_time_flow_volume_np(df)
  flow_and_volume_np = join_flow_volume_in_channel(flow_np, volume_np)

  # Parse just the flow_by_volume curve.
  flow_by_volume_np = get_flow_by_volume_np(df)

  # Parse just the volume_by_time curve.
  volume_by_time_np = np.expand_dims(volume_np, axis=2)

  # Stack the flow_by_time, volume_by_time, and flow_by_volume curves along the
  # last dimension.
  three_curves_np = np.concatenate(
      (flow_and_volume_np, flow_by_volume_np),
      axis=-1,
  )

  if duplicates > 1:
    flow_and_volume_np = np.repeat(flow_and_volume_np, duplicates, axis=0)
    flow_by_volume_np = np.repeat(flow_by_volume_np, duplicates, axis=0)
    volume_by_time_np = np.repeat(volume_by_time_np, duplicates, axis=0)
    three_curves_np = np.repeat(three_curves_np, duplicates, axis=0)

  # Placeholder numpy array of derived features, all zeros.
  derived_features = np.zeros(shape=(len(df) * duplicates, 5), dtype=float)

  assert flow_and_volume_np.shape == (len(df) * duplicates, 1000, 2)
  assert flow_by_volume_np.shape == (len(df) * duplicates, 1000, 1)
  assert volume_by_time_np.shape == (len(df) * duplicates, 1000, 1)
  assert three_curves_np.shape == (len(df) * duplicates, 1000, 3)
  assert derived_features.shape == (len(df) * duplicates, 5)

  filename_to_contents = {
      'ukb_3066_demo.flow_volume_in_channels.npy': flow_and_volume_np,
      'ukb_3066_demo.flow_by_volume_one_channel.npy': flow_by_volume_np,
      'ukb_3066_demo.volume_by_time_one_channel.npy': volume_by_time_np,
      'ukb_3066_demo.three_curves_in_channels.npy': three_curves_np,
      'ukb_3066_demo.derived_features.npy': derived_features,
  }

  return filename_to_contents


def write_npy_files(
    out_dir: pathlib.Path, filename_to_contents: dict[str, np.ndarray]
) -> None:
  """Writes each `np.ndarray` as an `npy` file in `out_dir`."""
  os.makedirs(out_dir, exist_ok=True)
  filepath_to_contents = {
      out_dir / filename: contents
      for filename, contents in filename_to_contents.items()
  }
  for filepath, contents in filepath_to_contents.items():
    with open(filepath, 'wb') as f:
      np.save(f, contents)


def main(unused_argv: Sequence[str]) -> None:
  trimmed_records_df = trim_records(UKB_3066_RECORDS)
  base_curve_dfs = derive_base_curves(trimmed_records_df)
  blow_curve_derived_df = derive_input_representations(base_curve_dfs)
  filename_to_contents = build_npy_files(
      blow_curve_derived_df, duplicates=_DUPLICATES.value
  )
  write_npy_files(pathlib.Path(_OUT_DIR.value), filename_to_contents)


if __name__ == '__main__':
  app.run(main)
