"""
Pascal VOC writer, forked from https://github.com/AndrewCarterUK/pascal-voc-writer
"""
import os
from jinja2 import Environment, PackageLoader


class Writer:
    "Class for writing Pascal VOC annotation formats."
    def __init__(self, path, width, height):
        environment = Environment(
            loader=PackageLoader('labelbox.exporters', package_path='pascal_voc_writer/templates'),
            keep_trailing_newline=True)
        self.annotation_template = environment.get_template('annotation.xml')

        abspath = os.path.abspath(path)

        self.template_parameters = {
            'path': abspath,
            'filename': os.path.basename(abspath),
            'folder': os.path.basename(os.path.dirname(abspath)),
            'width': width,
            'height': height,
            'depth': 3,
            'database': 'Unknown',
            'segmented': 0,
            'objects': []
        }

    def add_object(self, name, xy_coords):
        """
        Adds an annotation object represented by `xy_coords` to the current annotation being built.

        The object can be a bounding box or polygon. This method will detect
        a bounding box annotation and create the appropriate output.
        """
        # figure out if label is bounding box or polygon
        if len(xy_coords) == 8:
            x_points = sorted(xy_coords[::2])
            y_points = sorted(xy_coords[1::2])
            if (x_points[0] == x_points[1] and x_points[2] == x_points[3]
                    and y_points[0] == y_points[1] and y_points[2] == y_points[3]):
                label_type = 'bndbox'
            else:
                label_type = 'polygon'
        else:
            label_type = 'polygon'

        self.template_parameters['objects'].append({
            'name': name,
            'type': label_type,
            'xy_coords': xy_coords,
            'pose': 'Unspecified',
            'truncated': 0,
            'difficult': 0,
        })

    def save(self, annotation_path):
        "Saves the current annotation to `annotation_path`."
        with open(annotation_path, 'w') as file:
            content = self.annotation_template.render(**self.template_parameters)
            file.write(content)
