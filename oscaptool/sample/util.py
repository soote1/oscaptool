import os
import logging
import argparse

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
        if "subparsers" in config:
            self.load_subparsers(config['subparsers'], self.parser)
    
    def load_subparsers(self, subparsers_config, parent_parser):
        """Add subparsers to parent parser recursively.

        Positional arguments:
        subparsers_config -- the configuration dict for the current subparser
        parent_parser     -- the parent object to add the parsers to.
        """
        self.logger.debug('Loading subparsers recursively')
        # create subparsers
        subparsers = parent_parser.add_subparsers(dest=subparsers_config['id'])
        subparsers.required = subparsers_config['required']
        for subparser_config in subparsers_config['subparsers_cfgs']:
            subparser = subparsers.add_parser(subparser_config['name'], help=subparser_config['help'])

            # load arguments for subparser
            for arg in subparser_config['args']:
                if arg['type'] == 'opt':
                    arg_id = arg['id']
                    arg_id2 = arg['id2']
                    subparser.add_argument(arg_id, arg_id2)
                else:
                    arg_id = arg['id']
                    subparser.add_argument(arg_id)

            if 'subparsers' in subparser_config:
                self.load_subparsers(subparser_config['subparsers'], subparser)

    def parse(self, arguments):
        """Parse a list of arguments and return a dictionary with the result.
        
        Positional arguments:\n
        arguments -- a list of strings representing arguments\n

        Return value:\n
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
        with open(filename, 'w') as file_writer:
            file_writer.writelines(lines)

    @staticmethod
    def read(filename):
        """Open a file in read mode and extract the content.

        Positional arguments:\n
        filename -- a string representing the file's absolute path\n

        Return value:\n
        a string representing the file content
        """
        data = None
        with open(filename) as file_reader:
            data = file_reader.read()
        return data

    @staticmethod
    def get_files_from_dir(dir_path):
        """Get the names of all the files in a given directory.
        
        Positional arguments:\n
        dir_path -- a string representing the absolute path to the directory.

        Return valule:\n
        a list of strings, each string representing a file in the directory.
        """
        return [file for file in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, file))]
