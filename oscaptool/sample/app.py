import os
import sys
import json
import logging
import logging.config

from oscaptool.sample.util import ArgsParser
from oscaptool.sample.actionmanager.manager import ActionManager, WorkflowMetadata

class Client:
    """A class to represent the main process."""
    def __init__(self, config):
        """Initialize client with a given configuration dictionary."""
        self.config = config
        self.logger = logging.getLogger()

    def run(self):
        """Gets the list of arguments from the sys module and
        executes the parsing and workflow processes.
        """
        self.logger.debug('Reading args from input')
        args = sys.argv[1:]
        argsparser = ArgsParser(self.config['argparser'])
        parsed_args = argsparser.parse(args)

        self.logger.debug('Interpreting parsed args')
        workflow_metadata = self.build_workflow_metadata(parsed_args)
        action_manager = ActionManager(self.config['actionmanager'])
        action_manager.run_workflow(workflow_metadata)

    def build_workflow_metadata(self, parsed_args):
        """Creates a WorkflowMetadata object from a set of parsed args."""
        self.logger.debug('Building workflow metadata object')

        workflow_id_keys = {'action'}
        workflow_id = ''
        if parsed_args['action'] == 'scan':
            workflow_id_keys.add('scantype')
            workflow_id_keys.add('scansubtype')
            scan_type = parsed_args['scantype']
            scan_subtype = parsed_args['scansubtype']
            workflow_id = f"{parsed_args['action']}-{scan_type}-{scan_subtype}"
        elif parsed_args['action'] == 'show':
            workflow_id = 'show-scan-result' if parsed_args['scan_id'] else 'show-scan-history'
        elif parsed_args['action'] == 'comp':
            workflow_id = 'comp-scan-results'
        
        return WorkflowMetadata(workflow_id, parsed_args)

def create_app():
    """App's entry point."""
    # configure logging
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger()
    logger.info('oscaptool started')

    # load app configuration file
    config = None
    with open(f'{os.path.dirname(__file__)}/config.json') as json_config_file:
            config = json.loads(json_config_file.read())

    # initialize and run client
    client = Client(config)
    client.run()

    logger.info('oscaptool finished')