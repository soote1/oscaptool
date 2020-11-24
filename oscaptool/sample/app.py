import os
import sys
import json
import logging
import logging.config

from oscaptool.sample.util import ArgsParser
from actionmanager.manager import ActionManager, WorkflowMetadata

ARGPARSER = 'argparser'
ACTIONMANAGER = 'actionmanager'
ACTION = 'action'
SCAN = 'scan'
SCAN_TYPE = 'scantype'
SCAN_SUB_TYPE = 'scansubtype'
SHOW = 'show'
COMP = 'comp'
SCAN_ID = 'scan_id'
SHOW_SCAN_HISTORY = 'show-scan-history'
SHOW_SCAN_RESULT = 'show-scan-result'
COMP_SCAN_RESULTS = 'comp-scan-results'

class Client:
    """A class to represent the main process."""
    def __init__(self, config):
        """Initialize client with a given configuration dictionary."""
        self.logger = logging.getLogger()
        self.config = config
        self.init_objects()

    def init_objects(self):
        """Initialize argsparser and actionmanager using config dict."""
        try:
            self.logger.debug('Initializing argsparser and actionmanager')
            self._args_parser = ArgsParser(self.config[ARGPARSER])
            self._action_manager = ActionManager(self.config[ACTIONMANAGER])
        except:
            print('Critical error occurred while trying to initialize objects')
            print('See logs for details')
            self.logger.critical('Critical error while trying to initialize objects', exc_info=1)
            sys.exit(1)

    def run(self):
        """Run parsing arguments and execute workflow processes."""
        self.execute_workflow(self.parse_args())
    
    def parse_args(self):
        """Executes argument parsing logic"""
        self.logger.debug('Starting parsing process')
        args = sys.argv[1:]
        return self._args_parser.parse(args)

    def execute_workflow(self, parsed_args):
        """Executes a workflow using action manager."""
        try:
            self.logger.debug('Interpreting parsed args')
            self._action_manager.run_workflow(self.build_workflow_metadata(parsed_args))
        except Exception as e:
            print('An unexpected error ocurred while executing workflow:')
            print(e)
            print('See logs for details')
            self.logger.critical('Critical error occurred while trying to run workflow', exc_info=1)
            sys.exit(1)

    def build_workflow_metadata(self, parsed_args):
        """Creates a WorkflowMetadata object from a set of parsed args."""
        self.logger.debug('Building workflow metadata object')

        workflow_id_keys = {ACTION}
        workflow_id = ''
        try:
            if parsed_args[ACTION] == SCAN:
                workflow_id_keys.add(SCAN_TYPE)
                workflow_id_keys.add(SCAN_SUB_TYPE)
                scan_type = parsed_args[SCAN_TYPE]
                scan_subtype = parsed_args[SCAN_SUB_TYPE]
                workflow_id = f"{parsed_args[ACTION]}-{scan_type}-{scan_subtype}"
            elif parsed_args[ACTION] == SHOW:
                workflow_id = SHOW_SCAN_RESULT if parsed_args[SCAN_ID] else SHOW_SCAN_HISTORY
            elif parsed_args[ACTION] == COMP:
                workflow_id = COMP_SCAN_RESULTS
        except KeyError as e:
            print('Critical error ocurred while trying to build workflow metadata object')
            print(f'Key missing in parsed args dict: {e}')
            self.logger.critical('Critical error occurred while trying to build workflow metadata object', exc_info=1)
            sys.exit(1)
        
        return WorkflowMetadata(workflow_id, parsed_args)

def create_app():
    """App's entry point."""
    # configure logging
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger()
    logger.info('oscaptool started')

    # load app configuration file
    config = None
    with open(f'config.json') as json_config_file:
            config = json.loads(json_config_file.read())

    # initialize and run client
    client = Client(config)
    client.run()

    logger.info('oscaptool finished')