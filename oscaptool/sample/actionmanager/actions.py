import re
import time
import subprocess
from oscaptool.sample.util import FileHelper

class ActionError(Exception):
    """Base class for action exceptions."""
    def __init__(self, message):
        self.message = message

class Action:
    "Base class for specific actions."
    def __init__(self, config):
        pass

    def execute(self):
        pass

class CreateScanId(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        current_timestamp = int(time.time())
        scan_type = input_data['scantype']
        scan_subtype = input_data['scansubtype']
        input_data['scanid'] = f'{current_timestamp}_{scan_type}_{scan_subtype}'
        input_data['next_action'] = self.config['next_action']
        return input_data

class CompareScanResults(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print("CompareScanResults action")
        scan_stats_1 = self.get_scan_stats(input_data[self.config['scan_result_1_key_name']])
        scan_stats_2 = self.get_scan_stats(input_data[self.config['scan_result_2_key_name']])
        stats_comaparison = self.diff_stats(scan_stats_1, scan_stats_2)
        output_str = self.create_output_str(scan_stats_1, scan_stats_2, stats_comaparison)
        input_data[self.config['output_key_name']] = output_str
        input_data['next_action'] = self.config['next_action']
        return input_data
     
    def get_scan_stats(self, scan_result_str):
        pass_items = len(re.findall('pass', scan_result_str))
        fail_items = len(re.findall('fail', scan_result_str))
        na_items = len(re.findall('notapplicable', scan_result_str))
        return {'pass':pass_items, 'fail':fail_items, 'na':na_items}

    def diff_stats(self, stats1, stats2):
        pass_diff = abs(stats1['pass']-stats2['pass'])
        fail_diff = abs(stats1['fail']-stats2['fail'])
        na_diff = abs(stats1['na']-stats2['na'])
        return {'pass_diff':pass_diff, 'fail_diff':fail_diff, 'na_diff':na_diff}

    def create_output_str(self, stats1, stats2, comparison):
        scan_1_stats_str = f"Scan 1 - pass: {stats1['pass']} fail: {stats1['fail']} na: {stats1['na']}"
        scan_2_stats_str = f"Scan 2 - pass: {stats2['pass']} fail: {stats2['fail']} na: {stats2['na']}"
        comparison_str  = f"Diff - pass: {comparison['pass_diff']} fail: {comparison['fail_diff']} na: {comparison['na_diff']}"
        return f'{scan_1_stats_str}\n{scan_2_stats_str}\n{comparison_str}'

class GetScanResult(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print("GetScanResult action")
        try:
            scan_id = input_data[self.config['scan_id_key_name']]
        except Exception:
            raise ActionError('Missing input: scan_id')

        input_data[self.config['output_key_name']] = self.get_scan_result(scan_id)
        input_data['next_action'] = self.config['next_action']
        return input_data

    def get_scan_result(self, file_id):
        file_name = f"{self.config['path']}{file_id}.txt"
        return FileHelper.read(file_name)

class GetScanHistory(Action):
    def __init__(self, config):
        self.config = config
    
    def execute(self, input_data):
        print("GetScanHistory action")
        try:
            file_names = self.get_file_names()
        except Exception as error:
            print(error)

        input_data[self.config['output_key_name']] = file_names
        input_data['next_action'] = self.config['next_action']
        return input_data
    
    def get_file_names(self):
        return FileHelper.get_files_from_dir(self.config['path'])


class BuildCommand(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print("BuildCommand action")
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
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print('ExecuteCommand action')
        cmd_stdout = []
        for line in self.run_command(input_data['cmd_str'].split()):
            decoded_line = line.decode('utf-8')
            print(decoded_line)
            cmd_stdout.append(decoded_line)
        input_data['cmd_stdout'] = cmd_stdout
        input_data['next_action'] = self.config['next_action']
        return input_data

    def run_command(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) # redirect stderr to stdout but change it later
        return iter(p.stdout.readline, b'')

class SaveScanResult(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print("SaveScanResult action")
        self.save_scan_result(self.create_filename(input_data), input_data['cmd_stdout'])
        input_data['next_action'] = self.config['next_action']
        return input_data
    
    def create_filename(self, input_data):
        scan_id = input_data['scanid']
        path = self.config['path']
        filename = f'{path}{scan_id}.txt'
        return filename
    
    def save_scan_result(self, filename, result):
        FileHelper.write_lines(filename, result)

class PrintStdout(Action):
    def __init__(self, config):
        self.config = config

    def execute(self, input_data):
        print("PrintStdout action")
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