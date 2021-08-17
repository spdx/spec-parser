id_metadata_prefix = 'https://spdx.org/rdf/'

valid_metadata_key = ['name', 'SubclassOf',
                      'Nature', 'Range', 'Instantiability', 'Status']
valid_dataprop_key = ['type', 'minCount', 'maxCount']

metadata_defaults = {'Instantiability': ['Concrete'], 'Status': ['Stable']}
property_defaults = {'minCount': ['0'], 'maxCount': ['*']}
