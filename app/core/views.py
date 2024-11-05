from django.http import JsonResponse
from .models import NeoTerm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
import xml.etree.ElementTree as ET

import logging

logger = logging.getLogger('dict_config_logger')

def export_terms_as_csv(request):
    try:
        neoterm_nodes = NeoTerm.nodes.all()
        if not neoterm_nodes:
            messages.error(request, "There is no data to export.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        data = []
        
        for neoterm in neoterm_nodes:
            term = {}
            term['uid'] = neoterm.uid

            aliases = neoterm.alias.all() 
            term['aliases'] = ', '.join([alias.alias for alias in aliases])

            definitions = neoterm.definition.all()
            if definitions:
                term['definition'] = definitions[0].definition

            contexts = neoterm.context.all()
            term['contexts'] = []

            for context in contexts:
                context_info = {
                    'context': context.context 
                }

                context_description_nodes = context.context_description.all()
                if context_description_nodes:
                    context_info['context_description'] = context_description_nodes[0].context_description
                
                term['contexts'].append(context_info)

            logger.info(term)

            data.append(term)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="terms.csv"'

        header = ','.join(data[0].keys())
        response.write(header + '\n')

        for term in data:
            row = ','.join([str(value) for value in term.values()])
            response.write(row + '\n')

        return response
    except Exception as e:
        logger.error(f'Error exporting terms as CSV: {e}')
        messages.error(request, f'Error exporting terms as CSV: {e}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

def export_terms_as_json(request):
    try:
        neoterm_nodes = NeoTerm.nodes.all()
        if not neoterm_nodes:
            messages.error(request, "There is no data to export.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
        
        data = []
        
        for neoterm in neoterm_nodes:
            term = {}

            term['uid'] = neoterm.uid

            aliases = neoterm.alias.all() 
            term['aliases'] = [alias.alias for alias in aliases]

            definitions = neoterm.definition.all()
            if definitions:
                term['definition'] = definitions[0].definition

            contexts = neoterm.context.all()
            term['contexts'] = []

            for context in contexts:
                context_info = {
                    'context': context.context 
                }

                context_description_nodes = context.context_description.all()
                if context_description_nodes:
                    context_info['context_description'] = context_description_nodes[0].context_description
                
                term['contexts'].append(context_info)

            logger.info(term)

            data.append(term)

        response = JsonResponse(data, safe=False, json_dumps_params={'indent': 4})
        response['Content-Disposition'] = 'attachment; filename="terms.json"'
        return response

    except Exception as e:
        logger.error(f'Error exporting terms as JSON: {e}')
        messages.error(request, f'Error exporting terms as JSON: {e}')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

def export_terms_as_xml(request):
        try:
            neoterm_nodes = NeoTerm.nodes.all()
            if not neoterm_nodes:
                messages.error(request, "There is no data to export.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))
            data = []
            
            for neoterm in neoterm_nodes:
                term = {}

                term['uid'] = neoterm.uid

                alaises = neoterm.alias.all()
                term['aliases'] = [alias.alias for alias in alaises]
                
                definition = neoterm.definition.all()[0]

                term['definition'] = definition.definition

                contexts = neoterm.context.all()

                term['contexts'] = []

                for context in contexts:
                    context_info = {
                        'context': context.context,
                    }
                    context_description_node = context.context_description.all()[0]
                    if context_description_node:
                        context_info['context_description'] = context_description_node.context_description
                    
                    term['contexts'].append(context_info)
                

                logger.info(term)

                data.append(term)

            
            xml_output = convert_to_xml(data)
            if xml_output['error']:
                messages.error(request, f'Error exporting terms as XML: {xml_output["error"]}')
                return HttpResponseRedirect('.')
            else:
                response = HttpResponse(xml_output['xml_data'], content_type='application/xml')
                response['Content-Disposition'] = 'attachment; filename="terms.xml"'
            return response
        except Exception as e:
            logger.error(f'Error exporting terms as XML: {e}')
            messages.error(request, f'Error exporting terms as XML: {e}')
            return HttpResponseRedirect('.')

def convert_to_xml(data):
    try:    
        root = ET.Element("Terms")
        
        for term_data in data:
            term_elem = ET.SubElement(root, "Term")
            
            for key, value in term_data.items():
                if isinstance(value, list):
                    list_elem = ET.SubElement(term_elem, key)
                    for item in value:
                        if isinstance(item, dict):
                            item_elem = ET.SubElement(list_elem, key[:-1])
                            for sub_key, sub_value in item.items():
                                sub_elem = ET.SubElement(item_elem, sub_key)
                                sub_elem.text = str(sub_value)
                        else:
                            item_elem = ET.SubElement(list_elem, "Alias")
                            item_elem.text = str(item)
                else:
                    child_elem = ET.SubElement(term_elem, key)
                    child_elem.text = str(value)
        
        # Generate the XML string
        xml_data = ET.tostring(root, encoding='utf-8')
        logger.info(f'XML data generated: {xml_data}')
        return {'error': None, 'xml_data': xml_data}
    except Exception as e:
        return {'error': str(e)}
