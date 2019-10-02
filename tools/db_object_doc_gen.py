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
import importlib
import inspect
import json
import os
import re
import sys

import requests

sys.path.insert(0, os.path.abspath(".."))

import labelbox
import labelbox.utils
from labelbox.exceptions import LabelboxError


GENERAL_CLASSES = [labelbox.Client]
SCHEMA_CLASSES = [
    labelbox.Project, labelbox.Dataset, labelbox.DataRow, labelbox.Label,
    labelbox.AssetMetadata, labelbox.LabelingFrontend, labelbox.Task,
    labelbox.Webhook, labelbox.User, labelbox.Organization, labelbox.Review]

ERROR_CLASSES = [LabelboxError] + LabelboxError.__subclasses__()

_ALL_CLASSES = GENERAL_CLASSES + SCHEMA_CLASSES + ERROR_CLASSES


# Additional relationships injected into the Relationships part
# of a schema class.
ADDITIONAL_RELATIONSHIPS = {
    "Project": ["labels <em>(Label, ToMany)</em>"]}


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


def qual_class_name(cls):
    """ Returns the fully qualifieid class name (module + class name). """
    return cls.__module__ + "." + cls.__name__


def header(level, text):
    """ Wraps `text` into a <h> (header) tag ov the given level.
    Automatically increases the level by 2 to be inline with HelpDocs
    standards (h1 -> h3).

    Example:
        >>> header(2, "My Chapter")
        >>> "<h4>My Chapter</h4>
    """
    header_id = labelbox.utils.snake_case(text).replace(" ", "_")
    # Convert to level + 2 for HelpDocs standard.
    return tag(text, "h" + str(level + 2), {"id": header_id})


def paragraph(text):
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
    return tag("".join(tag(inject_class_links(item), "li")
                       for item in items), "ul")


def code_block(lines):
    """ Wraps lines into a Python code block in HelpDocs standard. """
    return tag("<br>".join(lines), "pre", {"class": "hljs python"})


def header_link(text, header_id):
    """ Converts the given text into a header link (intra-document relative
    link). Example:
        >>> header_link("Some text", "chapter_id")
        >>> <a href="#chapter_id">Some text</a>
    """
    return tag(text, "a", {"href":"#" + header_id})


def class_link(cls):
    """ Generates an intra-document link for the given class. Example:
        >>> from labelbox import Project
        >>> class_link(Project)
        >>> <a href="#class_labelbox_schema_project">Project</a>
    """
    header_id = "class_" + labelbox.utils.snake_case(qual_class_name(cls).
                                                     replace(".", "_"))
    return header_link(cls.__name__, header_id)


def inject_class_links(text):
    """ Finds all occurences of known class names in the given text and
    replaces them with relative links to those classes.
    """
    for cls in _ALL_CLASSES:
        pattern = r"\b(%s.)?%ss?\b" % (cls.__module__, cls.__name__)
        matches = list(re.finditer(pattern, text))
        for match in reversed(matches):
            start, end = match.span()
            text = text[:start] + class_link(cls) + text[end:]
    return text


def is_method(attribute):
    """ Determines if the given attribute is most likely a method. It's
    approximative since from Python 3 there are no more unbound methods. """
    return inspect.isfunction(attribute) and "." in attribute.__qualname__ \
        and inspect.getfullargspec(attribute).args[0] == 'self'


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

        return unordered_list([em(name + ":") + descr for name, descr
                in map(lambda r: r.split(":", 1), filter(None, result))])

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

    parts = (("Args: ", parse_list(args)),
             ("Kwargs: ", parse_block(kwargs)),
             ("Returns: ", parse_block(returns)),
             ("Raises: ", parse_list(raises)))

    return parse_block(docstring) + unordered_list([
        strong(name) + item for name, item in parts if bool(item)])


def generate_methods(cls):
    """ Generates HelpDocs style documentation for all the methods
    of the given class.
    """
    text = []
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if ((is_method(attr) and not attr_name.startswith("_")) or
            (cls == labelbox.Client and attr_name == "__init__")):
            text.append(paragraph(generate_signature(attr)))
            text.append(preprocess_docstring(attr.__doc__))

    return "".join(text)


def generate_signature(method):
    """ Generates HelpDocs style description of a method signature. """
    def fill_defaults(args, defaults):
        if defaults == None:
            defaults = tuple()
        return (None, ) * (len(args) - len(defaults)) + defaults

    argspec = inspect.getfullargspec(method)

    def format_arg(arg, default):
        return arg if default is None else arg + "=" + repr(default)

    components = list(map(format_arg, argspec.args,
                          fill_defaults(argspec.args, argspec.defaults)))

    if argspec.varargs:
        components.append("*" + argspec.varargs)
    if argspec.varkw:
        components.append("**" + argspec.varkw)

    components.extend(map(format_arg, argspec.kwonlyargs, fill_defaults(
        argspec.kwonlyargs, argspec.kwonlydefaults)))

    return tag(method.__name__ + "(" + ", ".join(components) + ")", "strong")


def generate_fields(cls):
    """ Generates HelpDocs style documentation for all the fields of a
    DbObject subclass.
    """
    return unordered_list([
        field.name + " " + em("(" + field.field_type.name + ")")
        for field in cls.fields()])


def generate_relationships(cls):
    """ Generates HelpDocs style documentation for all the relationships of a
    DbObject subclass.
    """
    relationships = list(ADDITIONAL_RELATIONSHIPS.get(cls.__name__, []))
    relationships.extend([
        r.name + " " + em("(%s %s)" % (r.destination_type_name,
                                       r.relationship_type.name))
        for r in cls.relationships()])

    return unordered_list(relationships)


def generate_class(cls, schema_class):
    """ Generates HelpDocs style documentation for the given class.
    Args:
        cls (type): The class to generate docs for.
        schema_class (bool): If `cls` is a DbObject subclass.
    Return:
        HelpDocs style documentation for `cls` containing class description,
        methods and fields and relationships if `schema_class`.
    """
    text = []
    text.append(header(2, "Class " + cls.__module__ + "." + cls.__name__))
    text.append(preprocess_docstring(cls.__doc__))
    if schema_class:
        text.append(header(3, "Fields"))
        text.append(generate_fields(cls))
        text.append(header(3, "Relationships"))
        text.append(generate_relationships(cls))
    methods = generate_methods(cls).strip()
    if len(methods):
        text.append(header(3, "Methods"))
        text.append(methods)
    return "\n".join(text)


def generate_all(general_classes, schema_classes, error_classes):
    """ Generates the full HelpDocs API documentation article body. """
    text = []
    text.append(header(3, "General Classes"))
    text.append(unordered_list([qual_class_name(cls) for cls in general_classes]))
    text.append(header(3, "Data Classes"))
    text.append(unordered_list([qual_class_name(cls) for cls in schema_classes]))
    text.append(header(3, "Error Classes"))
    text.append(unordered_list([qual_class_name(cls) for cls in error_classes]))

    text.append(header(1, "General classes"))
    text.extend(generate_class(cls, False) for cls in general_classes)
    text.append(header(1, "Data Classes"))
    text.extend(generate_class(cls, True) for cls in schema_classes)
    text.append(header(1, "Error Classes"))
    text.extend(generate_class(cls, False) for cls in error_classes)
    return "\n".join(text)


def main():
    argp = ArgumentParser(description=__doc__,
                          formatter_class=RawDescriptionHelpFormatter)
    argp.add_argument("helpdocs_api_key", nargs="?",
                      help="Helpdocs API key, used in uploading directly ")

    args = argp.parse_args()

    body  = generate_all(GENERAL_CLASSES, SCHEMA_CLASSES, ERROR_CLASSES)

    if args.helpdocs_api_key is not None:
        url = "https://api.helpdocs.io/v1/article/zg9hp7yx3u?key=" + \
            args.helpdocs_api_key
        response = requests.patch(url, data=json.dumps({"body": body}),
                                  headers={'content-type': 'application/json'})
        if response.status_code != 200:
            raise Exception("Failed to upload article with status code: %d "
                            " and message: %s", response.status_code,
                            response.text)
    else:
        sys.stdout.write(body)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
