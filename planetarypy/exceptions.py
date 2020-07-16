class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class SomethingNotSetError(Error):
    """Exception raised for errors in the input of transformations.

    Attributes:
        where -- where is something missing
        what     -- what is missing
    """

    def __init__(self, where, what):
        self.where = where
        self.what = what

    def __str__(self):
        return "{0} not set in {1}".format(self.what, self.where)


class ProjectionNotSetError(SomethingNotSetError):
    what = 'Projection'


class GeoTransformNotSetError(SomethingNotSetError):
    what = 'GeoTransform'


class KMASpiceError(Exception):
    """Base class for exceptions in this module."""
    pass


class SPointNotSetError(KMASpiceError):
    def __str__(self):
        return """You are trying to use a method that requires that the surface
point is defined. The class member is <spoint>. It can be set using the method
'set_spoint_by'. This operation had no effect."""


class ObserverNotSetError(KMASpiceError):
    def __str__(self):
        return """The method you called requires an observer to be set.
                  This operation had no effect."""


#
