VECTOR_TOOLS = {'bbox', 'polygon', 'line', 'point'}
SEGMENTATION_TOOLS = {'segmentation'}
CLASSIFICATION_TOOLS = {'answer', 'answers'}
ALL_TOOL_TYPES = VECTOR_TOOLS.union(SEGMENTATION_TOOLS).union(
    CLASSIFICATION_TOOLS)
