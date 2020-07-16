from string import Template

import pandas as pd


class CTXIndex:
    volumes_url = "https://pds-imaging.jpl.nasa.gov/volumes/mro.html"
    release_url_template = Template(
        "https://pds-imaging.jpl.nasa.gov/volumes/mro/release${release}.html"
    )
    volume_url_template = Template(
        "https://pds-imaging.jpl.nasa.gov/data/mro/mars_reconnaissance_orbiter/ctx/mrox_${volume}/"
    )

    @property
    def web_tables_list(self):
        print("Scraping volumes page ...")
        return pd.read_html(self.volumes_url)

    @property
    def release_number(self):
        l = self.web_tables_list
        # The last item of last table looks like "Release XX"
        return l[-1].iloc[-1, 0].split()[-1]

    @property
    def release_url(self):
        return self.release_url_template.substitute(release=self.release_number)

    @property
    def latest_volume_url(self):
        print("Scraping latest release page ...")
        l = pd.read_html(self.release_url)
        # get last row of 4th table
        row = l[3].iloc[-1]
        number = None
        # first number that is NAN breaks the loop over last row of table
        for elem in row.values:
            try:
                number = int(elem.split()[-1])
            except AttributeError:
                break
        return self.volume_url_template.substitute(volume=number)

    @property
    def latest_index_label_url(self):
        return self.latest_volume_url + "index/cumindex.lbl"
