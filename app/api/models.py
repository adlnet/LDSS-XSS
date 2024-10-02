from neomodel import StructuredNode, StringProperty

class Term(StructuredNode):
    term = StringProperty(required=True)
    definition = StringProperty(required=True)
    context = StringProperty(required=True)
    context_description = StringProperty(required=True)

    