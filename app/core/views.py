from django.http import JsonResponse
from .models import NeoTerm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
import xml.etree.ElementTree as ET
from neomodel import db
import csv
from io import StringIO

import logging

logger = logging.getLogger('dict_config_logger')

def export_terms_as_csv(request):
    try:
        # Check if there's any data to export
        check_query = """
        MATCH (n:NeoTerm) 
        RETURN count(n) as count
        """
        result, _ = db.cypher_query(check_query)
        
        if result[0][0] == 0:
            messages.error(request, "There is no data to export.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '.'))

        query = """
        MATCH (t:NeoTerm)
        OPTIONAL MATCH (t)-[:POINTS_TO]->(d:NeoDefinition)
        OPTIONAL MATCH (a:NeoAlias)-[:POINTS_TO]->(t)
        OPTIONAL MATCH (c:NeoContext)-[:IS_A]->(t)
        OPTIONAL MATCH (cd:NeoContextDescription)-[:RATIONALE]->(c)
        WITH t, d, a, c, cd,
             CASE WHEN c IS NOT NULL THEN c.context ELSE null END as context,
             CASE WHEN cd IS NOT NULL THEN cd.context_description ELSE null END as context_desc
        RETURN DISTINCT 
            t.uid as uid,
            t.lcvid as lcvid,
            COLLECT(DISTINCT a.alias) as aliases,
            COLLECT(DISTINCT d.definition) as definitions,
            context,
            context_desc
        ORDER BY t.uid, context
        """
        
        results, _ = db.cypher_query(query)
        
        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        headers = ['UID', 'Parent ID', 'Aliases', 'Definitions', 'Context', 'Context Description']
        writer.writerow(headers)
        
        for row in results:
            processed_row = [
                str(row[0]) if row[0] is not None else '',  # uid
                str(row[1]) if row[1] is not None else '',  # lcvid
                '; '.join(filter(None, row[2])) if row[2] else '',  # aliases
                '; '.join(filter(None, row[3])) if row[3] else '',  # definitions
                str(row[4]) if row[4] is not None else '',  # context
                str(row[5]) if row[5] is not None else '',  # context description
            ]
            writer.writerow(processed_row)
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="terms_export.csv"'
        
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
