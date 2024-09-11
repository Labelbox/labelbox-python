from enum import Enum, auto

""" Classes for defining the client-side comparison operations used
for filtering data in fetches. Intended for use by library internals
and not by the end user.
"""


class LogicalExpressionComponent:
    """Implements bitwise logical operator methods (&, | and ~) so they
    return a LogicalExpression object containing this
    LogicalExpressionComponent.
    """

    def __and__(self, other):
        if not isinstance(other, (LogicalExpression, Comparison)):
            return NotImplemented
        return LogicalExpression.Op.AND(self, other)

    def __or__(self, other):
        if not isinstance(other, (LogicalExpression, Comparison)):
            return NotImplemented
        return LogicalExpression.Op.OR(self, other)

    def __invert__(self):
        return LogicalExpression.Op.NOT(self)


class LogicalExpression(LogicalExpressionComponent):
    """A unary (NOT) or binary (AND, OR) logical expression between
    Comparison or LogicalExpression objects."""

    class Op(Enum):
        """Type of logical operation."""

        AND = auto()
        OR = auto()
        NOT = auto()

        def __call__(self, first, second=None):
            """Forwards to LogicalExpression constructor, passing `self`
            as the `op` argument."""
            return LogicalExpression(self, first, second)

    def __init__(self, op, first, second=None):
        """LogicalExpression constructor.

        Args:
            op (LogicalExpression.Op): The type of logical operation.
            first (LogicalExpression or Comparison): First operand.
            second (LogicalExpression or Comparison): Second operand.
        """
        self.op = op
        self.first = first
        self.second = second

    def __eq__(self, other):
        return self.op == other.op and (
            (self.first == other.first and self.second == other.second)
            or (self.first == other.second and self.second == other.first)
        )

    def __hash__(self):
        return (
            hash(self.op) + 2833 * hash(self.first) + 2837 * hash(self.second)
        )

    def __repr__(self):
        return "%r %s %r" % (self.first, self.op.name, self.second)

    def __str__(self):
        return "%s %s %s" % (self.first, self.op.name, self.second)


class Comparison(LogicalExpressionComponent):
    """A comparison between a database value (represented by a
    `labelbox.schema.Field` object) and a constant value."""

    class Op(Enum):
        """Type of the comparison operation."""

        EQ = auto()
        NE = auto()
        LT = auto()
        GT = auto()
        LE = auto()
        GE = auto()

        def __call__(self, *args):
            """Forwards to Comparison constructor, passing `self`
            as the `op` argument."""
            return Comparison(self, *args)

    def __init__(self, op, field, value):
        """Comparison constructor.

        Args:
            op (Comparison.Op): The type of comparison.
            field (labelbox.schema.Field): Field being compared.
            value (any): Value to which the DB field is compared.
        """
        self.op = op
        self.field = field
        self.value = value

    def __eq__(self, other):
        return (
            self.op == other.op
            and self.field == other.field
            and self.value == other.value
        )

    def __hash__(self):
        return hash(self.op) + 2861 * hash(self.field) + 2927 * hash(self.value)

    def __repr__(self):
        return "%r %s %r" % (self.field, self.op.name, self.value)

    def __str__(self):
        return "%s %s %s" % (self.field, self.op.name, self.value)
