import re
import time
import logging
import subprocess

from oscaptool.sample.util import FileHelper
from oscaptool.sample.actionmanager.actions import Action, ActionError

class CreateScanId(Action):
    """A class to create the scan id."""
    def __init__(self, config):
        """Initialize action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Creates a unique scan id using the current timestamp, scan type
        and scan subtype. Adds the calculated id to the input_values dict.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.\n
        """
        self.logger.debug('Running CreateScanId action')
        current_timestamp = int(time.time())
        scan_type = input_data['scantype']
        scan_subtype = input_data['scansubtype']
        input_data['scanid'] = f'{current_timestamp}_{scan_type}_{scan_subtype}'
        input_data['next_action'] = self.config['next_action']
        return input_data

class CompareScanResults(Action):
    """A class to compare two scan results."""
    def __init__(self, config):
        """Initialize action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Calculates stats (total, pass, fail and notapplicable results)
        for each scan result, then calculates the diff between both stats. Adds the
        final result to the input_values dictionary.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running CompareScanResults action')
        scan_stats_1 = self.get_scan_stats(input_data[self.config['scan_result_1_key_name']])
        scan_stats_2 = self.get_scan_stats(input_data[self.config['scan_result_2_key_name']])
        stats_comaparison = self.diff_stats(scan_stats_1, scan_stats_2)
        output_str = self.create_output_str(scan_stats_1, scan_stats_2, stats_comaparison)
        input_data[self.config['output_key_name']] = output_str
        input_data['next_action'] = self.config['next_action']
        return input_data
     
    def get_scan_stats(self, scan_result_str):
        """Uses a regular expression to extract all instances of a word (pass, fail, notapplicable)
        in a string, then counts the repetitions of each word and returns an object with the results.\n

        Positional arguments:\n
        scan_result_str -- a string representing a scan result\n

        Return value:\n
        a dictionary including the counts for each word.
        """
        self.logger.debug('Creating stats object for scan result')
        pass_items = len(re.findall('pass', scan_result_str))
        fail_items = len(re.findall('fail', scan_result_str))
        na_items = len(re.findall('notapplicable', scan_result_str))
        return {'pass':pass_items, 'fail':fail_items, 'na':na_items}

    def diff_stats(self, stats1, stats2):
        """Calculates the absolute difference between each stats object 
        and returns a new object with the results.

        Positional arguments:\n
        stats1 -- a dictionary including the counts for each result type\n
        stats2 -- a dictionary including the counts for each result type\n

        Return value:\n
        a dictionary including the diff between stats.
        """
        self.logger.debug('Creating diff object using scan result objects')
        pass_diff = abs(stats1['pass']-stats2['pass'])
        fail_diff = abs(stats1['fail']-stats2['fail'])
        na_diff = abs(stats1['na']-stats2['na'])
        return {'pass_diff':pass_diff, 'fail_diff':fail_diff, 'na_diff':na_diff}

    def create_output_str(self, stats1, stats2, diff):
        """Creates a string representation of each stats (stats1, stats2, diff).

        Positional arguments:\n
        stats1 -- a dictionary including the counts for each result type\n
        stats2 -- a dictionary including the counts for each result type\n
        diff   -- a dictionary including the diffs between stats1 and stats2\n

        Return value:\n
        a string representing the data on each input.
        """
        self.logger.debug('Building string representation for stats')
        scan_1_stats_str = f"Scan 1 - pass: {stats1['pass']} fail: {stats1['fail']} na: {stats1['na']}"
        scan_2_stats_str = f"Scan 2 - pass: {stats2['pass']} fail: {stats2['fail']} na: {stats2['na']}"
        diff_str  = f"Diff - pass: {diff['pass_diff']} fail: {diff['fail_diff']} na: {diff['na_diff']}"
        return f'{scan_1_stats_str}\n{scan_2_stats_str}\n{diff_str}'

class GetScanResult(Action):
    """A class to retrieve a scan result from the file system."""
    def __init__(self, config):
        """Initialize the action with the given config."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Extracts the scan id from the input_data object and uses a helper class
        to search for the file and extract the content as a string. Puts the output
        in the input_data dictionary.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running GetScanResult action')
        try:
            scan_id = input_data[self.config['scan_id_key_name']]
        except Exception:
            raise ActionError('Missing input: scan_id')

        input_data[self.config['output_key_name']] = self.get_scan_result(scan_id)
        input_data['next_action'] = self.config['next_action']
        return input_data

    def get_scan_result(self, scan_id):
        """Creates a file path using a given scan id and a path from the action's config.
        Passes the file path to a helper class to retrieve the file content as a string.

        Positional arguments:
        scan_id -- a string representing a scan id

        Result:
        a string representing the file content.
        """
        self.logger.debug('Fetching scan result from file system')
        file_name = f"{self.config['path']}{scan_id}.txt"
        return FileHelper.read(file_name)

class GetScanHistory(Action):
    """A class to retrieve scan history from the file system."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()
    
    def execute(self, input_data):
        """Retrieves the scan history from the file system and adds all the
        file names to the input_data object.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running GetScanHistory action')
        file_names = self.get_file_names()
        input_data[self.config['output_key_name']] = file_names
        input_data['next_action'] = self.config['next_action']
        return input_data
    
    def get_file_names(self):
        """Use a helper class to list all files in a given path.
        Return value:\n
        a list of strings representing each file in the path.
        """
        self.logger.debug('Fetching file names from directory')
        return FileHelper.get_files_from_dir(self.config['path'])


class BuildCommand(Action):
    """A class to build a command as a string."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Creates a command using a mappings dictionary from the action's config
        and the original arguments from the input_data dictionary. Puts the result
        in the input_data object.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running BuildCommand action')
        optional_args = []
        positional_args = []
        for key, val in self.config['mappings'].items():
            # get the value from inputs
            arg_val = input_data[key]
            if val:
                # optional argument
                optional_args.append(f'{val} {arg_val}')
            else:
                # positional argument
                positional_args.append(arg_val)
        input_data['cmd_str'] = f"{self.config['command']} {' '.join(optional_args)} {' '.join(positional_args)}"
        input_data['next_action'] = self.config['next_action']
        return input_data

class ExecuteCommand(Action):
    """A class to execute a command and save the output."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Extracts the command to execute from the input_data dictionary,
        then uses the subprocess module to run the command and capture the
        stdout. Puts the command output in the input_data dictionary.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running ExecuteCommand action')
        cmd_stdout = []
        for line in self.run_command(input_data['cmd_str'].split()):
            decoded_line = line.decode('utf-8')
            print(decoded_line)
            cmd_stdout.append(decoded_line)
        input_data['cmd_stdout'] = cmd_stdout
        input_data['next_action'] = self.config['next_action']
        return input_data

    def run_command(self, cmd):
        """Use subprocess module to run a command and return an iterator to the
        stdout.

        Positional arguments:\n
        cmd -- a string representing the command to be executed.

        Return value:\n
        an iterator pointing to the first item of the stdout.
        """
        self.logger.debug('Running command in a child process')
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) # TODO: redirect stderr to stdout but change it later
        return iter(p.stdout.readline, b'')

class SaveScanResult(Action):
    """A class to save a scan result in the file system."""
    def __init__(self, config):
        """Initialize action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Extracts the scan result from the input_data object and save it to a new file
        in the file system. The name of the file is calculated using the scan id. The
        destination path is defined by the config object.\n

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running SaveScanResult action')
        self.save_scan_result(self.create_filename(input_data), input_data['cmd_stdout'])
        input_data['next_action'] = self.config['next_action']
        return input_data
    
    def create_filename(self, input_data):
        """Create a file name and return it as a string.

        Positional arguments:\n
        input_data -- a dictionary including scanid value.

        Return value:\n
        a string representing the file name.
        """
        self.logger.debug('Creating filename using scan id')
        scan_id = input_data['scanid']
        path = self.config['path']
        filename = f'{path}{scan_id}.txt'
        return filename
    
    def save_scan_result(self, filename, result):
        """Use a helper class to create the file and save the scan result.
        
        Positional arguments:\n
        filename -- a string representing the file path.\n
        result   -- a set of strings to be saved in the file.\n
        """
        self.logger.debug('Saving scan result in a new file')
        FileHelper.write_lines(filename, result)

class PrintStdout(Action):
    """An action to print content in the stdout."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Extracts the content from input_data dictionary and print it in the stdout.

        Positional arguments:\n
        input_data -- a dictionary including all inputs required for the action.\n

        Return value:\n
        a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running PrintStdout action')
        stdout_input = input_data['stdout_input']
        if type(stdout_input) == str:
            print(stdout_input)
        elif type(stdout_input) == list:
            for line in stdout_input:
                print(line)
        else:
            raise ActionError('Invalid format for stdout_input input value')

        input_data['next_action'] = self.config['next_action']
        return input_data