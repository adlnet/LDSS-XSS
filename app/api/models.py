from neomodel import StructuredNode, StringProperty

class NeoTerm(StructuredNode):
    term = StringProperty(required=True)
    definition = StringProperty(required=True)
    context = StringProperty(required=True)
    context_description = StringProperty(required=True)

    