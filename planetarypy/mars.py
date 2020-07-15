# encoding: utf-8
"""
Some tools to work with Mars data.
Abbreviations:
ul = Upper Left
lr = LowerRight

Copyright (c) 2011 Klaus-Michael Aye. All rights reserved.
"""

from osgeo import gdal, osr
import sys
import os
from matplotlib.pyplot import figure, show
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import numpy as np
from math import atan2, degrees
from .exceptions import *

gdal.UseExceptions()


def calculate_image_azimuth(origPoint, newPoint, zero="right"):
    """Calculate azimuth angle between 2 image points.

    Parameters
    ==========
    origPoint, newPoint: <mars.Point> objects
    zero: <string>
        right' or 'top' to indicate where zero is.

    Returns
    =======
    azimuth: <float> azimuth angle
    """
    deltaSample = newPoint.sample - origPoint.sample
    deltaLine = newPoint.line - origPoint.line

    azimuth = degrees(atan2(deltaLine, deltaSample))

    if azimuth < 0.0:
        azimuth += 360.0
    if azimuth > 360.0:
        azimuth -= 360.0
    if zero == "top":
        azimuth += 90.0
        if azimuth > 360.0:
            azimuth -= 360.0

    return azimuth


def debug_srs(projection):
    """Correct wrong scale_factor in PolarStereographic data.

    Some PolarStereographic data have a 0 as a scale_factor in the
    projection (mostly MOLA), which is being corrected here.
    TODO: Check for being PolarStereographic before doing this!
    """
    srs = osr.SpatialReference(projection)
    if int(srs.GetProjParm("scale_factor")) == 0:
        srs.SetProjParm("scale_factor", 1)
    return srs


def shift_to_center(x, y, geotransform):
    # if i'd shift, the centerpoint does not show center coordinates
    # so that seems wrong. am i overlooking something?
    x += geotransform[1] / 2.0
    y += geotransform[5] / 2.0
    return x, y


def pixel_to_meter(sample, line, geotransform, shift=False):
    """provide point in map projection coordinates.

    Parameters
    ==========
    sample, line: <integer> Sample and line of an image in pixel coords
    Geotransform in format as given by GDAL datasets.GetGeoTransform()

    Returns
    =======
    tuple (x,y) coordinates in the projection of the dataset

    TODO: Shift had a problem. Write test to confirm what and fix.
    FIXME above
    """
    x, y = gdal.ApplyGeoTransform(geotransform, sample, line)
    if shift:
        x, y = shift_to_center(x, y, geotransform)
    return (x, y)


class Point(object):
    """Point class to manage pixel and map points and their transformations.

    Parameters
    ==========
    Either:
    sample, line: pixel coordinates
    or
    x, y: projection coordinates (km or m)
    or
    lon, lat: geographical coordinates in degrees

    Requires
    ========
    gdal to enable sample/line<-> map coords tra'fo's

    >>> p = Point(0,1)

    Need a dataset to try, so I get a MOLA dataset:
    >>> mola = MOLA()
    >>> '%4.2f, %4.2f' % p.pixel_to_meter(mola.dataset.GetGeoTransform())
    '-707109.70, 706994.61'
    >>> p = Point(x=0,y=1)
    >>> '%4.2f, %4.2f' % p.meter_to_pixel(mola.dataset.GetGeoTransform())
    '6144.00, 6143.99'
    >>> p2 = Point(x=3,y=3)
    >>> newP = p + p2
    >>> print(newP.x, newP.y)
    3 4
    """

    def __init__(
        self,
        sample=None,
        line=None,
        x=None,
        y=None,
        lon=None,
        lat=None,
        geotrans=None,
        proj=None,
    ):
        self.sample = sample
        self.line = line
        self.x = x
        self.y = y
        self.lat = lat
        self.lon = lon
        self.centered = False
        self.geotrans = geotrans
        self.proj = proj
        if geotrans is not None:
            if sample is not None:
                self.pixel_to_meter()
            elif x is not None:
                self.meter_to_pixel()
            if proj is not None:
                if sample is not None:
                    self.pixel_to_lonlat()
                elif x is not None:
                    self.lonlat_to_meter()

    @property
    def pixels(self):
        return np.array([self.sample, self.line])

    @property
    def coords(self):
        return np.array([self.x, self.y])

    @property
    def lonlats(self):
        return np.array([self.lon, self.lat])

    def shift_to_center(self, geotransform):
        # if i'd shift, the centerpoint does not show center coordinates
        # so that seems wrong. am i overlooking something?
        # self.x += geotransform[1] / 2.0
        # self.y += geotransform[5] / 2.0
        # self.centered = True
        pass

    def __add__(self, other):
        newPoint = Point(0, 0)
        if all([coord is not None for coord in [self.sample, other.sample]]):
            newPoint.sample = self.sample + other.sample
            newPoint.line = self.line + other.line
        if all([coord is not None for coord in [self.x, other.x]]):
            newPoint.x = self.x + other.x
            newPoint.y = self.y + other.y
        if all([coord is not None for coord in [self.lat, other.lat]]):
            newPoint.lat = self.lat + other.lat
            newPoint.lon = self.lon + other.lon
        return newPoint

    def __call__(self):
        print("Pixel: ({0},{1})".format(self.sample, self.line))
        print("Map: ({0},{1})".format(self.x, self.y))
        print("Geo: ({0},{1})".format(self.lon, self.lat))

    def pixel_to_meter(self, geotransform=None, shift_to_center=False):
        """provide point in map projection coordinates.

        Parameters
        ==========
        Geotransform in format as given by GDAL datasets.GetGeoTransform()
        If none is provided, the method uses the one given at object creation
        and throws an error if none was given at that time either.
        If a geotransform has been provided, it is copied into the
        object.

        Returns
        =======
        tuple (x,y) coordinates in the projection of the dataset

        >>> p = Point(0,0)
        >>> mola = MOLA()
        >>> '%6.2f, '*2 % p.pixel_to_meter(mola.dataset.GetGeoTransform())
        '-707109.70, 707109.70, '
        """
        # if not given as parameter, take it from self
        if geotransform is None:
            geotransform = self.geotrans
        else:
            # otherwise copy call parameter to self
            self.geotrans = geotransform
        # if it's still None
        if geotransform is None:
            # raise Error, abort method
            raise ProjectionNotSetError("pixel_to_meter")
        if self.sample is None:
            raise SomethingNotSetError("pixel_to_meter", "'sample'")
        self.x, self.y = pixel_to_meter(self.sample, self.line, geotransform)
        return (self.x, self.y)

    def meter_to_pixel(self, geotransform=None):
        """provide pixel coords from x,y coords.

        Input: gdal Dataset
        Return: list [line,sample] of the dataset for given coordinate
        >>> p = Point(x=5e5, y=6e5)
        >>> mola = MOLA()
        >>> '%6.2f ,'*2 % p.meter_to_pixel(mola.dataset.GetGeoTransform())
        '10488.45 ,930.66 ,'
        """
        if (self.x is None) or (self.y is None):
            raise SomethingNotSetError(
                (self.x, self.y), "Map coordinates not " "set for transformation."
            )
        success, tInverse = gdal.InvGeoTransform(geotransform)
        self.sample, self.line = gdal.ApplyGeoTransform(tInverse, self.x, self.y)
        return (self.sample, self.line)

    def pixel_to_lonlat(self, geotransform=None, projection=None):
        self.pixel_to_meter(geotransform)
        self.meter_to_lonlat(projection)
        return (self.lon, self.lat)

    def lonlat_to_pixel(self, geotransform=None, projection=None):
        self.lonlat_to_meter(projection)
        self.meter_to_pixel(geotransform)
        return (self.sample, self.line)

    def meter_to_lonlat(self, projection=None):
        if projection is None:
            projection = self.proj
        if projection is None:
            raise ProjectionNotSetError("lonlat_to_meter")
        srs = debug_srs(projection)
        ct = osr.CoordinateTransformation(srs, srs.CloneGeogCS())
        self.lon, self.lat, height = ct.TransformPoint(self.x, self.y)
        if self.lon < 0:
            self.lon = 360.0 - abs(self.lon)
        return (self.lon, self.lat)

    def lonlat_to_meter(self, projection=None):
        if projection is None:
            projection = self.proj
        if projection is None:
            raise ProjectionNotSetError("lonlat_to_meter")
        srs = debug_srs(projection)
        ct = osr.CoordinateTransformation(srs.CloneGeogCS(), srs)
        # height not used so far!
        self.x, self.y, height = ct.TransformPoint(self.lon, self.lat)
        return (self.x, self.y)

    def calculate_azimuth(self, p2, zero="right"):
        return calculate_image_azimuth(self, p2, zero=zero)


class Window(object):
    """class to manage a window made of corner Points (objects of Point())

    when using width, only quadratic windows supported currently
    >>> p1 = Point(0, 1)
    >>> p2 = Point(10,20)
    """

    def __init__(self, ulPoint=None, lrPoint=None, centerPoint=None, width=None):
        if not any([lrPoint, centerPoint, width]):
            self.usage()
        else:
            self.ul = ulPoint
            self.lr = lrPoint
            self.center = centerPoint
        self.width = width
        if not (ulPoint and lrPoint):
            if centerPoint and width:
                self.get_corners_from_center()
            elif ulPoint and width:
                self.get_lr_from_width()
            else:
                print(
                    "Either upper left and lower right or upper left/"
                    " centerPoint with width needs to be provided."
                )
                return

    def copy(self):
        win = Window(
            Point(
                self.ul.sample,
                self.ul.line,
                x=self.ul.x,
                y=self.ul.y,
                lon=self.ul.lon,
                lat=self.ul.lat,
            ),
            Point(
                self.lr.sample,
                self.lr.line,
                x=self.lr.x,
                y=self.lr.y,
                lon=self.lr.lon,
                lat=self.lr.lat,
            ),
        )
        return win

    def __call__(self):
        return self.ul(), self.lr(), self.width, self.center()

    def get_lr_from_width(self):
        lrSample = self.ul.sample + self.width
        lrLine = self.ul.line + self.width
        self.lr = Point(lrSample, lrLine)
        return self.lr

    def usage(self):
        print(
            """Usage: win = Window(pointObject1, pointObject2)
        or
        win = Window(pointObject1, width_in_Pixel)
        or
        win = Window(centerPoint, width_in_Pixel)"""
        )
        return

    def get_corners_from_center(self):
        """Create symmetric window around given center point.

        Create symmetric window around given sample/line point and return
        to Point objects for each corner point of the window
        >>> win = Window(centerPoint=Point(100,100),width=50)
        >>> win.ul.sample, win.ul.line, win.lr.sample, win.lr.line
        (75, 75, 125, 125)
        """
        ulSample = self.center.sample - self.width // 2
        ulLine = self.center.line - self.width // 2
        self.ul = Point(ulSample, ulLine)
        lrSample = self.center.sample + self.width // 2
        lrLine = self.center.line + self.width // 2
        self.lr = Point(lrSample, lrLine)
        return (self.ul, self.lr)

    def get_gdal_window(self):
        """provide window pixel coordinates in gdal format.

        thats [ulSample, ulLine, samplewidth,linewidth]
        >>> win = Window(Point(10,150),Point(100,200))
        >>> win.get_gdal_window()
        [10, 150, 90, 50]
        """
        return [
            int(self.ul.sample),
            int(self.ul.line),
            int(self.lr.sample - self.ul.sample),
            int(self.lr.line - self.ul.line),
        ]

    def get_extent(self, dataset, lonlat=False):
        """provide window coordinates in matplotlib extent format

        this is needed to get the imshow image plot in the right coordinates
        the strange looking string print out for getting the extent is only
        done to make up for floating point differences that can happen when
        this code executes on other machines
        >>> win = Window(Point(10,150),Point(100,200))
        >>> mola = MOLA()
        >>> '%6.2f, '*4 % tuple(win.get_extent(mola.dataset))
        '-705958.80, -695600.75, 684091.80, 689846.28, '
        """
        if lonlat is False:
            self.ul.pixel_to_meter(dataset.GetGeoTransform())
            self.lr.pixel_to_meter(dataset.GetGeoTransform())
            return [self.ul.x, self.lr.x, self.lr.y, self.ul.y]
        elif lonlat is True:
            self.ul.pixel_to_lonlat(dataset.GetGeoTransform(), dataset.GetProjection())
            self.lr.pixel_to_lonlat(dataset.GetGeoTransform(), dataset.GetProjection())
            return [self.ul.lon, self.lr.lon, self.lr.lat, self.ul.lat]


class ImgData(object):
    """docstring for ImgData"""

    def __init__(self, fname=None):
        self.fname = fname
        self.dataset = gdal.Open(self.fname)
        self.ds = self.dataset
        self.X = self.ds.RasterXSize
        self.Y = self.ds.RasterYSize
        for i in range(self.ds.RasterCount):
            setattr(self, "band" + str(i + 1), self.ds.GetRasterBand(i + 1))
        self.band = self.band1  # keep with older interface of just 1 band
        self.geotrans = self.dataset.GetGeoTransform()
        self.projection = self.dataset.GetProjection()
        self.center = Point(
            self.X // 2, self.Y // 2, geotrans=self.geotrans, proj=self.projection
        )

    def _read_data(self, band):
        band = getattr(self, band)
        data = band.ReadAsArray(*self.window.get_gdal_window())
        ndv = band.GetNoDataValue()
        mdata = np.ma.masked_equal(data, ndv)
        self.data = data
        self.mdata = mdata

    def read_cropped_by_n(self, n):
        "return a window of n x n "
        self.data = self.ds.ReadAsArray(n, n, self.X - n, self.Y - n)

    def read_center_window(self, width=500, band="band1"):
        """Get some sample data from the center of the dataset

        Input: width of square data array, default 500
        >>> mola= MOLA()
        >>> mola.read_center_window()
        >>> mola.data.shape
        (500, 500)
        >>> mola.data.min()
        3382217.5
        >>> mola.data.max()
        3382383.8
        """
        width = min(width, self.X, self.Y)
        self.window = Window(centerPoint=self.center, width=width)
        self._read_data(band)

    def read_all(self, maxdim=1024, band="band1"):
        """This reads all data into a max_dim sized buffer.

        GDAL is doing the downsampling.
        """

        b = getattr(self, band)
        ndv = b.GetNoDataValue()
        ns = self.X
        nl = self.Y

        self.window = Window(ulPoint=Point(0, 0), lrPoint=Point(self.X, self.Y))
        # if full res is smaller than maxdim, get everything
        if (maxdim > self.X) and (maxdim > self.Y):
            data = b.ReadAsArray()
            mdata = np.ma.masked_equal(data, ndv)
        else:
            # Don't want to load the entire dataset for stats computation
            # This is maximum dimension for reduced resolution array
            max_dim = maxdim

            scale_ns = ns / max_dim
            scale_nl = nl / max_dim
            scale_max = max(scale_ns, scale_nl)

            if scale_max > 1:
                nl = round(nl / scale_max)
                ns = round(ns / scale_max)

            # The buf_size parameters determine the final array dimensions
            data = np.array(b.ReadAsArray(buf_xsize=ns, buf_ysize=nl))
            mdata = np.ma.masked_equal(data, ndv)
        self.mdata = mdata
        self.data = data
        return mdata

    def read_window(self, ul_or_win, lrPoint=None, band="band1"):
        """get data for Window object or 2 Point objects

        user can either provide one Window object or 2 Point objects as input
        Point.sample and Point.line have to be filled.
        >>> mola = MOLA()
        >>> data = mola.read_window(Point(100,200),Point(300,400))
        >>> data.shape
        (200, 200)
        >>> data.min()
        3380594.5
        >>> data.max()
        3380967.0
        >>> data = mola.read_window(Window(Point(100,200),Point(400,500)))
        >>> data.shape
        (300, 300)
        >>> data.min()
        3380329.8
        """
        if isinstance(ul_or_win, Window):
            self.window = ul_or_win
        else:
            self.window = Window(ul_or_win, lrPoint)
        self._read_data(band)
        return self.data

    def window_coords_to_meter(self):
        self.window.ul.pixel_to_meter(self.geotrans)
        self.window.lr.pixel_to_meter(self.geotrans)

    def window_coords_to_lonlat(self):
        self.window.ul.pixel_to_lonlat(self.geotrans, self.projection)
        self.window.lr.pixel_to_lonlat(self.geotrans, self.projection)

    def window_coords_to_pixel(self):
        self.window.ul.lonlat_to_pixel(self.geotrans, self.projection)
        self.window.lr.lonlat_to_pixel(self.geotrans, self.projection)

    def normalize(self):
        new_data = self.data - self.data.min()
        new_data /= new_data.max()
        self.data = new_data

    def convert_to_uint8(self):
        self.normalize()
        self.data = np.array(self.data * 256, dtype=np.uint8)
        return self.data

    def show(self, lonlat=False, cb=False):
        fig = figure()
        ax = fig.add_subplot(111)
        extent = self.window.get_extent(self.dataset, lonlat)
        im = ax.imshow(self.data, extent=extent)  # ,origin='image')
        if lonlat:
            ax.set_xlabel("Longitude [deg]")
            ax.set_ylabel("Latitude [deg]")
        else:
            ax.set_xlabel("Rectangular X [m]")
            ax.set_ylabel("Rectangular Y [m]")
        if cb:
            fig.colorbar(im)
        self.ax = ax
        show()

    def add_scalebar(self, loc=3):
        extent = self.window.get_extent(self.dataset)
        diffx = abs(extent[1] - extent[0]) * 1000
        diffy = abs(extent[3] - extent[2]) * 1000
        diff = max(diffx, diffy)
        # get closed magnitude to 10 % of image extent
        scalebarLength = 10 ** int(round(np.log10(diff / 10)))
        scalebarLength /= 1000
        d = dict(
            [
                (1, "1 km"),
                (10, "10 m"),
                (100, "100 m"),
                (1000, "1 km"),
                (10000, "10 km"),
                (100000, "100 km"),
                (1000000, "1000 km"),
            ]
        )
        asb = AnchoredSizeBar(
            self.ax.transData, scalebarLength, d[scalebarLength], loc=loc
        )
        self.ax.add_artist(asb)
        self.ax.get_figure().canvas.draw()


class MOLA(ImgData):
    """docstring for MOLA"""

    def __init__(
        self, fname=os.path.join(os.getenv("HOME"), "data/mola/megr_s_512_1.cub")
    ):
        ImgData.__init__(self, fname)


class CTX(ImgData):
    """docstring for CTX"""

    def __init__(
        self,
        fname=os.getenv("HOME") + "/data/ctx/inca_city/PSP_004226_0984/"
        "P08_004226_0984_XI_81S063W.cal.des.map.cub",
    ):
        ImgData.__init__(self, fname)

    def add_mola_contours(self):
        self.window_coords_to_lonlat()
        mola = MOLA()
        mola.window = self.window.copy()
        mola.window_coords_to_pixel()
        mola.read_window(mola.window)
        mola.data = mola.data - mola.data.mean()
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111)
        plt.gray()
        ax.imshow(self.data, extent=self.window.get_extent(self.dataset))
        CS = ax.contour(
            mola.data,
            8,
            cmap=cm.jet,
            extent=self.window.get_extent(self.dataset),
            origin="image",
        )
        plt.clabel(CS, fontsize=13, inline=1)
        ax.set_xlabel("Polar stereographic X [km]")
        ax.set_ylabel("Polar stereographic Y [km]")
        ax.set_title("CTX: " + os.path.basename(self.fname))
        self.ax = ax
        plt.show()


class HiRISE(ImgData):
    """docstring for HiRISE"""

    def __init__(
        self,
        fname=os.getenv("HOME") + "/data/hirise/inca_city/"
        "PSP_002380_0985_RED.cal.norm.map.equ.mos.cub",
    ):
        ImgData.__init__(self, fname)


# def combine_ctx_and_mola(ctxFilename, ctxSample, ctxLine, ctxWidth):
#     """combine CTX and MOLA data.
#
#     MOLA and CTX data will be combined with these tools.
#     User shall provide line,sample center coordinate of CTX file ROI to
#     define distance in meters from southpole.
#     """
#
#     ctx = CTX(ctxFilename)
#     mola = MOLA()
#     ctxULsample, ctxULline, ctxLRsample, ctxLRline = \
#         get_corners_from_center(ctxSample, ctxLine, ctxWidth)
#     ulX,ulY = get_coords_from_pixels(ctxDS, ctxULsample, ctxULline)
#     lrX,lrY = get_coords_from_pixels(ctxDS, ctxLRsample, ctxLRline)
#
#     molaULsample,molaULline = get_pixels_from_coords(molaDS,ulX,ulY)
#     molaLRsample,molaLRline = get_pixels_from_coords(molaDS,lrX,lrY)
#     print(ctxULsample, ctxULline, ctxLRsample, ctxLRline)
#     print(molaULsample, molaULline,molaLRsample, molaLRline)
#     print(ulX,ulY,lrX,lrY)
#     ctxData = ctxDS.ReadAsArray(ctxULsample,ctxULline,ctxWidth,ctxWidth)
#     molaData = molaDS.ReadAsArray(int(molaULsample)+1,int(molaULline),
#                                   int(molaLRsample - molaULsample),
#                                   int(molaLRline - molaULline))
#
#     molaData = molaData - molaData.mean()
#
#     # x = np.arange(ulX,lrX)
#     # y = np.arange(lrY,ulY)
#     # X, Y = np.meshgrid(x,y)
#     # plotting
#     fig = plt.figure(figsize=(10,10))
#     ax = fig.add_subplot(111)
#     plt.gray()
#     ax.imshow(ctxData, extent=(min(ulX,lrX),max(ulX,lrX),min(ulY,lrY),
#                                      max(ulY,lrY)))
#     CS = ax.contour(molaData, 20, cmap = cm.jet,
#                      extent=(min(ulX,lrX),
#                              max(ulX,lrX),
#                              min(ulY,lrY),
#                              max(ulY,lrY)),
#                      origin='image' )
#     plt.clabel(CS,fontsize=9, inline=1)
#     plt.show()


def main(argv=None):
    """docstring for main"""
    from enthought.mayavi import mlab

    if argv is None:
        argv = sys.argv

    x1 = x2 = y1 = y2 = 0
    fname = ""
    try:
        fname = argv[1]
        x1, x2, y1, y2 = [int(i) for i in argv[2:]]
    except:
        print("Usage: {0} fname x1 x2 y1 y2".format(argv[0]))

    print(x1, x2, y1, y2)
    ds = gdal.Open(fname)
    band = ds.GetRasterBand(1)
    STORED_VALUE = band.ReadAsArray(x1, y1, x2 - x1, y2 - y1)
    ds = 0

    # PDS label infos:
    SCALING_FACTOR = 0.25
    OFFSET = -8000
    topo = (STORED_VALUE * SCALING_FACTOR) + OFFSET
    mlab.surf(topo, warp_scale=1 / 115.0, vmin=1700)
    mlab.colorbar(orientation="vertical", title="Height [m]", label_fmt="%4.0f")
    mlab.show()


if __name__ == "__main__":
    sys.exit(main())
