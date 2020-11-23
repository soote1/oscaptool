import re
import time
import logging
import subprocess

from oscaptool.sample.util import FileHelper
from actionmanager.actions import Action, ActionError

SCAN_TYPE = 'scantype'
SCAN_SUB_TYPE = 'scansubtype'
SCAN_ID = 'scanid'
NEXT_ACTION = 'next_action'
SCAN_RESULT_1_KEY_NAME = 'scan_result_1_key_name'
SCAN_RESULT_2_KEY_NAME = 'scan_result_2_key_name'
OUTPUT_KEY_NAME = 'output_key_name'
PASS_SCAN_RESULT = 'pass'
FAIL_SCAN_RESULT = 'fail'
NA_SCAN_RESULT = 'notapplicable'
SCAN_ID_KEY_NAME = 'scan_id_key_name'
PATH = 'path'
MAPPINGS = 'mappings'
CMD_STR = 'cmd_str'
COMMAND = 'command'
CMD_STDOUT = 'cmd_stdout'
STDOUT_INPUT = 'stdout_input'

class Rule:
    """A class to represent a rule evaluation result."""
    def __init__(self, title, rule, result):
        """Initialize rule properties."""
        self._title = title
        self._rule = rule
        self._result = result
    
    def __repr__(self):
        """Create a string representation of rule values."""
        return f'Title: {self._title}\nRule: {self._rule}\nResult: {self._result}\n\n'

class ScanResult:
    """A class to represent a scan result."""
    def __init__(self, rules, stats):
        """Initialize scan result properties."""
        self._rules = rules
        self._stats = stats

    def __repr__(self):
        """Create a string representation of scan result values."""
        result = ''
        for rule in self._rules:
            result += str(rule)
        
        result += '---- Stats ----\n\n'
        result += str(self._stats)
        return result

class ScanStats:
    """A class to represent scan result stats"""
    def __init__(self, pass_count, fail_count, na_count, total):
        self.pass_count = pass_count
        self.fail_count = fail_count
        self.na_count = na_count
        self.total = total
    
    def __str__(self):
        return f'total: {self.total} pass: {self.pass_count} fail: {self.fail_count} notapplicable: {self.na_count}'

class ScanResultComparison:
    """A class to represent a comparison between two scan results"""
    def __init__(self, scan1, scan2, introduced, fixed):
        self._scan1 = scan1
        self._scan2 = scan2
        self._introduced = introduced
        self._fixed = fixed

    def __repr__(self):
        """Create a string representation of a scan result comparison."""
        return f'scan1: {self._scan1._stats}\nscan2: {self._scan2._stats}\nintroduced: {self._introduced}\nfixed: {self._fixed}'

class CreateScanId(Action):
    """A class to create the scan id."""
    def __init__(self, config):
        """Initialize action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Creates a unique scan id using the current timestamp, scan type
        and scan subtype. Adds the calculated id to the input_values dict.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running CreateScanId action')
        current_timestamp = int(time.time())
        scan_type = input_data[SCAN_TYPE]
        scan_subtype = input_data[SCAN_SUB_TYPE]
        input_data[SCAN_ID] = f'{current_timestamp}_{scan_type}_{scan_subtype}'
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data

class CompareScanResults(Action):
    """A class to compare two scan results."""
    def __init__(self, config):
        """Initialize action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Retrieve two scan results from the input_data dict and calculate the number of
        fixed/introduced results diff between both scans.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running CompareScanResults action')
        scan_result_1 = input_data[self.config[SCAN_RESULT_1_KEY_NAME]]
        scan_result_2 = input_data[self.config[SCAN_RESULT_2_KEY_NAME]]
        input_data[self.config[OUTPUT_KEY_NAME]] = self.calculate_fixed_introduced_results_diff(scan_result_1, scan_result_2)
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data

    def calculate_fixed_introduced_results_diff(self, oldest_scan, newest_scan):
        """Count how many 'fail' results from oldest scan are fixed in newest scan and how
        many 'pass' results are failing now.
        """
        self.logger.debug('Calculating fixed/introduced results diff between scans')
        fixed_count = 0
        introduced_count = 0
        newest_scan_rules_result = {rule._rule: rule._result for rule in newest_scan._rules}
        for rule in oldest_scan._rules:
            if rule._result == 'pass':
                try:
                    if newest_scan_rules_result[rule._rule] == 'fail':
                        introduced_count += 1
                except:
                    pass
            elif rule._result == 'fail':
                try:
                    if newest_scan_rules_result[rule._rule] == 'pass':
                        fixed_count += 1
                except:
                    fixed_count += 1
        return ScanResultComparison(oldest_scan, newest_scan, introduced_count, fixed_count)

class GetScanResult(Action):
    """A class to retrieve a scan result from the file system."""
    def __init__(self, config):
        """Initialize the action with the given config."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Extracts the scan id from the input_data object and uses a helper class
        to search for the file and extract the content as a string. Puts the output
        in the input_data dictionary.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running GetScanResult action')
        try:
            scan_id = input_data[self.config[SCAN_ID_KEY_NAME]]
        except Exception:
            raise ActionError('Missing input: scan_id')

        input_data[self.config[OUTPUT_KEY_NAME]] = self.get_scan_result(scan_id)
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data
    
    def parse_result(self, scan_result_str):
        """Create a list of Result objects from scan result string."""
        state = 'find_title'
        title = None
        rule = None
        result = None
        rules = []

        for line in scan_result_str.split('\n'):
            if state == 'find_title':
                if line == 'Title':
                    state = 'grab_title'
            elif state == 'grab_title':
                title = line
                state = 'find_rule'
            elif state == 'find_rule':
                if line == 'Rule':
                    state = 'grab_rule'
            elif state == 'grab_rule':
                rule = line
                state = 'find_result'
            elif state == 'find_result':
                if line == 'Result':
                    state = 'grab_result'
            elif state == 'grab_result':
                result = line
                rules.append(Rule(title.strip(), rule.strip(), result.strip()))
                state = 'find_title'

        return rules

    def get_scan_result(self, scan_id):
        """Creates a file path using a given scan id and a path from the action's config.
        Passes the file path to a helper class to retrieve the file content as a string.

        Positional arguments:
            scan_id -- a string representing a scan id

        Result:
            a string representing the file content.
        """
        self.logger.debug('Fetching scan result from file system')
        file_name = f"{self.config[PATH]}{scan_id}.txt"
        scan_result_str = FileHelper.read(file_name)
        rules = self.parse_result(scan_result_str)
        scan_stats = self.get_scan_stats(scan_result_str)
        return ScanResult(rules, scan_stats)

    def get_scan_stats(self, scan_result_str):
        """Uses a regular expression to extract all instances of a word (pass, fail, notapplicable)
        in a string, then counts the repetitions of each word and returns an object with the results.

        Positional arguments:
            scan_result_str -- a string representing a scan result

        Return value:
            a dictionary including the counts for each word.
        """
        self.logger.debug('Creating stats object for scan result')
        pass_count = len(re.findall(PASS_SCAN_RESULT, scan_result_str))
        fail_count = len(re.findall(FAIL_SCAN_RESULT, scan_result_str))
        na_count = len(re.findall(NA_SCAN_RESULT, scan_result_str))
        total_count = pass_count + fail_count + na_count
        return ScanStats(pass_count, fail_count, na_count, total_count)

class GetScanHistory(Action):
    """A class to retrieve scan history from the file system."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()
    
    def execute(self, input_data):
        """Retrieves the scan history from the file system and adds all the
        file names to the input_data object.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running GetScanHistory action')
        file_names = self.get_file_names()
        input_data[self.config[OUTPUT_KEY_NAME]] = file_names
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data
    
    def get_file_names(self):
        """Use a helper class to list all files in a given path.

        Return value:
            a list of strings representing each file in the path.
        """
        self.logger.debug('Fetching file names from directory')
        return FileHelper.get_files_from_dir(self.config[PATH])


class BuildCommand(Action):
    """A class to build a command as a string."""
    def __init__(self, config):
        """Initialize the action with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def execute(self, input_data):
        """Creates a command using a mappings dictionary from the action's config
        and the original arguments from the input_data dictionary. Puts the result
        in the input_data object.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running BuildCommand action')
        optional_args = []
        positional_args = []
        for key, val in self.config[MAPPINGS].items():
            # get the value from inputs
            arg_val = input_data[key]
            if val:
                # optional argument
                optional_args.append(f'{val} {arg_val}')
            else:
                # positional argument
                positional_args.append(arg_val)
        input_data[CMD_STR] = f"{self.config[COMMAND]} {' '.join(optional_args)} {' '.join(positional_args)}"
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
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
        stdout. Puts the command output in the input_data dictionary.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running ExecuteCommand action')
        cmd_stdout = []
        for line in self.run_command(input_data[CMD_STR].split()):
            decoded_line = line.decode('utf-8')
            print(decoded_line)
            cmd_stdout.append(decoded_line)
        input_data[CMD_STDOUT] = cmd_stdout
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data

    def run_command(self, cmd):
        """Use subprocess module to run a command and return an iterator to the
        stdout.

        Positional arguments:
            cmd -- a string representing the command to be executed.

        Return value:
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
        destination path is defined by the config object.

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running SaveScanResult action')
        self.save_scan_result(self.create_filename(input_data), input_data[CMD_STDOUT])
        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data
    
    def create_filename(self, input_data):
        """Create a file name and return it as a string.

        Positional arguments:
            input_data -- a dictionary including scanid value.

        Return value:
            a string representing the file name.
        """
        self.logger.debug('Creating filename using scan id')
        scan_id = input_data[SCAN_ID]
        path = self.config[PATH]
        filename = f'{path}{scan_id}.txt'
        return filename
    
    def save_scan_result(self, filename, result):
        """Use a helper class to create the file and save the scan result.
        
        Positional arguments:
            filename -- a string representing the file path.
            result   -- a set of strings to be saved in the file.
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

        Positional arguments:
            input_data -- a dictionary including all inputs required for the action.

        Return value:
            a dictionary including the action's output and all previous inputs.
        """
        self.logger.debug('Running PrintStdout action')
        stdout_input = input_data[STDOUT_INPUT]
        if type(stdout_input) == str:
            print(stdout_input)
        elif type(stdout_input) == list:
            for line in stdout_input:
                print(line)
        else:
            print(str(stdout_input))

        input_data[NEXT_ACTION] = self.config[NEXT_ACTION]
        return input_data