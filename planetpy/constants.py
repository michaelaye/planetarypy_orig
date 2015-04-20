import pandas as pd
import numpy as np

all_planets_url = 'http://nssdc.gsfc.nasa.gov/planetary/factsheet/'


def parse_NASA_factsheet():
    """Use pandas to parse NASA's planetary factsheet.

    The result has a human readable index which is pretty, but hard to
    access programmatically.
    """
    # parse remote URL
    df = pd.read_html(all_planets_url,
                      header=0, index_col=0)[0]

    # replace unparsed exponent units with correct form
    newindex = pd.Series(df.index).str.replace('1024', '10^24')
    newindex = newindex.str.replace('106', '10^6')
    df.index = newindex

    # parse Yes/No/Unknown and set to True/False/NaN
    def convert_element(el):
        el = el.strip()
        if el == 'Yes':
            return True
        elif el == 'No':
            return False
        elif 'Unknown' in el:
            return np.NaN
        else:
            return el

    df = df.applymap(convert_element)

    # Convert all datatypes to float
    df = df.convert_objects(convert_numeric=True)

    # Drop the last line of headers without any data
    df = df.dropna(how='all')

    return df


def get_pretty_factsheet():
    return parse_NASA_factsheet()


def get_programmable_index(df):
    """Create a better index for programmatic use.

    The original parse creates pretty but harder to use indices. This function
    removes the units from the index and unifies it to lower case.
    """
    attributes = pd.Series(df.index)

    def map_pretty_index_to_attribute(index):
        first_token = index.split('(')[0].strip().lower()
        new_attr = '_'.join(first_token.split(' '))
        if new_attr.startswith('ring_system'):
            new_attr = 'is_ring_system'
        elif new_attr.startswith('global_magnetic'):
            new_attr = 'has_global_magnetic_field'
        return new_attr

    return attributes.map(map_pretty_index_to_attribute)


planets_pretty = parse_NASA_factsheet()
planets = planets_pretty.copy()
planets.index = get_programmable_index(planets)

mercury = planets.MERCURY
venus = planets.VENUS
earth = planets.EARTH
mars = planets.MARS
jupiter = planets.JUPITER
saturn = planets.SATURN
neptune = planets.NEPTUNE
uranus = planets.URANUS
