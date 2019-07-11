from datetime import datetime as dt

from astropy.time import Time

from .general import SPICEFTP


def casdate2dt(casdate):
    """Convert YYDOY or YYMMDD to datetime object.

    Parameters
    ----------
    casdate : str
        Cassini SPICE datestring in form of YYDOY or YYMMDD.
        Difference is determined by length

    Returns
    -------
    datetime object for YYDOY
    """
    casdate = str(casdate)
    if len(casdate) == 5:
        return dt.strptime(casdate, "%y%j")
    elif len(casdate) == 6:
        return dt.strptime(casdate, "%y%m%d")
    else:
        raise ValueError("Don't know what to do with len(casdate) not in (5,6).")


def tstr2casdate(tstr):
    t = Time(tstr)
    return t.datetime.strftime("%y%j")


class SPICE_FNAME:
    def __init__(self, fname):
        self.fname = fname
        self.tokens, *self.ext = fname.split('.')
        self.tokens = self.tokens.split('_')


class CK_FNAME(SPICE_FNAME):
    "Manage Cassini CK SPICE kernels."
    @property
    def is_len5(self):
        return len(self.tokens[0]) == 5

    @property
    def is_len6(self):
        return len(self.tokens[0]) == 6

    @property
    def is_token0_numeric(self):
        return self.tokens[0].isnumeric()

    @property
    def is_old_style(self):
        if self.is_special:
            raise TypeError("Cannot determine style for special files.")
        return True if self.is_len6 else False

    @property
    def is_special(self):
        status = False
        # too few or too many items in filename
        if self.n_tokens < 2 or self.n_tokens > 3:
            status = True
        # first part not a date
        if not self.is_token0_numeric:
            status = True
        # no type descriptor
        if self.type not in ('r', 'p', 'c'):
            status = True
        return status

    @property
    def n_tokens(self):
        return len(self.tokens)

    @property
    def start_date(self):
        try:
            return casdate2dt(self.tokens[0])
        except:
            self.start_not_numeric = True

    @property
    def end_date(self):
        return casdate2dt(self.tokens[1][:5])

    @property
    def type_index(self):
        return 6 if self.is_len6 else 5

    @property
    def type(self):
        try:
            type_char = self.tokens[1][self.type_index]
        except IndexError:
            return None
        else:
            return type_char

    @property
    def version(self):
        ind = self.type_index + 1
        return self.tokens[1][ind]


class SPK_FNAME(SPICE_FNAME):
    "Manage Cassini SPK SPICE kernels."
    # separation date between old and new style
    sep_date = Time("2003-05-01")

    descr = dict(
        SK='orbiter S/C trajectory',
        OPK='orbiter and probe trajectory',
        PE='planetary ephemeris SPK',
        SE='major satellite ephemeris SPK',
    )

    def __init__(self, *args):
        super().__init__(*args)
        self._is_special = False
        self.evaluate_special()
        self.set_delivery_date()

    @property
    def is_special(self):
        return self._is_special

    def evaluate_special(self):
        if len(self.tokens[0]) < 6 or \
          self.tokens[0].startswith('de') or\
          self.tokens[0].startswith('sat'):
            self._is_special = True

    @property
    def is_old_style(self):
        return self.delivery_date < self.sep_date

    def set_delivery_date(self):
        try:
            self._delivery_date = casdate2dt(self.tokens[0][:6])
        except ValueError:
            self._is_special = True
            self._delivery_date = None

    @property
    def delivery_date(self):
        return self._delivery_date

    @property
    def version(self):
        char = self.fname[6]
        if char == '_':
            return 'none'
        elif char.upper() in ['P', 'R']:
            return 'none'
        else:
            return char.upper()

    @property
    def type(self):
        char = self.fname[6]
        if char.upper() in ['P', 'R']:
            return char
        else:
            return 'none'

    @property
    def description(self):
        return self.tokens[1]

    @property
    def long_description(self):
        if self.is_old_style is True:
            return self.decode_old_description()
        else:
            return self.decode_new_description()

    @property
    def start_event(self):
        if self.is_old_style is True:
            return SPK_FNAME.decode_old_event(self.tokens[2])
        else:
            return SPK_FNAME.decode_new_event(self.tokens[2])

    @staticmethod
    def decode_new_event(token):
        return casdate2dt(token)

    @staticmethod
    def decode_old_event(token):
        result = []
        field1 = dict(L='Launch', V1='Venus 1', V2='Venus 2', E='Earth', J='Jupiter',
                      S='Saturn')
        field2 = dict(P='after swingby', M='before swingby')
        for key in field1.keys():
            if token.startswith(key):
                result.append(field1[key])
                token = token[len(key):]
        result.append(field2[token[0]])
        token = token[1:]
        n_days = int(token)
        result.append(f"{n_days} days")
        return result

    @property
    def end_event(self):
        if self.is_old_style:
            return SPK_FNAME.decode_old_event(self.tokens[3])
        else:
            return SPK_FNAME.decode_new_event(self.tokens[3])

    def decode_old_description(self):
        return self.descr[self.description]

    def decode_new_description(self):
        d = self.desc.copy()
        d2 = dict(
            RE='minor satellite ephemeris SPK',
            IRRE='outer irregular satellite ephemeris SPK',
            SCPSE='merged S/C, Planetary and Satellite Ephemerides'
        )
        d.update(d2)
        return d[self.description] + ' file'


class CASSINI_KERNEL(SPICEFTP):
    """Mother class to retrieve CASSINI SPICE kernels.

    Can be used via daugher classes definining the sub_dir or
    via argument `kernel_dir` at object instantiation.

    Parameters
    ----------
    kernel_dir : str
        String indicating the kernel kind for which the
    """
    # used in super().__init__()
    root = 'pub/naif/CASSINI/kernels/'

    def __init__(self, kernel_dir=None):
        if kernel_dir is not None:
            # define here so that super() has it available.
            self.kernel_dir = kernel_dir
        super().__init__()


change_dates = dict(ck=Time("2003-11-6"),
                    spk=SPK_FNAME.sep_date)


class SEARCH:
    def __init__(self, kerneltype):
        self.kerneltype = kerneltype


class CKSEARCH:

    change_date = Time("2003-11-6")

    def __init__(self, timestr, fnames):
        self.target = Time(timestr)
        self.fnames = fnames
        self.sort_fnames()

    def sort_fnames(self):
        "Sort filenames in old, new, and special formats."
        self.old = []
        self.new = []
        self.special = []

        for fname in self.fnames:
            if fname.endswith('.lbl'):
                continue
            ckfname = CK_FNAME(fname)
            if ckfname.is_special:
                bucket = self.special
            elif ckfname.is_old_style:
                bucket = self.old
            else:
                bucket = self.new
            bucket.append(fname)

    def search_target(self):
        target = self.target
        to_search = self.old if target < self.change_date else self.new
        hits = []
        for fname in to_search:
            ckfname = CK_FNAME(fname)
            if ckfname.start_date <= target and ckfname.end_date >= target:
                hits.append(fname)
        return hits


def spksearch(timestr, fnames):
    t = Time(timestr)
    want_old = t < change_dates['spk']
    hits = []
    for fname in fnames:
        if fname.endswith('.lbl') or fname.startswith('aaread'):
            continue

        spkfname = SPK_FNAME(fname)
        if spkfname.is_special:
            continue
        if spkfname.description in ['PE', 'SE', 'RE', 'OPK', 'IRRE']:
            continue
        if spkfname.is_old_style == want_old:
            if spkfname.start_event <= t and spkfname.end_event >= t:
                hits.append(fname)

    return hits


def find_highest_version(fnames):
    version = '0'
    best_fname = ''
    for fname in fnames:
        ckfname = CK_FNAME(fname)
        if ckfname.type == 'r':
            return fname
        if ckfname.version > version:
            version = ckfname.version
            best_fname = fname
    return best_fname
