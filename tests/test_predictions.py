import numpy as np

import labelbox.predictions as lbpreds

def test_vectorize_to_v4_label():
    segmentation_map = np.zeros((256,256), dtype=np.int32)
    segmentation_map[:32,:32] = 1 # top left corner
    segmentation_map[32:128,:32] = 2 # strip from top left to top middle
    segmentation_map[:64,-32:] = 3 # left half of bottom
    segmentation_map[-64:,-32:] = 3 # right half of bottom

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
    assert any(map(lambda x: x['geometry'][0] == {'x':0, 'y':0}, label['TL']))
    assert len(label['TL']) == 1

    # two regions, bottom left and bottom right
    assert len(label['2B']) == 2

    # does not contain unannotated class
    assert 'NO_LABELS' not in label.keys()
