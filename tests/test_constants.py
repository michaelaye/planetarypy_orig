from planetpy import constants

def test_constants():
    mars_escape_velocity = 5.0
    eps = 1e-5
    assert abs(mars_escape_velocity - constants.mars.escape_velocity) < eps
