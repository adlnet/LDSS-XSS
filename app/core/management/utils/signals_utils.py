import logging

from core.models import ChildTermSet, Term, TermSet

logger = logging.getLogger('dict_config_logger')


def create_child_termset(termset_name, parent_iri, status, updated_by):
    """function to create/save termset"""
    parent_iri = \
        ChildTermSet.objects.create(parent_term_set=parent_iri,
                                    name=termset_name,
                                    status=status,
                                    updated_by=updated_by)
    parent_iri.save()

    return parent_iri


def create_terms(term_obj, term_name, parent_iri, status, updated_by):
    """function to create/save terms"""

    term = \
        Term.objects.create(term_set=parent_iri, name=term_name,
                            status=status, updated_by=updated_by)
    term.__dict__.update(term_obj)
    term.save()

    return term


def termset_object(metadata, schema_iri, status, updated_by):
    """Function to flatten/normalize data dictionary"""

    # Check every key elements value in data
    for element in metadata:
        # If Json Field value is a Nested Json
        if isinstance(metadata[element], dict):
            for sub_element in metadata[element]:
                if isinstance(metadata[element][sub_element], dict):
                    parent_iri = create_child_termset(
                        element, schema_iri, status, updated_by)
                    termset_object(metadata[element], parent_iri, status,
                                   updated_by)
                # If Json Field value is a string
                elif isinstance(metadata[element][sub_element], str):
                    term_object(
                        metadata[element], element, schema_iri, status,
                        updated_by)
                break


def term_object(term_obj, term_name, parent_iri, status, updated_by):
    """function to update flattened object to dict variable"""

    create_terms(term_obj, term_name, parent_iri, status, updated_by)


def update_status(termset, status, updated_by):
    """function to update the status of children terms/termsets"""

    child_termset = ChildTermSet.objects.filter(parent_term_set=termset)

    if child_termset:
        for child_element in child_termset:
            child_termset.update(status=status, updated_by=updated_by)
            update_status(child_element, status, updated_by)
    term = termset.terms
    term.update(status=status, updated_by=updated_by)


def termset_map(target, source, mapping):
    """
    recursive function to create mappings between schemas
    """
    for kid in mapping:
        # if the value in the dict is a string, the key is the term
        if isinstance(mapping[kid], str):
            path = mapping[kid].split('.')
            source_ts = TermSet.objects.get(iri=source.iri)

            try:
                source_ts = __traverse_path(source_ts, path)
            except Exception:
                # if one of the child term sets doesn't exist, log and
                # skip to the next mapping
                logger.info(f"Source Term Set {mapping[kid]} does not exist")
                continue

            source_name = path[-1]
            target_name = kid

            # verify terms exist
            if not target.terms.filter(name=target_name).exists():
                logger.info(f"Target Term {target_name} does not exist")
                continue
            if not source_ts.terms.filter(name=source_name).exists():
                logger.info(f"Source Term {source_name} does not exist")
                continue

            # get the terms
            source_term = source_ts.terms.get(name=source_name)
            target_term = target.terms.get(name=target_name)

            # add the term connection
            target_term.mapping.add(source_term)
            target_term.save()

        # if kid is not a child of target, log and skip to next mapping
        elif not target.children.filter(name=kid).exists():
            logger.info(
                f"Target Term Set {kid} does not exist in {target.iri}")
            continue

        # else the key is a child term set
        else:
            termset_map(target.children.get(
                name=kid), source, mapping[kid])


def __traverse_path(termset, path):
    """helper function to traverse the source term sets"""
    for step in path[:-1]:
        termset = termset.children.get(
            name=step)
    return termset
