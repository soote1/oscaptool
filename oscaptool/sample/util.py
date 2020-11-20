import os
import logging
import argparse

SUBPARSERS = 'subparsers'
REQUIRED = 'required'
ID = 'id'
SUBPARSERS_CFGS = 'subparsers_cfgs'
NAME = 'name'
HELP = 'help'
ARGS = 'args'
TYPE = 'type'
OPT = 'opt'
ID2 = 'id2'
WRITE_MODE = 'w'
 
class ArgsParser:
    """A helper class to validate arguments."""
    def __init__(self, config):
        """Initialize instance with given config."""
        self.logger = logging.getLogger()
        self.load_parsers(config)

    def load_parsers(self, config):
        """Create arg parser object."""
        self.logger.debug('Creating parser objects using config dictionary')
        self.parser = argparse.ArgumentParser()
        if SUBPARSERS in config:
            self.load_subparsers(config[SUBPARSERS], self.parser)
    
    def load_subparsers(self, subparsers_config, parent_parser):
        """Add subparsers to parent parser recursively.

        Positional arguments:
            subparsers_config -- the configuration dict for the current subparser
            parent_parser     -- the parent object to add the parsers to.
        """
        self.logger.debug('Loading subparsers recursively')
        # create subparsers
        subparsers = parent_parser.add_subparsers(dest=subparsers_config[ID])
        subparsers.required = subparsers_config[REQUIRED]
        for subparser_config in subparsers_config[SUBPARSERS_CFGS]:
            subparser = subparsers.add_parser(subparser_config[NAME], help=subparser_config[HELP])

            # load arguments for subparser
            for arg in subparser_config[ARGS]:
                if arg[TYPE] == OPT:
                    arg_id = arg[ID]
                    arg_id2 = arg[ID2]
                    subparser.add_argument(arg_id, arg_id2)
                else:
                    arg_id = arg[ID]
                    subparser.add_argument(arg_id)

            if SUBPARSERS in subparser_config:
                self.load_subparsers(subparser_config[SUBPARSERS], subparser)

    def parse(self, arguments):
        """Parse a list of arguments and return a dictionary with the result.
        
        Positional arguments:
            arguments -- a list of strings representing arguments

        Return value:
            a dictionary with the result of argparse.ArgumentParser.parse_args()
        """
        self.logger.debug('Parsing arguments')
        args = self.parser.parse_args(arguments)
        return vars(args)

class FileHelper:
    """A helper class to handle file I/O"""
    @staticmethod
    def write_lines(filename, lines):
        """Open a file in write mode and add a list of strings.
        Create the parent directory if it doesn't exist.

        Positional arguments:\n
        filename -- a string representing the file's absolute path\n
        lines    -- a list of strings representing the content
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, WRITE_MODE) as file_writer:
            file_writer.writelines(lines)

    @staticmethod
    def read(filename):
        """Open a file in read mode and extract the content.

        Positional arguments:
            filename -- a string representing the file's absolute path

        Return value:
            a string representing the file content
        """
        data = None
        with open(filename) as file_reader:
            data = file_reader.read()
        return data

    @staticmethod
    def get_files_from_dir(dir_path):
        """Get the names of all the files in a given directory.
        
        Positional arguments:
            dir_path -- a string representing the absolute path to the directory.

        Return valule:
            a list of strings, each string representing a file in the directory.
        """
        return [file for file in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, file))]
