import pandas as pd
from .models import Term

REQUIRED_COLUMNS = ['Term', 'Definition', 'Context', 'Context Description']

def validate_csv(csv_file):
        missing_rows = []
        
        try:
            df = pd.read_csv(csv_file)
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

        return {'error': None, 'missing_rows': []}

def create_terms_from_csv(csv_file):

        df = pd.read_csv(csv_file)

        for index, row in df.iterrows():
            term = Term(term = row['Term'],
                        definition = row['Definition'],
                        context = row['Context'],
                        context_description = row['Context Description'])
            term.save()