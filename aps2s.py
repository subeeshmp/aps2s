
import argparse
import inspect
import logging
from pathlib import Path

import xarray as xr 
import xesmf as xe

import numpy as np
import matplotlib.pyplot as plt
import f90nml
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.colors as mcolors


class AutoCLI(object):
    """Keeps track of registered functions."""

    def __init__(self):

        # Create a logger for this CLI
        self.logger = logging.getLogger(str(self))

        # By default print warnings to standard-output
        self.logger.stream_handler = logging.StreamHandler()
        self.logger.stream_handler.setLevel(logging.WARNING)
        self.logger.log_formatter = logging.Formatter(
            "%(levelname)5s:%(filename)s:%(lineno)d:%(name)s - %(message)s"
        )
        self.logger.stream_handler.setFormatter(self.logger.log_formatter)
        self.logger.addHandler(self.logger.stream_handler)

        # Instantiate a dict to store registered commands
        self.commands = {}

        # Instantiate the main parser for the CLI
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # Allow debugging level to be set
        self.parser.add_argument(
            "--log-level", dest="log_level", metavar="LEVEL",
            choices=[
                "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
            ],
            help="Set the logging level"
        )

        # Specifies whether or not the return value of the executed function should be printed
        self.parser.add_argument(
            "--return-output", dest="return_output", action='store_true',
            help="Print the returned value of the executed function"
        )

        # Allow logging to a file instead of to the console
        self.parser.add_argument(
            "--log-file", dest="log_file", metavar="LOGFILE",
            help="Write logs to a file instead of to the console"
        )

        # Customize help message (replace "positional arguments header")
        self.parser._positionals.title = "Subcommands"

        # Add support for subparsers (customize layout using metavar)
        self.subparsers = self.parser.add_subparsers(
            help="Description",
            dest="subcommand_name",
            metavar="<command>",
            required=True,
        )

    def run(self):
        """Parse the command-line and execute the given command."""

        # Parse the command-line
        args = self.parser.parse_args()

        # Set log level
        if(args.log_level):
            self.logger.setLevel(args.log_level)

        # Set log file
        if(args.log_file):
            self.logger.file_handler = logging.FileHandler(args.log_file)
            self.logger.file_handler.setFormatter(self.logger.log_formatter)
            self.logger.addHandler(self.logger.file_handler)
            self.logger.file_handler.setLevel(logging.NOTSET)
        else:
            self.logger.stream_handler.setLevel(logging.NOTSET)

        # Convert the Namespace object to a dictionary
        arg_dict = vars(args)

        # Extract the subcommand name
        subcommand_name = args.subcommand_name

        # Convert hyphens/dashes to underscores
        # subcommand_name = subcommand_name.replace('-', '_')

        # Get the corresponding function object
        _function = self.commands[subcommand_name]

        # Get the argument specification object of the function
        argspec = inspect.signature(_function)

        # Extract the arguments for the subcommand
        # NOTE: Convert hyphens/dashes to underscores
        # NOTE: Superfluous arguments are ignored!
        relevant_args = {
            key: arg_dict[key]
            for key in arg_dict
            if key in argspec.parameters
        }

        # Log some output
        self.logger.debug("Executing function: %s" % self.commands[subcommand_name])

        # Execute the command
        return_value = self.commands[subcommand_name](**relevant_args)

        # If desired, print the canonical representation of the return value
        if args.return_output:
            print(return_value.__repr__())

    def register_command(self, _function):
        """A function to register a function as cli command 
        """
        # Make sure _function is a function 
        assert(inspect.isfunction(_function))

        # Get command name and convert underscores to hyphens/dashes
        command_name = _function.__name__

        # Get the help message from the doc-string if the doc-string exists
        help_string = inspect.getdoc(_function)
        if not help_string:
            help_string = ""

        # Add a subparser corresponding to the given function
        subparser = self.subparsers.add_parser(
            command_name,
            help=help_string,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        argspec = inspect.signature(_function)

        # Ensure that args are a list
        # (i.e. handle case where no arguments are given)
        parameters = argspec.parameters 

        # Add the positional function parameter to the subparsers
        for name, parameter in parameters.items():
            arg_type = parameter.annotation if parameter.annotation is not parameter.empty else None
            default = None
            parameter_name = parameter.name
            if parameter.default is not parameter.empty:
                parameter_name = '--'+parameter.name
                default = parameter.default

            subparser.add_argument(parameter_name, default=default, help=' ', type=arg_type)

        # Register the function with the CLI
        self.commands[command_name] = _function


def plot_bathy(lat, lon, z):
    ax = plt.axes(projection=ccrs.PlateCarree())
    levels = list(np.linspace(-3000,-200,10))[:-1] + list(np.linspace(-200,0,21))
    levels = [ -0.0000001 if item == 0.0 else item for item in levels ]

    cmap=plt.cm.jet
    norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

    cs=ax.contourf(lon,lat,z,levels=levels,cmap=cmap,norm=norm,transform=ccrs.PlateCarree(),extend='max')
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False

    plt.colorbar(cs)

    plt.savefig('bathymetry.png')


def make_bathy(wrf_geo:str,input_bathy:str):
    """Create bathymetry file for MITGCM"""

    ds_geo = xr.open_dataset(wrf_geo)
    ds_input_bathy = xr.open_dataset(input_bathy)
    input_bathy = ds_input_bathy['z']

    XLAT_M = ds_geo['XLAT_M'][0,:,0]
    XLONG_M = ds_geo['XLONG_M'][0,0,:]

    print(XLAT_M.values)
    print(XLONG_M.values)

    grid_out = xr.Dataset(
        {
            "lat": (["lat"], XLAT_M.values, {"units": "degrees_north"}),
            "lon": (["lon"], XLONG_M.values, {"units": "degrees_east"}),
        }
    )
    regridder = xe.Regridder(ds_input_bathy, grid_out, "conservative")

    dr_out = regridder(input_bathy, keep_attrs=True)

    dr_out.to_netcdf('test.nc')

    plot_bathy(XLAT_M, XLONG_M, dr_out)


if __name__=="__main__":
    cli = AutoCLI()
    cli.register_command(make_bathy)
    cli.run()


