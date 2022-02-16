import pytest

from labelbox import Project
from labelbox.orm.comparison import Comparison, LogicalExpression


def test_comparison_creation():
    comparison = Comparison.Op.EQ(Project.name, "test")
    assert comparison.op == Comparison.Op.EQ
    assert comparison.field == Project.name
    assert comparison.value == "test"


def test_comparison_equality():
    Op = Comparison.Op
    assert Op.EQ(Project.name, "test") == Op.EQ(Project.name, "test")
    assert Op.EQ(Project.name, "test") != Op.EQ(Project.uid, "test")
    assert Op.EQ(Project.name, "test") != Op.EQ(Project.name, "t")
    assert Op.EQ(Project.name, "test") != Op.NE(Project.name, "test")


def test_rich_comparison():
    Op = Comparison.Op
    assert (Project.uid == "uid") == Op.EQ(Project.uid, "uid")
    assert (Project.uid != "uid") == Op.NE(Project.uid, "uid")
    assert (Project.uid < "uid") == Op.LT(Project.uid, "uid")
    assert (Project.uid <= "uid") == Op.LE(Project.uid, "uid")
    assert (Project.uid > "uid") == Op.GT(Project.uid, "uid")
    assert (Project.uid >= "uid") == Op.GE(Project.uid, "uid")

    # inverse operands
    assert ("uid" == Project.uid) == Op.EQ(Project.uid, "uid")
    assert ("uid" != Project.uid) == Op.NE(Project.uid, "uid")
    assert ("uid" < Project.uid) == Op.GT(Project.uid, "uid")
    assert ("uid" <= Project.uid) == Op.GE(Project.uid, "uid")
    assert ("uid" > Project.uid) == Op.LT(Project.uid, "uid")
    assert ("uid" >= Project.uid) == Op.LE(Project.uid, "uid")


def test_logical_expr_creation():
    comparison_1 = Comparison.Op.EQ(Project.name, "name")
    comparison_2 = Comparison.Op.LT(Project.uid, "uid")

    op = LogicalExpression.Op.AND(comparison_1, comparison_2)
    assert op.op == LogicalExpression.Op.AND
    assert op.first == comparison_1
    assert op.second == comparison_2


def test_logical_expr_ops():
    comparison_1 = Comparison.Op.EQ(Project.name, "name")
    comparison_2 = Comparison.Op.LT(Project.uid, "uid")

    log_op_1 = comparison_1 & comparison_2
    assert log_op_1 == LogicalExpression.Op.AND(comparison_1, comparison_2)
    log_op_2 = log_op_1 | comparison_1
    assert log_op_2 == LogicalExpression.Op.OR(log_op_1, comparison_1)
    log_op_3 = ~log_op_2
    assert log_op_3 == LogicalExpression.Op.NOT(log_op_2)

    # Can't create logical expressions with anything except comparisons and
    # other logical expressions.
    with pytest.raises(TypeError):
        logical_op = comparison_1 & 42
    with pytest.raises(TypeError):
        logical_op = comparison_1 | 42
