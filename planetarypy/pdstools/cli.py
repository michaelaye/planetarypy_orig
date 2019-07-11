import click
from .indices import fix_hirise_edrcumindex
from . import indices

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
def greet():
    pass


@greet.command()
@click.argument('infile', type=click.Path(exists=True))
@click.argument('outfile', type=click.Path())
def fix_hirise_index(infile, outfile):
    """Tool to fix HiRISE EDRCUMINDEX bug.

    Reads INFILE and creates OUTFILE.
    """
    fix_hirise_edrcumindex(infile, outfile)
    print(infile)
    print(outfile)

@greet.command()
def list_available():
    """List the indices available for download.
    
    A list is printed that shows which index locations have been
    implemented with their URLs for downloading.
    """
    indices.list_available_index_files()

@greet.command()
def testing(**kwargs):
    print("Just testing")


if __name__ == '__main__':
    greet()
