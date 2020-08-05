#!/usr/bin/env python3
"""
Generates API documentation for the Labelbox Python Client in a form
tailored for HelpDocs (https://www.helpdocs.io). Supports automatic
uploading of generated documentation to Labelbox's HelpDocs pages,
if given a HelpDocs API Key for Labelbox with write priviledges. Otherwise
outputs the generated documenation to stdout.

Must be invoked from within the `tools` directory in the Labelbox
Python client repo as it assumes that the Labelbox Python client source
can be found at relative path "../labelbox".

Usage:
    $ cd repo_root/tools
    $ python3 db_object_doc_gen.py # outputs to stdout
    $ python3 db_object_doc_gen.py <api_key> # uploads to HelpDocs
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import Enum
import importlib
import inspect
from itertools import chain
import json
import os
import re
import sys

import requests

sys.path.insert(0, os.path.abspath(".."))

import labelbox
from labelbox.utils import snake_case
from labelbox.exceptions import LabelboxError
from labelbox.orm.db_object import Deletable, BulkDeletable, Updateable
from labelbox.orm.model import Entity
from labelbox.schema.project import LabelerPerformance

GENERAL_CLASSES = [labelbox.Client]
SCHEMA_CLASSES = [
    labelbox.Project, labelbox.Dataset, labelbox.DataRow, labelbox.Label,
    labelbox.AssetMetadata, labelbox.LabelingFrontend, labelbox.Task,
    labelbox.Webhook, labelbox.User, labelbox.Organization, labelbox.Review,
    labelbox.Prediction, labelbox.PredictionModel, LabelerPerformance
]

ERROR_CLASSES = [LabelboxError] + LabelboxError.__subclasses__()

_ALL_CLASSES = GENERAL_CLASSES + SCHEMA_CLASSES + ERROR_CLASSES

# Additional relationships injected into the Relationships part
# of a schema class.
ADDITIONAL_RELATIONSHIPS = {"Project": ["labels <em>(Label, ToMany)</em>"]}


def tag(text, tag, values={}):
    """ Wraps text into an HTML tag. Example:
        >>> tag("Some text", "p", {"id": "id_value"})
        >>> "<p id=id_value>Some text</p>

    Args:
        text (str): The text to wrap inside tags.
        tag (str): The kind of tag.
        values (dict): Optional additional tag key-value pairs.
    """
    values = "".join(" %s=%s" % item for item in values.items())
    return "<%s%s>%s</%s>" % (tag, values, text, tag)


def header(level, text, header_id=None):
    """ Wraps `text` into a <h> (header) tag ov the given level.
    Automatically increases the level by 2 to be inline with HelpDocs
    standards (h1 -> h3).

    Example:
        >>> header(2, "My Chapter")
        >>> "<h4>My Chapter</h4>

    Args:
        level (int): Level of header.
        text (str): Header text.
        header_id (str or None): The ID of the header. If None it's
            generated from text by converting to snake_case and
            replacing all whitespace with "_".
    """
    if header_id == None:
        header_id = snake_case(text).replace(" ", "_")
    # Convert to level + 2 for HelpDocs standard.
    return tag(text, "h" + str(level + 2), {"id": header_id})


def paragraph(text, link_classes=True):
    if link_classes:
        text = inject_class_links(text)
    return tag(text, "p")


def strong(text):
    return tag(text, "strong")


def em(text):
    return tag(text, "em")


def unordered_list(items):
    """ Formats given items into an unordered HTML list. Example:
        >>> unordered_list(["First", "Second"])
        >>> "<ul><li>First</li><li>Second</li></ul>
    """
    if len(items) == 0:
        return ""
    return tag("".join(tag(inject_class_links(item), "li") for item in items),
               "ul")


def code_block(lines):
    """ Wraps lines into a Python code block in HelpDocs standard. """
    return tag("<br>".join(lines), "pre", {"class": "hljs python"})


def inject_class_links(text):
    """ Finds all occurences of known class names in the given text and
    replaces them with relative links to those classes.
    """
    pattern_link_pairs = [(r"\b(%s.)?%ss?\b" % (cls.__module__, cls.__name__),
                           "#" + snake_case(cls.__name__))
                          for cls in _ALL_CLASSES]
    pattern_link_pairs.append(
        (r"\bPaginatedCollection\b", "general-concepts#pagination"))

    for pattern, link in pattern_link_pairs:
        matches = list(re.finditer(pattern, text))
        for match in reversed(matches):
            start, end = match.span()
            link = tag(match.group(), "a", {"href": link})
            text = text[:start] + link + text[end:]
    return text


def is_method(attribute):
    """ Determines if the given attribute is most likely a method. It's
    approximative since from Python 3 there are no more unbound methods. """
    return inspect.isfunction(attribute) and "." in attribute.__qualname__ \
        and inspect.getfullargspec(attribute).args[:1] == ['self']


def preprocess_docstring(docstring):
    """ Parses and re-formats the given class or method `docstring`
    from Python documentation (Google style) into HelpDocs Python Client
    API specification style.
    """

    def extract(docstring, keyword):
        """ Helper method for extracting a part of the docstring. Parts
        like "Returns" and "Args" are supported. Splits the `docstring`
        into two parts, before and after the given keyword.
        """
        if docstring is None or docstring == "":
            return "", ""

        pattern = r"\n\s*%ss?:\s*\n" % keyword
        split = re.split(pattern, docstring)
        if len(split) == 1:
            return docstring, None
        elif len(split) == 2:
            return split
        else:
            raise Exception("Docstring '%s' split in more then two parts "
                            "by keyword '%s'" % (docstring, keyword))

    docstring, raises = extract(docstring, "Raise")
    docstring, returns = extract(docstring, "Return")
    docstring, kwargs = extract(docstring, "Kwarg")
    docstring, args = extract(docstring, "Arg")

    def parse_list(text):
        """ Helper method for parsing a list of items from Google-style
        Python docstring. Used for argument and exception lists. Supports
        multi-line text, assuming proper indentation. """
        if not bool(text):
            return []

        indent = re.match(r"^\s*", text).group()
        lines = re.split(r"\n", text)
        result = [lines[0].strip()]
        for line in lines[1:]:
            next_indent = re.match(r"^\s*", line).group()
            if len(next_indent) > len(indent):
                result[-1] += " " + line.strip()
            else:
                result.append(line.strip())

        return unordered_list([
            em(name + ":") + descr for name, descr in map(
                lambda r: r.split(":", 1), filter(None, result))
        ])

    def parse_block(block):
        """ Helper for parsing a block of documentation that possibly contains
        Python code in an indentent block with each line starting with ">>>".
        """
        if block is None:
            return ""

        result = []
        lines_p, f_p = [], lambda l: paragraph(" ".join(l))
        lines_code, f_code = [], code_block

        def process(collection, f):
            if collection:
                result.append(f(collection))
                collection.clear()

        for line in filter(None, map(str.strip, block.split("\n"))):
            if line.startswith(">>>"):
                process(lines_p, f_p)
                lines_code.append(line)
            else:
                process(lines_code, f_code)
                lines_p.append(line)

        process(lines_p, f_p)
        process(lines_code, f_code)

        return "".join(result)

    def parse_maybe_block(text):
        """ Adapts to text. Calls `parse_block` if there is a codeblock
        indented, otherwise just joins lines into a single line and
        reduces whitespace.
        """
        if text is None:
            return ""
        if re.findall(r"\n\s+>>>", text):
            return parse_block()
        return re.sub(r"\s+", " ", text).strip()

    parts = (("Args: ", parse_list(args)), ("Kwargs: ",
                                            parse_maybe_block(kwargs)),
             ("Returns: ", parse_maybe_block(returns)), ("Raises: ",
                                                         parse_list(raises)))

    return parse_block(docstring) + unordered_list(
        [strong(name) + item for name, item in parts if bool(item)])


def generate_functions(cls, predicate):
    """ Generates HelpDocs style documentation for the functions
    of the given class that satisfy the given predicate. The functions
    also must not being with "_", with the exception of Client.__init__.

    Args:
        cls (type): The class being generated.
        predicate (callable): A callable accepting a single argument
            (class attribute) and returning a bool indicating if
            that attribute should be included in documentation
            generation.
    Return:
        Textual documentation of functions belonging to the given
        class that satisfy the given predicate.
    """

    # Get all class atrributes plus selected superclass attributes.
    attributes = chain(cls.__dict__.values(),
                       (getattr(cls, name)
                        for name in ("delete", "update")
                        if name in dir(cls) and name not in cls.__dict__))

    # Remove attributes not satisfying the predicate
    attributes = filter(predicate, attributes)

    # Extract function from staticmethod and classmethod wrappers
    attributes = map(lambda attr: getattr(attr, "__func__", attr), attributes)

    # Apply name filter
    attributes = filter(lambda attr: not attr.__name__.startswith("_") or \
                        (cls == labelbox.Client and attr.__name__ == "__init__"),
                        attributes)

    # Sort on name
    attributes = sorted(attributes, key=lambda attr: attr.__name__)

    return "".join(
        paragraph(generate_signature(function)) +
        preprocess_docstring(function.__doc__) for function in attributes)


def generate_signature(method):
    """ Generates HelpDocs style description of a method signature. """

    def fill_defaults(args, defaults):
        if defaults == None:
            defaults = tuple()
        return (None,) * (len(args) - len(defaults)) + defaults

    argspec = inspect.getfullargspec(method)

    def format_arg(arg, default):
        return arg if default is None else arg + "=" + repr(default)

    components = list(
        map(format_arg, argspec.args,
            fill_defaults(argspec.args, argspec.defaults)))

    if argspec.varargs:
        components.append("*" + argspec.varargs)
    if argspec.varkw:
        components.append("**" + argspec.varkw)

    components.extend(
        map(format_arg, argspec.kwonlyargs,
            fill_defaults(argspec.kwonlyargs, argspec.kwonlydefaults)))

    return tag(method.__name__ + "(" + ", ".join(components) + ")", "strong")


def generate_fields(cls):
    """ Generates HelpDocs style documentation for all the fields of a
    DbObject subclass.
    """
    return unordered_list([
        field.name + " " + em("(" + field.field_type.name + ")")
        for field in cls.fields()
    ])


def generate_relationships(cls):
    """ Generates HelpDocs style documentation for all the relationships of a
    DbObject subclass.
    """
    relationships = list(ADDITIONAL_RELATIONSHIPS.get(cls.__name__, []))
    relationships.extend([
        r.name + " " + em("(%s %s)" %
                          (r.destination_type_name, r.relationship_type.name))
        for r in cls.relationships()
    ])

    return unordered_list(relationships)


def generate_constants(cls):
    values = []
    for name, value in cls.__dict__.items():
        if name.isupper() and isinstance(value, (str, int, float, bool)):
            values.append("%s %s" %
                          (name, em("(" + type(value).__name__ + ")")))

    for name, value in cls.__dict__.items():
        if isinstance(value, type) and issubclass(value, Enum):
            enumeration_items = unordered_list([item.name for item in value])
            values.append("Enumeration %s%s" % (name, enumeration_items))

    return unordered_list(values)


def generate_class(cls):
    """ Generates HelpDocs style documentation for the given class.
    Args:
        cls (type): The class to generate docs for.
    Return:
        HelpDocs style documentation for `cls` containing class description,
        methods and fields and relationships if `schema_class`.
    """
    text = []
    schema_class = issubclass(cls, Entity)

    text.append(header(2, cls.__name__, snake_case(cls.__name__)))

    package_and_superclasses = "Class " + cls.__module__ + "." + cls.__name__
    if schema_class:
        superclasses = [
            plugin.__name__
            for plugin in (Updateable, Deletable, BulkDeletable)
            if issubclass(cls, plugin)
        ]
        if superclasses:
            package_and_superclasses += " (%s)" % ", ".join(superclasses)
    package_and_superclasses += "."
    text.append(paragraph(package_and_superclasses, False))

    text.append(preprocess_docstring(cls.__doc__))

    constants = generate_constants(cls)
    if constants:
        text.append(header(3, "Constants"))
        text.append(constants)

    if schema_class:
        text.append(header(3, "Fields"))
        text.append(generate_fields(cls))
        text.append(header(3, "Relationships"))
        text.append(generate_relationships(cls))

    for name, predicate in (("Static Methods",
                             lambda attr: type(attr) == staticmethod),
                            ("Class Methods",
                             lambda attr: type(attr) == classmethod),
                            ("Object Methods", is_method)):
        functions = generate_functions(cls, predicate).strip()
        if len(functions):
            text.append(header(3, name))
            text.append(functions)

    return "\n".join(text)


def generate_all():
    """ Generates the full HelpDocs API documentation article body. """
    text = []
    text.append(header(3, "General Classes"))
    text.append(unordered_list([cls.__name__ for cls in GENERAL_CLASSES]))
    text.append(header(3, "Data Classes"))
    text.append(unordered_list([cls.__name__ for cls in SCHEMA_CLASSES]))
    text.append(header(3, "Error Classes"))
    text.append(unordered_list([cls.__name__ for cls in ERROR_CLASSES]))

    text.append(header(1, "General classes"))
    text.extend(generate_class(cls) for cls in GENERAL_CLASSES)
    text.append(header(1, "Data Classes"))
    text.extend(generate_class(cls) for cls in SCHEMA_CLASSES)
    text.append(header(1, "Error Classes"))
    text.extend(generate_class(cls) for cls in ERROR_CLASSES)
    return "\n".join(text)


def main():
    argp = ArgumentParser(description=__doc__,
                          formatter_class=RawDescriptionHelpFormatter)
    argp.add_argument("helpdocs_api_key",
                      nargs="?",
                      help="Helpdocs API key, used in uploading directly ")

    args = argp.parse_args()

    body = generate_all()
    if args.helpdocs_api_key is not None:
        url = "https://api.helpdocs.io/v1/article/zg9hp7yx3u?key=" + \
            args.helpdocs_api_key
        response = requests.patch(url,
                                  data=json.dumps({"body": body}),
                                  headers={'content-type': 'application/json'})
        if response.status_code != 200:
            raise Exception(
                "Failed to upload article with status code: %d "
                " and message: %s", response.status_code, response.text)
    else:
        sys.stdout.write(body)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
