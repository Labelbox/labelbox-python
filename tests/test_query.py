import pytest

from labelbox import query
from labelbox.db_objects import Project, Dataset
from labelbox.filter import Comparison, LogicalExpression


def test_format_where():
    query_str, params = query.format_where(Project.name > "name")
    assert query_str == "{name_gt: $param_0}"
    assert params == {"param_0": ("name", Project.name)}

    query_str, params = query.format_where(
        (Project.name != "name") & (Project.uid <= 42))
    assert query_str == "{AND: [{name_not: $param_0}, {id_lte: $param_1}]}"
    assert params == {"param_0": ("name", Project.name),
                      "param_1": (42, Project.uid)}

    query_str, params = query.format_where(~(3.4 < Project.name))
    assert query_str == "{NOT: [{name_gt: $param_0}]}"
    assert params == {"param_0": (3.4, Project.name)}


def param_declaration(where):
    _, params = query.format_where(where)
    return query.format_param_declaration(params)


def test_format_param_declaration():
    assert param_declaration(Project.name > "name") == "($param_0: String!)"
    assert param_declaration((Project.name > "name") & (Project.uid == 42)) \
        == "($param_0: String!, $param_1: ID!)"


def test_format_order_by():
    assert query.format_order_by(None) == ""
    assert query.format_order_by(Project.name.asc) == " orderBy: name_ASC"
    assert query.format_order_by(Project.uid.desc) == " orderBy: id_DESC"


def test_fields():
    assert set(query.fields(None)) == set()
    comparison_1 = Comparison.Op.EQ(Project.name, "name")
    assert set(query.fields(comparison_1)) == {Project.name}
    comparison_2 = Comparison.Op.LT(Dataset.uid, "uid")
    assert set(query.fields(comparison_2)) == {Dataset.uid}
    op = LogicalExpression.Op.AND(comparison_1, comparison_2)
    assert set(query.fields(op)) == {Project.name, Dataset.uid}


def test_logical_ops():
    Op = LogicalExpression.Op

    assert list(query.logical_ops(None)) == []
    comparison_1 = Comparison.Op.EQ(Project.name, "name")
    assert list(query.logical_ops(comparison_1)) == []
    comparison_2 = Comparison.Op.LT(Dataset.uid, "uid")
    assert list(query.logical_ops(comparison_2)) == []
    op_1 = Op.AND(comparison_1, comparison_2)
    assert list(query.logical_ops(op_1)) == [Op.AND]
    op_2 = Op.OR(comparison_1, comparison_2)
    assert list(query.logical_ops(op_2)) == [Op.OR]
    op_3 = Op.OR(op_1, op_2)
    assert list(query.logical_ops(op_3)) == [Op.OR, Op.AND, Op.OR]
