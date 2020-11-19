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
        self._config = config
        self._current_output = None
        self._current_action = None
        self._workflow_config = None

    def run_workflow(self, workflow_metadata):
        """Executes a list of actions in sequential order, passing an input object as
        the argument. The execution stops when the next_action key in the output is an empty string.

        - Positional arguments:
            workflow_metadata -- an object including the workflow to be executed and the initial inputs.

        - Exceptions:
            An Action manager error is raised if:
                Can't set initial values
                Can't set next action
                Can't create and action using action metadata
            An ActionError is raised if:
                Action's execute() method throws any exception
        """
        try:
            self.set_initial_values(workflow_metadata)
            while True:
                self._output = self._current_action.execute(self._output)
                self.set_next_action()
                if not self._current_action:
                    break
        except ActionManagerError:
            raise
        except Exception as error:
            raise ActionError(str(error))

    def set_next_action(self):
        """Create next action to be executed."""
        try:
            next_action_name = self._output[ActionManager.NEXT_ACTION]
            if next_action_name == '':
                self._current_action = None
            else:
                self._current_action = self.create_action(self._workflow_config[next_action_name])
        except ActionManagerError:
            raise
        except Exception as error:
            msg = f'error while setting next action: {str(error)}'
            raise ActionManagerError(msg)
    
    def set_initial_values(self, workflow_metadata):
        """Initialize main objects for action manager"""
        try:
            self._output = workflow_metadata._inputs
            self._workflow_config = self._config['workflows'][workflow_metadata._id]
            self._current_action = self.create_action(self._workflow_config[ActionManager.INITIAL_ACTION])
        except ActionManagerError:
            raise
        except Exception as error:
            msg = f'error while setting initial values: {str(error)}'
            raise ActionManagerError(msg)
    
    def create_action(self, action_metadata):
        """Returns a new object matching the given action metadata.

        Exceptions:
            An ActionManagerError is thrown if can't create action instance.

        Return value:
            An instance of Action class.
        """
        try:
            return ActionFactory.create_action(
                action_metadata[ActionManager.MODULE], 
                action_metadata[ActionManager.CLASS], 
                action_metadata[ActionManager.CONFIG]
            )
        except Exception as error:
            msg = f'error while creating action using action metadata: {str(error)}'
            raise ActionManagerError(msg)