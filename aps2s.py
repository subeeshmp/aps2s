#!/usr/bin/env python3
import argparse
import inspect
import logging
from pathlib import Path
from docstring_parser import parse_from_object

from utils import make_bathy, plot_bathymetry


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
            help=argparse.SUPPRESS
        )

        # Specifies whether or not the return value of the executed function should be printed
        self.parser.add_argument(
            "--return-output", dest="return_output", action='store_true',
            help=argparse.SUPPRESS
        )

        # Allow logging to a file instead of to the console
        self.parser.add_argument(
            "--log-file", dest="log_file", metavar="LOGFILE",
            help=argparse.SUPPRESS
        )

        # # Customize help message (replace "positional arguments header")
        self.parser._positionals.title = "Available sub-commands"
        # self.parser._positionals.title = ""

        # Add support for subparsers (customize layout using metavar)
        self.subparsers = self.parser.add_subparsers(
            # help="Description",
            dest="subcommand_name",
            metavar="<sub-command>",
            # required=True,
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

        print(args.log_level, args.log_file)        

        # Log some output
        self.logger.debug("Executing function: %s" % self.commands[subcommand_name])

        # Execute the command
        return_value = self.commands[subcommand_name](**relevant_args)

        # If desired, print the canonical representation of the return value
        if args.return_output:
            print(return_value.__repr__())

    def register_command(self, _function, name=None):
        """
        Register a function as cli command 
        """
        # Make sure _function is a function 
        assert(inspect.isfunction(_function))

        # Get command name and convert underscores to hyphens/dashes
        command_name = _function.__name__
        if name:
            command_name=name

        # Get the help message from the doc-string if the doc-string exists
        help_string = inspect.getdoc(_function)

        docstring = parse_from_object(_function)

        help_string = docstring.short_description
        description = f'{docstring.short_description} \n {docstring.long_description}'

        params_description = { params.arg_name: params.description for params in docstring.params }

        if not help_string:
            help_string = ""

        # Add a subparser corresponding to the given function
        subparser = self.subparsers.add_parser(
            command_name,
            help=help_string,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter
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
            metavar = f'<{parameter.name}>'
            if parameter.default is not parameter.empty:
                parameter_name = '--'+parameter.name
                default = parameter.default
            parameter_help = ' '
            if parameter.name in params_description:
                parameter_help = params_description[parameter.name]
            if default:
                parameter_help += f' (default: {default})'

            # print(parameter_name, parameter_help, default)

            subparser.add_argument(
                parameter_name, 
                default=default, 
                help=parameter_help,
                metavar=metavar,
                type=arg_type,
                )

        # Register the function with the CLI
        self.commands[command_name] = _function

def get_cli():
    cli = AutoCLI()
    cli.register_command(make_bathy, name='create_bathymetry')
    cli.register_command(plot_bathymetry)
    return cli

def get_cli_parser():
    cli = get_cli()
    return cli.parser

if __name__=="__main__":
    cli = get_cli()
    cli.run()

