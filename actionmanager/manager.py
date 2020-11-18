from actionmanager.actions import ActionError
from actionmanager.helpers import ActionFactory

class ActionManagerError(Exception):
    """Raised when the action manager presents an error."""
    def __init__(self, message):
        self.message = message

class WorkflowMetadata:
    """A class to represent the workflow that should be executed."""
    def __init__(self, workflow_id, inputs):
        self._id = workflow_id
        self._inputs = inputs

class ActionManager:
    """A class to perform a set of actions to on given object."""

    MODULE = "module"
    CLASS = "class"
    CONFIG = "config"
    NEXT_ACTION = "next_action"
    INITIAL_ACTION = "initial_action"

    def __init__(self, config):
        """Prepares the action manager instance with a given configuration."""
        self.config = config

    def run_workflow(self, workflow_metadata):
        """Executes a list of actions in sequential order, passing an input object as
        the argument. The execution stops when the next_action key in the output is an empty string.

        Positional arguments:\n
        workflow_metadata -- an object including the workflow to be executed and the initial inputs.

        Exceptions:\n
        If the action manager can't read the next action, it throws an ActionManagerError.\n
        If the action manager receives an ActionError, it would stop the execution.\n

        Return value:\n
        a boolean value that indicating wether the execution of the workflow was successful or not.
        """
        output = workflow_metadata._inputs
        workflow_config = self.config['workflows'][workflow_metadata._id]
        self.current_action = self.create_action(workflow_config[ActionManager.INITIAL_ACTION])
        try:
            while True:
                output = self.current_action.execute(output)
                next_action_name = output[ActionManager.NEXT_ACTION]
                if not next_action_name:
                    break
                
                self.current_action = self.create_action(workflow_config[next_action_name])
            return True
        except KeyError:
            raise ActionManagerError(f"No action metadata for {next_action_name}")
            
    
    def create_action(self, action_metadata):
        """Returns a new object matching the given action metadata.

        Exceptions:\n
        An ActionManagerError is thrown if can't create action instance.

        Return value:\n
        an instance of Action class.
        """
        try:
            action = ActionFactory.create_action(
                action_metadata[ActionManager.MODULE], 
                action_metadata[ActionManager.CLASS], 
                action_metadata[ActionManager.CONFIG]
            )
        except:
            raise ActionManagerError(f"Error while creating action instance using {action_metadata}")
        
        return action