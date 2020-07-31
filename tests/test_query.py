import pytest

from labelbox import Project, Dataset
from labelbox.orm import query
from labelbox.orm.comparison import Comparison, LogicalExpression


def format(*args, **kwargs):
    return query.Query(*args, **kwargs).format()[0]


def test_query_what():
    assert format("first", Project).startswith("first{")
    assert format("other", Project).startswith("other{")


def test_query_subquery():
    assert format("x", query.Query("sub", Project)).startswith("x{sub{")
    assert format("x", query.Query("bus", Project)).startswith("x{bus{")


def test_query_where():
    q, p = query.Query("x", Project, Project.name > "name").format()
    assert q.startswith("x(where: {name_gt: $param_0}){")
    assert p == {"param_0": ("name", Project.name)}

    q, p = query.Query("x", Project,
                       (Project.name != "name") & (Project.uid <= 42)).format()
    assert q.startswith(
        "x(where: {AND: [{name_not: $param_0}, {id_lte: $param_1}]}")
    assert p == {
        "param_0": ("name", Project.name),
        "param_1": (42, Project.uid)
    }


def test_query_param_declaration():
    q, _ = query.Query("x", Project, Project.name > "name").format_top("y")
    assert q.startswith("query yPyApi($param_0: String!){x")

    q, _ = query.Query("x", Project, (Project.name > "name") &
                       (Project.uid == 42)).format_top("y")
    assert q.startswith("query yPyApi($param_0: String!, $param_1: ID!){x")


def test_query_order_by():
    q, _ = query.Query("x", Project, order_by=Project.name.asc).format()
    assert q.startswith("x(orderBy: name_ASC){")

    q, _ = query.Query("x", Project, order_by=Project.uid.desc).format()
    assert q.startswith("x(orderBy: id_DESC){")


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
