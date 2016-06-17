#
# **********************************************  Projection ***********************************************************
#
from Functions.ShellClasses import *
from Functions.Utility import *
from Globals.Registry import register_category

ProjectionRegistry = {}

# class ProjectionLog(IntEnum):
#     NONE            = 0
#     TIME_STAMP      = 1 << 0
#     ALL = TIME_STAMP
#     DEFAULTS = NONE

kpProjectionTimeScaleLogEntry = "Projection TimeScale"


class ProjectionError(Exception):
    def __init__(self, error_value):
        self.error_value = error_value

    def __str__(self):
        return repr(self.error_value)

# Projection factory method:
# def projection(name=NotImplemented, params=NotImplemented, context=NotImplemented):
#         """Instantiates default or specified subclass of Projection
#
#         If called w/o arguments or 1st argument=NotImplemented, instantiates default subclass (MechanismParameterState)
#         If called with a name string:
#             - if registered in ProjectionRegistry class dictionary as name of a subclass, instantiates that class
#             - otherwise, uses it as the name for an instantiation of the default subclass, and instantiates that
#         If a params dictionary is included, it is passed to the subclass
#
#         :param name:
#         :param param_defaults:
#         :return:
#         """
#
#         # Call to instantiate a particular subclass, so look up in MechanismRegistry
#         if name in ProjectionRegistry:
#             return ProjectionRegistry[name].mechanismSubclass(params)
#         # Name is not in MechanismRegistry or is not provided, so instantiate default subclass
#         else:
#             # from Functions.Defaults import DefaultProjection
#             return DefaultProjection(name, params)
#

class Projection_Base(Projection):
    """Abstract class definition for Projection category of Function class (default type:  Mapping)

    Description:
        Projections are used as part of a configuration (together with projections) to execute a process
        Each instance must have:
        - a sender: MechanismState object from which it gets its input (serves as variable argument of the Function);
            if this is not specified, paramClassDefaults[kwProjectionSender] is used to assign a default
        - a receiver: MechanismState object to which it projects;  this MUST be specified
        - an execute method that executes the projection:
            this can be implemented as <class>.function, or specified as a reference to a method in params[kwExecuteMethod]
        - a set of parameters: determine the operation of its execute method
        The default projection type is a Mapping projection

    Subclasses:
        There are two [TBI: three] standard subclasses of Projection:
        - Mapping: uses a function to convey the MechanismState from sender to the inputState of a receiver
        - ControlSignal:  takes an allocation as input (sender) and uses it to modulate the controlState of the receiver
        [- TBI: Gating: takes an input signal and uses it to modulate the inputState and/or outputState of the receiver

    Instantiation:
        Projections should NEVER be instantiated by a direct call to the class
           (since there is no obvious default), but rather by calls to the subclass
        Subclasses can be instantiated in one of three ways:
            - call to __init__ with args to subclass for sender, receiver and (optional) params dict:
                - sender (Mechanism or MechanismState):
                    this is used if kwProjectionParam is same as default
                    sender.value used as variable for Projection.execute method
                - receiver (Mechanism or MechanismState)
                NOTES:
                    if sender and/or receiver is a Mechanism, the appropriate MechanismState is inferred as follows:
                        Mapping projection:
                            sender = <Mechanism>.outputState
                            receiver = <Mechanism>.inputState
                        ControlSignal projection:
                            sender = <Mechanism>.outputState
                            receiver = <Mechanism>.paramsCurrent[<param>] IF AND ONLY IF there is a single one
                                        that is a MechanismParameterState;  otherwise, an exception is raised
                - params (dict):
                    + kwProjectionSender:<Mechanism or MechanismState class reference or object>:
                        this is populated by __init__ with the default sender state for each subclass
                        it is used if sender arg is not provided (see above)
                        if it is different than the default, it overrides the sender arg even if that is provided
                    + kwProjectionSenderValue:<value>  - use to instantiate ProjectionSender
            - specification dict, that includes params (above), and the following two additional params
                    + kwProjectionType
                    + kwProjectionParams
            - as part of the instantiation of a MechanismState (see MechanismState);
                the MechanismState will be assigned as the projection's receiver
            * Note: the projection will be added to it's sender's MechanismState.sendsToProjections attribute

    ProjectionRegistry:
        All Projections are registered in ProjectionRegistry, which maintains a dict for each subclass,
          a count for all instances of that type, and a dictionary of those instances

    Naming:
        Projections can be named explicitly (using the name='<name>' argument).  If the argument is omitted,
        it will be assigned the subclass name with a hyphenated, indexed suffix ('subclass.name-n')

    Class attributes:
        + functionCategory (str): kwProjectionFunctionCategory
        + className (str): kwProjectionFunctionCategory
        + suffix (str): " <className>"
        + registry (dict): ProjectionRegistry
        + classPreference (PreferenceSet): ProjectionPreferenceSet, instantiated in __init__()
        + classPreferenceLevel (PreferenceLevel): PreferenceLevel.CATEGORY
        + variableClassDefault (value): [0]
        + requiredParamClassDefaultTypes = {kwProjectionSender: [str, Mechanism, MechanismState]}) # Default sender type
        + paramClassDefaults (dict)
        + paramNames (dict)
        + kwExecuteMethod (Function class or object, or method)

    Class methods:
        None

    Instance attributes:
        + sender (MechanismState)
        + receiver (MechanismState)
        + params (dict) - set currently in effect
        + paramsCurrent (dict) - current value of all params for instance (created and validated in Functions init)
        + paramInstanceDefaults (dict) - defaults for instance (created and validated in Functions init)
        + paramNames (list) - list of keys for the params in paramInstanceDefaults
        + sender (MechanismState) - mechanism from which projection receives input (default: self.senderDefault)
        + executeMethodOutputDefault (value) - sample output of projection's execute method
        + executeMethodOutputType (type) - type of output of projection's execute method
        + name (str) - if it is not specified as an arg, a default based on the class is assigned in register_category
        + prefs (PreferenceSet) - if not specified as an arg, default is created by copying ProjectionPreferenceSet

    Instance methods:
        # The following method MUST be overridden by an implementation in the subclass:
        • execute:
            - called by <Projection>reciever.ownerMechanism.update_states_and_execute()
            - must be implemented by Projection subclass, or an exception is raised
    """

    color = 0

    functionCategory = kwProjectionFunctionCategory
    className = functionCategory
    suffix = " " + className

    registry = ProjectionRegistry

    classPreferenceLevel = PreferenceLevel.CATEGORY

    variableClassDefault = [0]

    requiredParamClassDefaultTypes = Function.requiredParamClassDefaultTypes.copy()
    requiredParamClassDefaultTypes.update({kwProjectionSender: [str, Mechanism, MechanismState]}) # Default sender type

    def __init__(self,
                 receiver,
                 sender=NotImplemented,
                 params=NotImplemented,
                 name=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """Assign sender, receiver, and execute method and register mechanism with ProjectionRegistry

        This is an abstract class, and can only be called from a subclass;
           it must be called by the subclass with a context value

# DOCUMENT:  MOVE TO ABOVE, UNDER INSTANTIATION
        Initialization arguments:
            - sender (Mechanism, MechanismState or dict):
                specifies source of input to projection (default: senderDefault)
            - receiver (Mechanism, MechanismState or dict)
                 destination of projection (default: none)
            - params (dict) - dictionary of projection params:
                + kwExecuteMethod:<method>
        - name (str): if it is not specified, a default based on the class is assigned in register_category,
                            of the form: className+n where n is the n'th instantiation of the class
            - prefs (PreferenceSet or specification dict):
                 if it is omitted, a PreferenceSet will be constructed using the classPreferences for the subclass
                 dict entries must have a preference keyPath as key, and a PreferenceEntry or setting as their value
                 (see Description under PreferenceSet for details)
            - context (str): must be a reference to a subclass, or an exception will be raised

        NOTES:
        * Receiver is required, since can't instantiate a Projection without a receiving MechanismState
        * If sender and/or receiver is a Mechanism, the appropriate MechanismState is inferred as follows:
            Mapping projection:
                sender = <Mechanism>.outputState
                receiver = <Mechanism>.inputState
            ControlSignal projection:
                sender = <Mechanism>.outputState
                receiver = <Mechanism>.paramsCurrent[<param>] IF AND ONLY IF there is a single one
                            that is a MechanismParameterState;  otherwise, an exception is raised
        * instantiate_sender, instantiate_receiver must be called before instantiate_execute_method:
            - validate_params must be called before instantiate_sender, as it validates kwProjectionSender
            - instantatiate_sender may alter self.variable, so it must be called before validate_execute_method
            - instantatiate_receiver must be called before validate_execute_method,
                 as the latter evaluates receiver.value to determine whether to use self.execute or kwExecuteMethod
        * If variable is incompatible with sender's output, it is set to match that and revalidated (instantiate_sender)
        * if kwExecuteMethod is provided but its output is incompatible with receiver value, self.execute is tried
        * registers projection with ProjectionRegistry

        :param sender: (MechanismState or dict)
        :param receiver: (MechanismState or dict)
        :param param_defaults: (dict)
        :param name: (str)
        :param context: (str)
        :return: None
        """

        if not isinstance(context, Projection_Base):
            raise ProjectionError("Direct call to abstract class Projection() is not allowed; "
                                 "use projection() or one of the following subclasses: {0}".
                                 format(", ".join("{!s}".format(key) for (key) in ProjectionRegistry.keys())))

        # Assign functionType to self.name as default;
        #  will be overridden with instance-indexed name in call to super
        if name is NotImplemented:
            self.name = self.functionType
        # Not needed:  handled by subclass
        # else:
        #     self.name = name

        self.functionName = self.functionType

        register_category(self, Projection_Base, ProjectionRegistry, context=context)

        self.sender = sender
        self.receiver = receiver

# MODIFIED 6/12/16:  VARIABLE & SENDER ASSIGNMENT MESS:
        # ADD validate_variable, THAT CHECKS FOR SENDER?
        # WHERE DOES DEFAULT SENDER GET INSTANTIATED??
        # VARIABLE ASSIGNMENT SHOULD OCCUR AFTER THAT

# MODIFIED 6/12/16:  ADDED ASSIGNMENT HERE -- BUT SHOULD GET RID OF IT??
        # AS ASSIGNMENT SHOULD BE DONE IN VALIDATE_VARIABLE, OR WHEREVER SENDER IS DETERMINED??
# FIX:  NEED TO KNOW HERE IF SENDER IS SPECIFIED AS A MECHANISM OR MECHANISMSTATE
        try:
            variable = sender.value
        except:
            if self.receiver.prefs.verbosePref:
                print("Unable to get value of sender ({0}) for {1};  will assign default ({2})".
                      format(sender, self.name, self.variableClassDefault))
            variable = NotImplemented

# FIX: SHOULDN'T variable_default HERE BE sender.value ??  AT LEAST FOR Mapping?, WHAT ABOUT ControlSignal??
# FIX:  ?LEAVE IT TO VALIDATE_VARIABLE, SINCE SENDER MAY NOT YET HAVE BEEN INSTANTIATED
# MODIFIED 6/12/16:  ADDED ASSIGNMENT ABOVE
#                   (TO HANDLE INSTANTIATION OF DEFAULT ControlSignal SENDER -- BUT WHY ISN'T VALUE ESTABLISHED YET?
        # Validate variable, execute method and params, and assign params to paramsInstanceDefaults
        # Note: pass name of mechanism (to override assignment of functionName in super.__init__)
        super(Projection_Base, self).__init__(variable_default=variable,
                                              param_defaults=params,
                                              name=self.name,
                                              prefs=prefs,
                                              context=context.__class__.__name__)

        self.paramNames = self.paramInstanceDefaults.keys# ()

    def validate_params(self, request_set, target_set=NotImplemented, context=NotImplemented):
        """Validate kwProjectionSender and/or sender arg (current self.sender), and assign one of them as self.sender

        Check:
        - that kwProjectionSender is a Mechanism or MechanismState
        - if it is different from paramClassDefaults[kwProjectionSender], use it
        - if it is the same or is invalid, check if sender arg was provided to __init__ and is valid
        - if sender arg is valid use it (if kwProjectionSender can't be used);
        - otherwise use paramClassDefaults[kwProjectionSender]

        Note: check here for sender's type, but not content (e.g., length, etc.); that is done in instantiate_sender

        :param request_set:
        :param target_set:
        :param context:
        :return:
        """

        super(Projection, self).validate_params(request_set, target_set, context)

        try:
            sender_param = target_set[kwProjectionSender]
        except KeyError:
            # This should never happen, since kwProjectionSender is a required param
            raise ProjectionError("Program error: required param {0} missing in {1}".
                                  format(kwProjectionSender, self.name))

        # kwProjectionSender is either an instance or class of Mechanism or MechanismState:
        if (isinstance(sender_param, (Mechanism, MechanismState)) or
                (inspect.isclass(sender_param) and
                     (issubclass(sender_param, Mechanism) or issubclass(sender_param, MechanismState)))):
            # it is NOT the same as the default, use it
            if sender_param is not self.paramClassDefaults[kwProjectionSender]:
                self.sender = sender_param
            # it IS the same as the default, but sender arg was not provided, so use it (= default):
            elif self.sender is NotImplemented:
                self.sender = sender_param
                if self.prefs.verbosePref:
                    print("Neither {0} nor sender arg was provided for {1} projection to {2}; "
                          "default ({3}) will be used".format(kwProjectionSender,
                                                              self.name,
                                                              self.receiver.ownerMechanism.name,
                                                              sender_param.__class__.__name__))
            # it IS the same as the default, so check if sender arg (self.sender) is valid
            elif not (isinstance(self.sender, (Mechanism, MechanismState, Process)) or
                          (inspect.isclass(self.sender) and
                               (issubclass(self.sender, Mechanism) or issubclass(self.sender, MechanismState)))):
                # sender arg (self.sender) is not valid, so use kwProjectionSender (= default)
                self.sender = sender_param
                if self.prefs.verbosePref:
                    print("{0} was not provided for {1} projection to {2}, and sender arg ({3}) is not valid; "
                          "default ({4}) will be used".format(kwProjectionSender,
                                                              self.name,
                                                              self.receiver.ownerMechanism.name,
                                                              self.sender,
                                                              sender_param.__class__.__name__))
# # FIX:  MOVED THIS TO instantiate_sender FOR MAPPING PROJECTION
#                 # If sender is a Process and this projection is for its first Mechanism, it is OK
#                 if isinstance(self.sender, Process):
#                     mech_num = len(self.sender.configurationMechanismNames)
#                     if mech_num > 1:
#                         raise ProjectionError("Illegal attempt to add projection from {0} to mechanism {0} in "
#                                               "configuration list; this is only allowed for first mechanism in list".
#                                               format(self.sender.name, ))
#                 else:
#                     raise ProjectionError("sender arg ({0}) for {1} projection is not a Mechanism or MechanismState")
# FIX: IF PROJECTION, PUT HACK HERE TO ACCEPT AND FORGO ANY FURTHER PROCESSING??
            # IS the same as the default, and sender arg was provided, so use sender arg
            else:
                pass
        # kwProjectionSender is not valid, and:
        else:
            # sender arg was not provided, use paramClassDefault
            if self.sender is NotImplemented:
                self.sender = self.paramClassDefaults[kwProjectionSender]
                if self.prefs.verbosePref:
                    print("{0} ({1}) is invalid and sender arg ({2}) was not provided; default {3} will be used".
                          format(kwProjectionSender, sender_param, self.sender,
                                 self.paramClassDefaults[kwProjectionSender]))
            # sender arg is also invalid, so use paramClassDefault
            elif not isinstance(self.sender, (Mechanism, MechanismState)):
                self.sender = self.paramClassDefaults[kwProjectionSender]
                if self.prefs.verbosePref:
                    print("Both {0} ({1}) and sender arg ({2}) are both invalid; default {3} will be used".
                          format(kwProjectionSender, sender_param, self.sender,
                                 self.paramClassDefaults[kwProjectionSender]))
            else:
                self.sender = self.paramClassDefaults[kwProjectionSender]
                if self.prefs.verbosePref:
                    print("{0} ({1}) is invalid; sender arg ({2}) will be used".
                          format(kwProjectionSender, sender_param, self.sender))
            if not (isinstance(self.paramClassDefaults[kwProjectionSender], Mechanism, MechanismState)):
                raise ProjectionError("Program error: {0} ({1}) and sender arg ({2}) for {3} are both absent or invalid"
                                      " and default (paramClassDefault[{4}]) is also invalid".
                                      format(kwProjectionSender,
                                             sender_param.__name__,
                                             self.sender.__name__,
                                             self.name,
                                             self.paramClassDefaults[kwProjectionSender].__name__))

    def instantiate_attributes_before_execute_method(self, context=NotImplemented):
        self.instantiate_sender(context=context)
        self.instantiate_receiver(context=context)

    def instantiate_sender(self, context=NotImplemented):
        """Assign self.sender to outputState of sender and insure compatibility with self.variable

        If self.sender is a Mechanism, re-assign it to <Mechanism>.outputState
        If self.sender is a MechanismState class reference, validate that it is a MechanismOutputState
        Assign projection to sender's sendsToProjections attribute
        If self.value / self.variable is NotImplemented, set to sender.executeMethodOutputDefault / sender.value
        Insure that sender.executeMethodOutputDefault is compatible with self.value

        Notes:
        * ControlSignal initially overrides this method to check if sender is SystemDefaultControlMechanism;
            if so, assigns a ControlSignal-specific inputState, outputState and ControlSignalChannel to it

        :param context: (str)
        :return:
        """

        from Functions.MechanismStates.MechanismOutputState import MechanismOutputState

        # If sender is a class, instantiate it:
        # - assume it is Mechanism or MechanismState (as validated in validate_params)
        # - implement default sender of the corresponding type
        if inspect.isclass(self.sender):
            if issubclass(self.sender, MechanismOutputState):
                self.sender = self.paramsCurrent[kwProjectionSender](self.paramsCurrent[kwProjectionSenderValue])
            else:
                raise ProjectionError("Sender ({0}, for {1}) must be a MechanismOutputState".
                                      format(self.sender.__class__.__name__, self.name))


        # # If sender is a Mechanism (rather a MechanismState), get relevant outputState and assign to self.sender
        if isinstance(self.sender, Mechanism):

            # # IMPLEMENT: HANDLE MULTIPLE SENDER -> RECEIVER MAPPINGS, EACH WITH ITS OWN MATRIX:
            # #            - kwMATRIX NEEDS TO BE A 3D np.array, EACH 3D ITEM OF WHICH IS A 2D WEIGHT MATRIX
            # #            - MAKE SURE len(self.sender.value) == len(self.receiver.inputStates.items())
            # # for i in range (len(self.sender.value)):
            # #            - CHECK EACH MATRIX AND ASSIGN??
            # # FOR NOW, ASSUME SENDER HAS ONLY ONE OUTPUT STATE, AND THAT RECEIVER HAS ONLY ONE INPUT STATE
            self.sender = self.sender.outputState

        # At this point, self.sender should be a MechanismOutputState
        if not isinstance(self.sender, MechanismOutputState):
            raise ProjectionError("Sender for Mapping projection must be a Mechanism or MechanismState")

        # Assign projection to sender's sendsToProjections list attribute
        self.sender.sendsToProjections.append(self)

        # Validate projection's variable (self.variable) against sender.outputState.value
        if iscompatible(self.variable, self.sender.value):
            # Is compatible, so assign sender.outputState.value to self.variable
            self.variable = self.sender.value

        else:
            # Not compatible, so:
            # - issue warning
            if self.prefs.verbosePref:
                print("The variable ({0}) of {1} projection to {2} is not compatible with output ({3})"
                      " of execute method {4} for sender ({5}); it has been reassigned".
                      format(self.variable,
                             self.name,
                             self.receiver.ownerMechanism.name,
                             self.sender.value,
                             self.sender.execute.__class__.__name__,
                             self.sender.ownerMechanism.name))
            # - reassign self.variable to sender.value
            self.assign_defaults(variable=self.sender.value, context=context)

    def instantiate_receiver(self, context=NotImplemented):
        """Assign self.receiver to inputState of receiver

        If self.receiver is a Mechanism, re-assign to <Mechanism>.inputState
        Notes:
        * Constraint that self.executeMethodOutputDefault is compatible with receiver.inputState.value
            is evaluated and enforced in instantiate_execute_method, since that may need to be modified (see below)
        * If receiver is specified as a Mechanism, and that Mechanism has more than one inputState,
            projection is assigned to first one (Mechanism.inputState);
            assignment to other inputStates must be done explicilty (i.e., by: instantiate_receiver(MechanismState))

        :param context: (str)
        :return:
        """

        # This is to avoid PyCharm "mis-typecasting" self.receiver below
        receiver = self.receiver

        if isinstance(receiver, Mechanism):
            self.receiver = self.receiver.inputState

        self.receiver.receivesFromProjections.append(self)

    def instantiate_execute_method(self, context=NotImplemented):
        """Insure that output of execute method is compatible with the receiver's value

        Note:
        - this is called after super.validate_execute_method, self.instantiate_sender and self.instantiate_receiver
        - it overrides super.instantiate_execute_method

        Check if self.execute exists and, if so:
            save it, self.executeMethodOutputDefault and self.executeMethodOutputType
        Call super.instantiate_execute_method to instantiate params[kwExecuteMethod] if it is specified
        Check if self.value is compatible with receiver.variable; if it:
            IS compatible, return
            is NOT compatible:
                if self.execute is not implemented, raise exception
                if self.execute is implemented:
                    restore self.execute and check whether it is compatible with receiver.variable;  if it:
                        IS compatible, issue warning (if in VERBOSE mode) and proceed
                        is NOT compatible, raise exception
        Note:  during checks, if receiver.variable is a single numeric item (exposed value or in a list)
               try modifying kwFunctionOutputType of execute method to match receiver's value

        :param request_set:
        :return:
        """

        # Check subclass implementation of self.execute, its output and type and save if it exists
        try:
            self_execute_method = self.execute
        except AttributeError:
            self_execute_method = NotImplemented
            self_execute_output = NotImplemented
            self_execute_type = NotImplemented
        else:
            self_execute_output = self.value

        # Instantiate params[kwExecuteMethod], if it is specified
        super(Projection_Base, self).instantiate_execute_method(context=context)

        # If output of assigned execute method is compatible with receiver's value, return
        if iscompatible(self.value, self.receiver.variable):
            return

        # output of assigned execute method is NOT compatible with receiver's value
        else:
            # If receiver.variable is a single numeric item (exposed value or in a list)
            #   try modifying kwFunctionOutputType of execute method to match receiver's value
            conversion_message = ""
            receiver = self.receiver.variable
            projection_output = self.value
            try:
                if isinstance(receiver, numbers.Number) and len(projection_output) is 1:
                    try:
                        # self.execute.__self__.paramsCurrent[kwFunctionOutputType] = UtilityFunctionOutputType.NUMBER
                        # self.execute.__self__.functionOutputType = UtilityFunctionOutputType.NUMBER
                        self.execute.__self__.functionOutputType = UtilityFunctionOutputType.RAW_NUMBER
                    except UtilityError as error:
                        conversion_message = "; attempted to convert output but "+error.value+" "
                    else:
                        self.value = 0
                        if iscompatible(self.receiver.variable, self.execute()):
                            return
            except TypeError:
                if isinstance(projection_output, numbers.Number) and len(receiver) is 1:
                    try:
                        # self.execute.__self__.paramsCurrent[kwFunctionOutputType] = UtilityFunctionOutputType.LIST
                        # self.execute.__self__.functionOutputType = UtilityFunctionOutputType.LIST
                        self.execute.__self__.functionOutputType = UtilityFunctionOutputType.NP_1D_ARRAY
                    except UtilityError as error:
                        conversion_message = "; attempted to convert output but "+error.value+" "
                    else:
                        self.value = [0]
                        return

            # If self.execute was NOT originally implemented, raise exception
            if self_execute_method is NotImplemented:
                raise ProjectionError("The output type ({0}) of params[kwExecuteMethod] ({1}) for {2} projection "
                                      "to {6} for {3} param of {4} is not compatible with its value ({5}){7}"
                                      "(note: self.execute is not implemented for {2} so can't be used)".
                                      format(type(self.value).__name__,
                                             self.execute.__self__.functionName,
                                             self.name,
                                             self.receiver.name,
                                             self.receiver.ownerMechanism.name,
                                             type(self.receiver.variable).__name__,
                                             self.receiver.__class__.__name__,
                                             conversion_message))
            # If self.execute WAS originally implemented, but is also incompatible, raise exception:
            elif not iscompatible(self_execute_output, self.receiver.variable):
                raise ProjectionError("The output type ({0}) of self.execute ({1}) for projection {2} "
                          "is not compatible with the value ({3}) of its receiver and"
                          " params[kwExecuteMethod] was not specified{4}".
                          format(type(self.value).__name__,
                                 self.execute.functionName,
                                 self.name,
                                 type(self.receiver.variable).__name__,
                                 conversion_message))
            # self.execute WAS originally implemented and is compatible, so use it
            else:
                if self.prefs.verbosePref:
                    print("The output type ({0}) of params[kwExecuteMethod] ({1}) for projection {2} "
                                          "is not compatible with the value ({3}) of its receiver; "
                                          " default ({4}) will be used".
                                          format(type(self.value).__name__,
                                                 self.execute.functionName,
                                                 self.name,
                                                 type(self.receiver.variable).__name__,
                                                 self_execute_method.functionName))
                self.execute = self_execute_method
                self.update_value()