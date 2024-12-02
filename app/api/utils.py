import pandas as pd

import xml.etree.ElementTree as ET
from django.http import HttpResponse
## To connect to DB
from neo4j import GraphDatabase
import logging
from core.models import NeoTerm

logger = logging.getLogger('dict_config_logger')
REQUIRED_COLUMNS = ['Term', 'Definition', 'Context', 'Context Description']

def validate_csv(csv_file):
        missing_rows = []
        
        try:
            logger.info(f'Validating CSV file...')
            df = pd.read_csv(csv_file)
            logger.info(f'{len(df)} rows found in CSV file.')
            
        except pd.errors.EmptyDataError:
            return {'error': 'The CSV file is empty.', 'missing_rows': []}
        
        except pd.errors.ParserError:
            return {'error': 'The CSV file is malformed or not valid.', 'missing_rows': []}
        
        # Check for required columns
        for column in REQUIRED_COLUMNS:
            if column not in df.columns:
                return {'error': f'Missing required column: {column}', 'missing_rows': []}

        # Check for rows with missing data
        for index, row in df.iterrows():
            for column in REQUIRED_COLUMNS:
                if pd.isna(row[column]) or row[column] == '' or row[column] == ' ':
                    missing_rows.append({'row_index': index + 1, 'column': column})

        # If missing_rows is not empty, return them with error message
        if missing_rows:
            return {'error': 'Some rows are missing required data.', 'missing_rows': missing_rows}

        return {'error': None, 'data_frame': df, 'missing_rows': []}

def create_terms_from_csv(df):
    try:
        logger.info(f'Creating terms from CSV file...')
        logger.info(f'{len(df)} rows found in data frame file.')
        for index, row in df.iterrows():
            logger.info(f"This is the term for index { index }  {row['Term']}")

            term = NeoTerm.create_new_term()
            term.term = row['Term']
            term.definition = row['Definition']
            term.context = row['Context']
            # term.context_description = row['Context Description']

            term.save()
        logger.info(f'{len(df)} terms created from CSV file.')

    except Exception as e:
        logger.error(f'Error creating terms from CSV file: {str(e)}')
        return {'error': str(e)}

def convert_to_xml(data):
    try:    
        root = ET.Element("terms")
        
        for term_data in data:
            term_elem = ET.SubElement(root, "term")
            
            for key, value in term_data.items():
                child_elem = ET.SubElement(term_elem, key)
                child_elem.text = value
        
        # Generate the XML string
        xml_data = ET.tostring(root, encoding='utf-8')
        logger.info(f'XML data generated: {xml_data}')
        return HttpResponse(xml_data, content_type="application/xml")
    
    except Exception as e:
        return {'error': str(e)}
    
    ##Functions to connect to DB/API calls

   ## class Neo4jConnection:
  # Function to create a Neo4j driver, to initiate a connection to the database. The driver will create sessions and execute queries.
  ## For testing this is probably going to have uri of bolt://localhost:7687? -MB
def create_neo4j_driver(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))

# Function to run a query against Neo4j
## Utilizes the driver object created above to run the query (passed in as argument) and return the results. The parameters is optional for dynamic query building (if none are
## passed in, it will default to an empty dictionary). -MB
def run_neo4j_query(driver, query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters or {})
        ## record.data converts each returned record to a dictionary format to be easier to work with
        return [record.data() for record in result]

# Function to close the Neo4j driver
def close_neo4j_driver(driver):
    driver.close()
