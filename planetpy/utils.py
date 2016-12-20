import datetime as dt
import gdal

nasa_date_format = '%Y-%j'
nasa_dt_format = nasa_date_format + 'T%H:%M:%S'
nasa_dt_format_with_ms = nasa_dt_format + '.%f'
standard_date_format = '%Y-%m-%d'
standard_dt_format = standard_date_format + 'T%H:%M:%S'


def nasa_date_to_iso(datestr):
    date = dt.datetime.strptime(datestr, nasa_date_format)
    return date.isoformat()


def iso_to_nasa_date(datestr):
    date = dt.datetime.strptime(datestr, standard_date_format)
    return date.strftime(nasa_date_format)


def nasa_datetime_to_iso(dtimestr):
    if dtimestr.split('.')[1]:
        tformat = nasa_dt_format_with_ms
    else:
        tformat = nasa_dt_format
    time = dt.datetime.strptime(dtimestr, tformat)
    return time.isoformat()


def iso_to_nasa_datetime(dtimestr):
    date = dt.datetime.strptime(dtimestr, standard_dt_format)
    return date.strftime(nasa_dt_format)


def get_center_coords(imgpath):
    ds = gdal.Open(str(imgpath))
    xmean = ds.RasterXSize // 2
    ymean = ds.RasterYSize // 2
    return xmean, ymean
