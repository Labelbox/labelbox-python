import numpy as np
from PIL import Image, ImageDraw

import labelbox.predictions as lbpreds


def test_vectorize_to_v4_label():
    segmentation_map = np.zeros((256, 256), dtype=np.int32)
    segmentation_map[:32, :32] = 1  # top left corner
    segmentation_map[32:128, :32] = 2  # strip from top left to top middle
    segmentation_map[:64, -32:] = 3  # left half of bottom
    segmentation_map[-64:, -32:] = 3  # right half of bottom

    legend = {
            1: 'TL',
            2: 'TM',
            3: '2B',
            4: 'NO_LABELS',
    }

    label = lbpreds.vectorize_to_v4_label(segmentation_map, legend)

    assert isinstance(label, dict)
    assert set(legend.values()).issuperset(label.keys())

    # contains top left, and has (0,0)
    assert any(map(lambda x: x['geometry'][0] == {'x': 0, 'y': 0}, label['TL']))
    assert len(label['TL']) == 1

    # two regions, bottom left and bottom right
    assert len(label['2B']) == 2

    # does not contain unannotated class
    assert 'NO_LABELS' not in label.keys()


def test_vectorize_simplify():
    coords = [
        (0.0, 0.0),
        (5.0, 4.0),
        (11.0, 5.5),
        (17.3, 3.2),
        (27.8, 0.1)
    ]

    segmentation_map = Image.new('L', (28, 28))
    draw = ImageDraw.Draw(segmentation_map)
    draw.polygon(coords, fill=1)

    legend = {
            1: 'CLASS',
    }
    segmentation_map = np.asarray(segmentation_map)

    label = lbpreds.vectorize_to_v4_label(segmentation_map, legend, max_num_points=None)
    label_simple = lbpreds.vectorize_to_v4_label(segmentation_map, legend, max_num_points=10)

    # simplification reduces the number of points
    assert len(label['CLASS'][0]['geometry']) > len(label_simple['CLASS'][0]['geometry'])


def test_vectorize_simplify_defaults(datadir):
    with open(datadir.join('dog_prediction.png'), 'rb') as fp:
        im = np.array(Image.open(fp))
        legend = {
                65535: 'Dog',
        }
        label = lbpreds.vectorize_to_v4_label(im, legend, max_num_points=None)

        # a huge label with no simplification
        assert len(label['Dog'][0]['geometry']) > 5000

        # by default, simplifies to <= 50 points
        label_simple = lbpreds.vectorize_to_v4_label(im, legend)
        assert len(label_simple['Dog'][0]['geometry']) <= 50
