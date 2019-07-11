import pandas as pd
import numpy as np

all_planets_url = 'http://nssdc.gsfc.nasa.gov/planetary/factsheet/'


def grep_url_data():
    # parse remote URL
    df = pd.read_html(all_planets_url,
                      header=0, index_col=0)[0]
    # returning transform because planets on the index make more sense.
    # They are, in a way, another set of mesasurements for the given
    # parameters
    # Also, drop the last line that just has planet names
    return df.T.loc[:, df.T.columns[:-1]]


def parse_NASA_factsheet():
    """Use pandas to parse NASA's planetary factsheet.

    The result has a human readable index which is pretty, but hard to
    access programmatically.
    """
    df = grep_url_data()

    # replace unparsed exponent units with correct form
    newcols = pd.Series(df.columns).str.replace('1024', '10^24')
    newcols = newcols.str.replace('106', '10^6')
    df.columns = newcols

    # parse Yes/No/Unknown and set to True/False/NaN
    def convert_element(el):
        el = str(el).strip(' *')
        if el == 'Yes':
            return 1.0
        elif el == 'No':
            return 0.0
        elif 'Unknown' in el:
            return np.NaN
        else:
            return el

    df = df.applymap(convert_element)

    # Convert data types to their correct dtypes
    df = df.convert_objects(convert_numeric=True)

    return df


def get_programmable_columns(df):
    """Create a better index for programmatic use.

    The original parse creates pretty but harder to use indices. This function
    removes the units from the index and unifies it to lower case.
    """
    attributes = pd.Series(df.columns)

    def map_pretty_index_to_attribute(index):
        first_token = index.split('(')[0].strip().lower()
        new_attr = '_'.join(first_token.split(' '))
        if new_attr.startswith('ring_system'):
            new_attr = 'is_ring_system'
        elif new_attr.startswith('global_magnetic'):
            new_attr = 'has_global_magnetic_field'
        return new_attr

    return attributes.map(map_pretty_index_to_attribute)


def get_programmatic_dataframe():
    df = parse_NASA_factsheet()

    df.columns = get_programmable_columns(df)
    return df
