from pathlib import Path
from ftplib import FTP


class SPICEFTP:
    local_dir = Path('/Volumes/USB128II/spice/UVIS_data/kernels')
    url = 'naif.jpl.nasa.gov'

    def __init__(self):
        ftp = FTP(self.url)   # connect to host, default port
        ftp.login()            # user anonymous, passwd anonymous@
        folder = self.root + self.kernel_dir
        ftp.cwd(folder)
        self.ftp = ftp

    @property
    def filenames(self):
        return self.ftp.nlst()

    def close(self):
        self.ftp.close()

    @property
    def readme(self):
        return self.ftp.retrlines('RETR aareadme.txt')

    def __del__(self):
        self.ftp.close()

    def get_file(self, remote_name, local_name=None):
        if local_name is None:
            local_name = remote_name
        local_path = str(self.local_dir / Path(self.kernel_dir) / local_name)
        self.ftp.retrbinary(f"RETR {remote_name}", open(f"{local_path}", "wb").write)
