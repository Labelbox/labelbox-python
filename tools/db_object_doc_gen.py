""" Generates a list of Labelbox DB object types and their fields and
relationships.

You need to provide a path to the parent folder of the labelbox package
so that "import labelbox" works. Typically that is the repo root (..).
Provide it as a cmd-line argument:
    user@machine~ python3 db_object_doc_gen.py ..
"""
import sys

sys.path.append(sys.argv[1])


from labelbox import (Project, Dataset, DataRow, User, Organization, Task,
                      LabelingFrontend, Webhook)
from labelbox.schema import Field, Relationship


for cls in (Project, Dataset, DataRow, User, Organization, Task, LabelingFrontend,
            Webhook):
    print("")
    print("##", cls.__name__)

    print("")
    print("Field name", "|", "Field type")
    print("---", "|", "---")
    for field in (f for f in cls.__dict__.values() if isinstance(f, Field)):
        print(field.name, "|", field.field_type.name)

    print("")
    print("Relationship name", "|", "Destination type", "|", "Cardinality")
    print("---", "|", "---", "|", "---")
    for relationship in (r for r in cls.__dict__.values()
                         if isinstance(r, Relationship)):
        print(relationship.name, "|", relationship.destination_type_name, "|",
              relationship.relationship_type.name[2:])
