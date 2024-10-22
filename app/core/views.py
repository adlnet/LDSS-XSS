from django.http import JsonResponse
from .models import NeoTerm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
import xml.etree.ElementTree as ET

import logging

logger = logging.getLogger('dict_config_logger')

def export_terms_as_json(request):
    terms = NeoTerm.nodes.all()

    if not terms:
        messages.error(request, "There is no data to export.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
    
    data = []
    for term in terms:
        data.append({
            'term': term.term,
            'definition': term.definition,
            'context': term.context,
            'context_description': term.context_description
        })
    
    # Return the data as a JSON response
    response = JsonResponse(data, safe=False)
    response['Content-Disposition'] = 'attachment; filename="terms.json"'
    return response

def export_terms_as_xml(request):
        terms = NeoTerm.nodes.all()

        if not terms:
            messages.error(request, "There is no data to export.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        data = [{'term': term.term, 'definition': term.definition, 'context': term.context, 'context_description': term.context_description} for term in terms]
        
        xml_output = convert_to_xml(data)
        if xml_output['error']:
            messages.error(request, f'Error exporting terms as XML: {xml_output["error"]}')
            return HttpResponseRedirect('.')
        else:
            response = HttpResponse(xml_output['xml_data'], content_type='application/xml')
            response['Content-Disposition'] = 'attachment; filename="terms.xml"'
        return response

def convert_to_xml(data):
    try:    
        root = ET.Element("NeoTerms")
        
        for term_data in data:
            term_elem = ET.SubElement(root, "NeoTerm")
            
            for key, value in term_data.items():
                child_elem = ET.SubElement(term_elem, key)
                child_elem.text = value
        
        # Generate the XML string
        xml_data = ET.tostring(root, encoding='utf-8')
        logger.info(f'XML data generated: {xml_data}')
        return {'error': None, 'xml_data': xml_data}
    except Exception as e:
        return {'error': str(e)}