import bleach


def sort_version(sort_list, reverse_order=False):
    """
    Sort a list of Terms or TermSet by version number
    """
    sort_list.sort(key=lambda item: int(item.version.split('.')
                   [2]), reverse=reverse_order)
    sort_list.sort(key=lambda item: int(item.version.split('.')
                   [1]), reverse=reverse_order)
    sort_list.sort(key=lambda item: int(item.version.split('.')
                   [0]), reverse=reverse_order)
    return sort_list


def bleach_data_to_json(rdata):
    """Recursive function to bleach/clean HTML tags from string
    data and return dictionary data.

    :param rdata: dictionary to clean.
    WARNING rdata will be edited
    :return: dict"""

    # iterate over dict
    for key in rdata:
        # if string, clean
        if isinstance(rdata[key], str):
            rdata[key] = bleach.clean(rdata[key], tags={}, strip=True)
        # if dict, enter dict
        if isinstance(rdata[key], dict):
            rdata[key] = bleach_data_to_json(rdata[key])

    return rdata
