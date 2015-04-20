from . import factsheet_parse as fp


# Create a pretty table
planets_pretty = fp.parse_NASA_factsheet()

# Create the programmatic version with index having
# no units, all lowercase and spaces removed
planets = fp.get_programmatic_dataframe()

# create planet versions that just refer to the columns of the `planets` object
mercury = planets.loc['MERCURY']
venus = planets.loc['VENUS']
earth = planets.loc['EARTH']
mars = planets.loc['MARS']
jupiter = planets.loc['JUPITER']
saturn = planets.loc['SATURN']
neptune = planets.loc['NEPTUNE']
uranus = planets.loc['URANUS']
