from django.db import models
from django_neomodel import DjangoNode
from neomodel import StringProperty, Relationship
from uid.models import UIDNode, ProviderDjangoModel

# Create your models here.
class LCVTerm(DjangoNode):
    lcvid = StringProperty(required=True)
    uid_chain = StringProperty(required=True)
    ccv_term=Relationship('CCVTerm', 'CCV_TERM')

class CCVTerm(DjangoNode):
    ccvid = StringProperty(required=True)
    uid = StringProperty(required=True)
    uid_chain = StringProperty(required=True)
    uid_node = Relationship('UIDNode', 'HAS_UID')
    ccv_definition = Relationship('NeoDefinition', 'CCV_DEFINITION')
    lcv_term=Relationship('LCVTerm', 'CCV_TERM')

    @classmethod
    def create_node(cls, ccvid: str = None):
        ccv_term = CCVTerm() if ccvid is None else CCVTerm(ccvid=ccvid)
        ccv_uid_node = UIDNode.create_node(ccv_term.ccvid)
        ccv_term.ccvid = ccv_uid_node.uid
        ccv_term.save()

        ccv_term.uid_node.connect(ccv_uid_node)
        ccv_term.save()

        default_provider_name = ccv_term.ccvid
        provider = ProviderDjangoModel.ensure_provider_exists(default_provider_name)
        
        provider.uid.connect(ccv_uid_node)
        provider.save()

        ccv_term.uid_chain = f'{provider.default_uid}-{ccv_term.uid}'
        ccv_term.save()

        return ccv_term





