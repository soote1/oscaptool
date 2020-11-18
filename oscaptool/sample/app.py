import os
import sys
import json

from oscaptool.sample.util import ArgsParser
from oscaptool.sample.actionmanager.manager import ActionManager, WorkflowMetadata

class Client:
    """A class to represent the main process."""
    def __init__(self):
        """Loads a configuration file into a class property.
        """
        # load config
        self.config = None
        with open(f'{os.path.dirname(__file__)}/config.json') as json_config_file:
            self.config = json.loads(json_config_file.read())

    def run(self):
        """Gets the list of arguments from the sys module and
        executes the parsing and workflow processes.
        """
        args = sys.argv[1:]
        argsparser = ArgsParser(self.config['argparser'])
        parsed_args = argsparser.parse(args)

        workflow_metadata = self.build_workflow_metadata(parsed_args)
        action_manager = ActionManager(self.config['actionmanager'])
        action_manager.run_workflow(workflow_metadata)

    def build_workflow_metadata(self, parsed_args):
        """Creates a WorkflowMetadata object from a set of parsed args."""
        action = parsed_args['action']

        # create workflow id
        workflow_id_keys = {'action'}
        workflow_id = ''
        if action == 'scan':
            workflow_id_keys.add('scantype')
            workflow_id_keys.add('scansubtype')
            scan_type = parsed_args['scantype']
            scan_subtype = parsed_args['scansubtype']
            workflow_id = f'{action}-{scan_type}-{scan_subtype}'
        elif action == 'show':
            workflow_id = 'show-scan-result' if parsed_args['scan_id'] else 'show-scan-history'
        elif action == 'comp':
            workflow_id = 'comp-scan-results'
        
        return WorkflowMetadata(workflow_id, parsed_args)

def create_app():
    """App's entry point."""
    client = Client()
    client.run()