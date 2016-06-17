#
# ***********************************************  Utility *************************************************************
#

__all__ = ['Arithmetic',
           'Linear',
           'Exponential',
           'Integrator',
           'LinearMatrix',
           'UtilityError',
           "UtilityFunctionOutputType"]

from Main import *
from Globals.Keywords import *
from Globals.Registry import register_category
from Functions.ShellClasses import *

import math
import numpy as np
from random import randint
from operator import *
from functools import reduce

UtilityRegistry = {}


class UtilityError(Exception):
     def __init__(self, error_value):
         self.error_value = error_value

     def __str__(self):
         return repr(self.error_value)


class UtilityFunctionOutputType(IntEnum):
    RAW_NUMBER = 0
    NP_1D_ARRAY = 1
    NP_2D_ARRAY = 2


# class Utility_Base(Function):
class Utility_Base(Utility):
    """Implement abstract class for Utility category of Function class

    Description:
        Utility functions are ones used by other function categories;
        They are defined here (on top of standard libraries) to provide a uniform interface for managing parameters
         (including defaults)
        NOTE:   the Utility category definition serves primarily as a shell, and an interface to the Function class,
                   to maintain consistency of structure with the other function categories;
                it also insures implementation of .function for all Utility Functions
                (as distinct from other Function subclasses, which can use a kwExecuteMethod param
                    to implement .function instead of doing so directly

    Instantiation:
        A utility function can be instantiated in one of several ways:
IMPLEMENTATION NOTE:  *** DOCUMENTATION

    Variable and Parameters:
IMPLEMENTATION NOTE:  ** DESCRIBE VARIABLE HERE AND HOW/WHY IT DIFFERS FROM PARAMETER
        - Parameters can be assigned and/or changed individually or in sets, by:
          • including them in the initialization call
          • calling the assign_defaults method (which changes their default values)
          • including them in a call the function method (which changes their values for just for that call)
        - Parameters must be specified in a params dictionary:
          • the key for each entry should be the name of the parameter (used also to name associated projections)
          • the value for each entry is the value of the parameter

    Return values:
        The functionOutputType can be used to specify type conversion for single-item return values:
        - it can only be used for numbers or a single-number list; other values will generate an exception
        - if self.functionOutputType is set to:
            UtilityFunctionOutputType.RAW_NUMBER, return value is "exposed" as a number
            UtilityFunctionOutputType.NP_1D_ARRAY, return value is 1d np.array
            UtilityFunctionOutputType.NP_2D_ARRAY, return value is 2d np.array
        - it must be enabled for a subclass by setting params[kwFunctionOutputTypeConversion] = True
        - it must be implemented in the execute method of the subclass
        - see Linear for an example

    MechanismRegistry:
        All Utility functions are registered in UtilityRegistry, which maintains a dict for each subclass,
          a count for all instances of that type, and a dictionary of those instances

    Naming:
        Utility functions are named by their functionName attribute (usually = functionType)

    Class attributes:
        + functionCategory: kwUtilityeFunctionCategory
        + className (str): kwMechanismFunctionCategory
        + suffix (str): " <className>"
        + registry (dict): UtilityRegistry
        + classPreference (PreferenceSet): UtilityPreferenceSet, instantiated in __init__()
        + classPreferenceLevel (PreferenceLevel): PreferenceLevel.CATEGORY
        + paramClassDefaults (dict): {kwFunctionOutputTypeConversion: False}

    Class methods:
        none

    Instance attributes:
        + functionType (str):  assigned by subclasses
        + functionName (str):   assigned by subclasses
        + variable (value) - used as input to function's execute method
        + paramInstanceDefaults (dict) - defaults for instance (created and validated in Functions init)
        + paramsCurrent (dict) - set currently in effect
        + executeMethodOutputDefault (value) - sample output of function's execute method
        + executeMethodOutputType (type) - type of output of function's execute method
        + name (str) - if it is not specified as an arg, a default based on the class is assigned in register_category
        + prefs (PreferenceSet) - if not specified as an arg, default is created by copying UtilityPreferenceSet

    Instance methods:
        The following method MUST be overridden by an implementation in the subclass:
        • execute(variable, params)
        The following can be implemented, to customize validation of the function variable and/or params:
        • [validate_variable(variable)]
        • [validate_params(request_set, target_set, context)]
    """

    functionCategory = kwUtilityFunctionCategory
    className = functionCategory
    suffix = " " + className

    registry = UtilityRegistry

    classPreferenceLevel = PreferenceLevel.CATEGORY

    variableClassDefault = None
    variableClassDefault_locked = False

    # Note: the following enforce encoding as 1D np.ndarrays (one array per variable)
    variableEncodingDim = 1

    paramClassDefaults = Function.paramClassDefaults.copy()
    paramClassDefaults.update({kwFunctionOutputTypeConversion: False}) # Enable/disable output type conversion

    def __init__(self,
                 variable_default,
                 param_defaults,
                 name=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """Assign category-level preferences, register category, and call super.__init__

        Initialization arguments:
        - variable_default (anything): establishes type for the variable, used for validation
        - params_default (dict): assigned as paramInstanceDefaults
        Note: if parameter_validation is off, validation is suppressed (for efficiency) (Function class default = on)

        :param variable_default: (anything but a dict) - value to assign as variableInstanceDefault
        :param param_defaults: (dict) - params to be assigned to paramInstanceDefaults
        :param log: (FunctionLog enum) - log entry types set in self.functionLog
        :param name: (string) - optional, overrides assignment of default (functionName of subclass)
        :return:
        """
        self._functionOutputType = None
        self.name = self.functionName

        register_category(self, Utility_Base, UtilityRegistry, context=context)

        super(Utility_Base, self).__init__(variable_default=variable_default,
                                           param_defaults=param_defaults,
                                           name=name,
                                           prefs=prefs,
                                           context=context)

    @property
    def functionOutputType(self):
        if self.paramsCurrent[kwFunctionOutputTypeConversion]:
            return self._functionOutputType
        return None

    @functionOutputType.setter
    def functionOutputType(self, value):

        # Attempt to set outputType but conversion not enabled
        if value and not self.paramsCurrent[kwFunctionOutputTypeConversion]:
            raise UtilityError("output conversion is not enabled for {0}".format(self.__class__.__name__))

        # Bad outputType specification
        if value and not isinstance(value, UtilityFunctionOutputType):
            raise UtilityError("value ({0}) of functionOutputType attribute must be UtilityFunctionOutputType for {1}".
                               format(self.functionOutputType, self.__class__.__name__))

        # Can't convert from arrays of length > 1 to number
        # if (self.variable.size  > 1 and (self.functionOutputType is UtilityFunctionOutputType.RAW_NUMBER)):
        if (len(self.variable)  > 1 and (self.functionOutputType is UtilityFunctionOutputType.RAW_NUMBER)):
            raise UtilityError("{0} can't be set to return a single number since its variable has more than one number".
                               format(self.__class__.__name__))
        self._functionOutputType = value


# *****************************************   EXAMPLE FUNCTION   *******************************************************


class Contradiction(Utility_Base): # Example
    """Example function for use as template for function construction

    Iniialization arguments:
     - variable (boolean or statement resolving to boolean)
     - params (dict) specifying the:
         + propensity (kwPropensity: a mode specifying the manner of responses (tendency to agree or disagree)
         + pertinacity (kwPertinacity: the consistency with which the manner complies with the propensity

    Contradiction.function returns True or False
    """

    # Function functionName and type (defined at top of module)
    functionName = kwContradiction
    functionType = kwExampleFunction

    # Variable class default
    # This is used both to type-cast the variable, and to initialize variableInstanceDefault
    variableClassDefault = 0
    variableClassDeafult_locked = False

    # Mode indicators
    class Manner(Enum):
        OBSEQUIOUS = 0
        CONTRARIAN = 1

    # Param class defaults
    # These are used both to type-cast the params, and as defaults if none are assigned
    #  in the initialization call or later (using either assign_defaults or during a function call)
    kwPropensity = "PROPENSITY"
    kwPertinacity = "PERTINACITY"
    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwPropensity: Manner.CONTRARIAN,
                          kwPertinacity:  10,
                          })

    def __init__(self,
                 variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        # This validates variable and/or params_list if assigned (using validate_params method below),
        #    and assigns them to paramsCurrent and paramInstanceDefaults;
        #    otherwise, assigns paramClassDefaults to paramsCurrent and paramInstanceDefaults
        # NOTES:
        #    * paramsCurrent can be changed by including params in call to function
        #    * paramInstanceDefaults can be changed by calling assign_default
        super(Contradiction, self).__init__(variable_default,
                                            param_defaults,
                                            prefs=prefs,
                                            context=context)

    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Returns a boolean that is (or tends to be) the same as or opposite the one passed in

        Returns True or False, that is either the same or opposite the statement passed in as the variable
        The propensity parameter must be set to be Manner.OBSEQUIOUS or Manner.CONTRARIAN, which
            determines whether the response is (or tends to be) the same as or opposite to the statement
        The pertinacity parameter determines the consistency with which the response conforms to the manner

        :param variable: (boolean) Statement to probe
        :param params: (dict) with entires specifying
                       kwPropensity: Contradiction.Manner - contrarian or obsequious (default: CONTRARIAN)
                       kwPertinacity: float - obstinate or equivocal (default: 10)
        :return response: (boolean)
        """
        self.check_args(variable, params)

        # Compute the function

        # Use self.variable (rather than variable), as it has been validated (and default assigned, if necessary)
        statement = self.variable
        propensity = self.paramsCurrent[self.kwPropensity]
        pertinacity = self.paramsCurrent[self.kwPertinacity]
        whim = randint(-10, 10)

        if propensity == self.Manner.OBSEQUIOUS:
            return whim < pertinacity

        elif propensity == self.Manner.CONTRARIAN:
            return whim > pertinacity

        else:
            raise UtilityError("This should not happen if parameter_validation == True;  check its value")

    def validate_variable(self, variable, context=NotImplemented):
        """Validates variable and assigns validated values to self.variable

        This overrides the class method, to perform more detailed type checking
        See explanation in class method.
        Note:  this method (or the class version) is called only if the parameter_validation attribute is True

        :param variable: (anything but a dict) - variable to be validated:
        :param context: (str)
        :return none:
        """

        if type(variable) == type(self.variableClassDefault) or \
                (isinstance(variable, numbers.Number) and  isinstance(self.variableClassDefault, numbers.Number)):
            self.variable = variable
        else:
            raise UtilityError("Variable must be {0}".format(type(self.variableClassDefault)))

    def validate_params(self, request_set, target_set=NotImplemented, context=NotImplemented):
        """Validates variable and /or params and assigns to targets

        This overrides the class method, to perform more detailed type checking
        See explanation in class method.
        Note:  this method (or the class version) is called only if the parameter_validation attribute is True

        :param request_set: (dict) - params to be validated
        :param target_set: (dict) - destination of validated params
        :return none:
        """

        message = ""

        # Check params
        for param_name, param_value in request_set.items():

            # Check that specified parameter is legal
            if param_name not in request_set.keys():
                message += "{0} is not a valid parameter for {1}".format(param_name, self.name)

            if param_name == self.kwPropensity:
                if isinstance(param_value, Contradiction.Manner):
                    # target_set[self.kwPropensity] = param_value
                    pass # This leaves param in request_set, clear to be assigned to target_set in call to super below
                else:
                    message = "Propensity must be of type Example.Mode"
                continue

            # Validate param
            if param_name == self.kwPertinacity:
                if isinstance(param_value, numbers.Number) and 0 <= param_value <= 10:
                    # target_set[self.kwPertinacity] = param_value
                    pass # This leaves param in request_set, clear to be assigned to target_set in call to super below
                else:
                    message += "Pertinacity must be a number between 0 and 10"
                continue

        if message:
            raise UtilityError(message)

        super(Contradiction, self).validate_params(request_set, target_set, context)



# *****************************************   UTILITY FUNCTIONS   ******************************************************

#  COMBINATION FUNCTIONS +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Arithmetic
#  [Polynomial — TBI]

kwArithmeticInitializer = "Initializer"

class Arithmetic(Utility_Base): # ------------------------------------------------------------------------------------------
    """Combines list of values, w/ option weighting, offset and/or scaling (kwWeights, kwOffset, kwScale, kwOperation))

    Initialization arguments:
     - variable (value, np.array or list): values to be combined;
         the length of the list must be equal to the length of the weights param (default is 2)
         if it is a list, must be a list of numbers, lists, or np.arrays
     - params (dict) specifying:
         + list of weights (kwWeights: list of numbers) — * each variable before combining them (default: [1, 1])
         + offset (kwOffset: value) - added to the result (after the arithmetic operation is applied; default is 0)
         + scale (kwScale: value) - * result (after arithmetic operation is applied; default: 1)
         + operation (kwOperation: Operation Enum) - used to combine terms (default: SUM)

    Arithmetic.execute returns combined values:
    - single number if variable was a single number or list of numbers
    - list of numbers if variable was list of numbers
    - np.array if variable was a single np.variable or list of np.arrays
    """

    functionName = kwArithmetic
    functionType = kwCombinationFunction

    # Operation indicators
    class Operation(Enum):
        SUM = 0
        PRODUCT = 1

    # class Format(IntEnum):
    #     NUMBER = 0
    #     is_list_of_numbers = 1
    #     LIST_OF_LISTS = 2

    # Params:
    kwWeights = "WEIGHTS"
    kwOffset = "ADDITIVE CONSTANT"
    kwScale = "MULTIPLICATIVE SCALE"
    kwOperation = "OPERATION"

    variableClassDefault = [2, 2]
    # variableClassDefault_locked = True

    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwWeights: NotImplemented,
                               kwOffset: 0,
                               kwScale: 1,
                               kwOperation: Operation.SUM})

    def __init__(self,
                 variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):

        super(Arithmetic, self).__init__(variable_default,
                                         param_defaults,
                                         prefs,
                                         context=context)

# MODIFIED 6/12/16 NEW:
    def validate_params(self, request_set, target_set=NotImplemented, context=NotImplemented):

        super(Utility_Base, self).validate_params(request_set=request_set,
                                                  target_set=target_set,
                                                  context=context)

        weights = target_set[self.kwWeights]
        operation = target_set[self.kwOperation]

        # Make sure weights is a list of numbers or an np.ndarray
        if weights and not weights is NotImplemented:
            if ((isinstance(weights, list) and all(isinstance(elem, numbers.Number) for elem in weights)) or
                    isinstance(weights, np.ndarray)):
                # convert to 2D np.ndarrray (to distribute over 2D self.variable array)
                target_set[self.kwWeights] = np.atleast(self.paramsCurrent[self.kwWeights]).reshape(2,1)
            else:
                raise UtilityError("weights param ({0}) for {1} must be a list of numbers or an np.array".
                               format(weights, self.name))

        if not operation:
            raise UtilityError("Operation param missing")
        if not operation == self.Operation.SUM and not operation == self.Operation.PRODUCT:
            raise UtilityError("Operation param ({0}) must be Operation.SUM or Operation.PRODUCT".format(operation))
# MODIFIED 6/12/16 END

    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Arithmetically combine a list of values, and optionally offset and/or scale them

# DOCUMENT:
        Handles 1-D or 2-D arrays of numbers
        Convert to np.array
        All elements must be numeric
        If linear (single number or 1-D array of numbers) just apply scale and offset
        If 2D (array of arrays), apply weights to each array
        Operators:  SUM AND PRODUCT
        -------------------------------------------
        OLD:
        Variable must be a list of items:
            - each item can be a number or a list of numbers
        Corresponding elements of each item in variable are combined based on kwOperation param:
            - SUM adds corresponding elements
            - PRODUCT multiples corresponding elements
        An initializer (kwArithmeticInitializer) can be provided as the first item in variable;
            it will be populated with a number of elements equal to the second item,
            each element of which is determined by kwOperation param:
            - for SUM, initializer will be a list of 0's
            - for PRODUCT, initializer will be a list of 1's
        Returns a list of the same length as the items in variable,
            each of which is the combination of their corresponding elements specified by kwOperation

        :var variable: (list of numbers) - values to calculate (default: [0, 0]:
        :parameter params: (dict) with entries specifying:
                           kwWeights: list - value multiplied by each value in the variable list (default: 1):
                           kwOffset: number - additive constant (default: 0):
                           kwScale: number - scaling factor (default: 1)
                           kwOperation: Arithmetic.Operation - operation to perform (default: SUM):
        :return: (number)
        """

        # Validate variable and assign to self.variable
        self.check_args(variable=variable, params=params, context=context)

        weights = self.paramsCurrent[self.kwWeights]
        operation = self.paramsCurrent[self.kwOperation]
        offset = self.paramsCurrent[self.kwOffset]
        scale = self.paramsCurrent[self.kwScale]

        # IMPLEMENTATION NOTE:  SHOULD NEVER OCCUR, AS validate_variable NOW ENFORCES 2D np.ndarray
        # If variable is 0D or 1D:
        if np_array_less_than_2d(self.variable):
            return (self.variable * scale) + offset

        # Apply weights if they were specified
        if weights and not weights is NotImplemented:
            if len(weights) != len(self.variable):
                raise UtilityError("Number of items in variable ({0}) does not equal number of weights ({1})".
                                   format(len(self.variable.shape), len(weights)))
            else:
                self.variable = self.variable * weights

        # Calculate using relevant aggregation operation and return
        if (operation is self.Operation.SUM):
            result = sum(self.variable) * scale + offset
        elif operation is self.Operation.PRODUCT:
            result = reduce(mul, self.variable, 1)
        else:
            raise UtilityError("Unrecognized operator ({0}) for Arithmetic function".
                               format(self.paramsCurrent[self.kwOperation].self.Operation.SUM))
        return result

# Polynomial param indices
# TBI


# class Polynomial(Utility_Base): # ------------------------------------------------------------------------------------------
#     pass


#  TRANSFER FUNCTIONS +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#  Linear
#  Exponential
#  Integrator

class Linear(Utility_Base): # ----------------------------------------------------------------------------------------------
    """Calculate a linear transform of input variable (kwSlope, kwIntercept)

    Initialization arguments:
     - variable (number): transformed by linear function: slope * variable + intercept
     - params (dict): specifies
         + slope (kwSlope: value) - slope (default: 1)
         + intercept (kwIntercept: value) - intercept (defaul: 0)

    Linear.function returns scalar result
    """

    functionName = kwLinear
    functionType = kwTransferFuncton

    # Params
    kwSlope = "SLOPE"
    kwIntercept = "INTERCEPT"

    variableClassDefault = [0]

    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwSlope: 1,
                               kwIntercept: 0,
                               kwFunctionOutputTypeConversion: True})

    def __init__(self,
                 variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):

        super(Linear, self).__init__(variable_default=variable_default,
                                     param_defaults=param_defaults,
                                     prefs=prefs,
                                     context=context)

        self.functionOutputType = None

    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Calculate single value (defined by slope and intercept)

        :var variable: (number) - value to be "plotted" (default: 0
        :parameter params: (dict) with entries specifying:
                           kwSlope: number - slope (default: 1)
                           kwIntercept: number - intercept (default: 0)
        :return number:
        """

        self.check_args(variable, params)

        slope = self.paramsCurrent[self.kwSlope]
        intercept = self.paramsCurrent[self.kwIntercept]
        outputType = self.functionOutputType

        # By default, result should be returned as np.ndarray with same dimensionality as input
        result = self.variable * slope + intercept

        #region Type conversion (specified by outputType):
        # Convert to 2D array, irrespective of variable type:
        if outputType is UtilityFunctionOutputType.NP_2D_ARRAY:
            result = np.atleast2d(result)

        # Convert to 1D array, irrespective of variable type:
        # Note: if 2D array (or higher) has more than two items in the outer dimension, generate exception
        elif outputType is UtilityFunctionOutputType.NP_1D_ARRAY:
            # If variable is 2D
            if self.variable.ndim == 2:
                # If there is only one item:
                if len(self.variable) == 1:
                    result = result[0]
                else:
                    raise UtilityError("Can't convert result ({0}: 2D np.ndarray object with more than one array)"
                                       " to 1D array".format(result))
            elif len(self.variable) == 1:
                result = result
            elif len(self.variable) == 0:
                result = np.atleast_1d(result)
            else:
                raise UtilityError("Can't convert result ({0} to 1D array".format(result))

        # Convert to raw number, irrespective of variable type:
        # Note: if 2D or 1D array has more than two items, generate exception
        elif outputType is UtilityFunctionOutputType.RAW_NUMBER:
            # If variable is 2D
            if self.variable.ndim == 2:
                # If there is only one item:
                if len(self.variable) == 1 and len(self.variable[0]) == 1:
                    result = result[0][0]
                else:
                    raise UtilityError("Can't convert result ({0}) with more than a single number to a raw number".
                                       format(result))
            elif len(self.variable) == 1:
                if len(self.variable) == 1:
                    result = result[0]
                else:
                    raise UtilityError("Can't convert result ({0}) with more than a single number to a raw number".
                                       format(result))
            else:
                return result
        #endregion

        return result


class Exponential(Utility_Base): # -------------------------------------------------------------------------------------
    """Calculate an exponential transform of input variable  (kwRate, kwScale)

    Initialization arguments:
     - variable (number):
         + scalar value to be transformed by exponential function: scale * e**(rate * x)
     - params (dict): specifies
         + rate (kwRate: coeffiencent on variable in exponent (default: 1)
         + scale (kwScale: coefficient on exponential (default: 1)

    Exponential.function returns scalar result
    """

    functionName = kwExponential
    functionType = kwTransferFuncton

    # Params
    kwRate = "RATE"
    kwScale = "SCALE"

    variableClassDefault = 0

    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwRate: 1,
                          kwScale: 1
                          })

    def __init__(self,
                 variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):

        super(Exponential, self).__init__(variable_default,
                                          param_defaults,
                                          prefs=prefs,
                                          context=context)

    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Exponential function

        :var variable: (number) - value to be exponentiated (default: 0
        :parameter params: (dict) with entries specifying:
                           kwRate: number - rate (default: 1)
                           kwScale: number - scale (default: 1)
        :return number:
        """

        self.check_args(variable, params)

        # Assign the params and return the result
        rate = self.paramsCurrent[self.kwRate]
        scale = self.paramsCurrent[self.kwScale]

        return scale * np.exp(rate * self.variable)


class Integrator(Utility_Base): # --------------------------------------------------------------------------------------
    """Calculate an accumulated value for input variable using a specified accumulation method  (kwRate, kwWeighting)

    Initialization arguments:
     - variable (list of numbers): old and new values used to accumulate variable at rate and using a method in params
     - params (dict): specifying:
         + scale (kwRate: value - rate of accumuluation based on weighting of new vs. old value (default: 1)
         + weighting (kwWeighting: Weightings Enum) - method of accumulation (default: LINEAR):
                LINEAR — returns old_value incremented by rate parameter
                SCALED — returns old_value incremented by rate * new_value
                TIME_AVERAGED — returns rate-weighted average of old and new values
                                rate = 0:  no change (returns old_value)
                                rate 1:    instantaneous change (returns new_value)

    Integrator.function returns scalar result
    """

    class Weightings(Enum):
        LINEAR                   = 0
        SCALED                   = 1
        TIME_AVERAGED            = 2

    functionName = kwIntegrator
    functionType = kwTransferFuncton

    # Params:
    kwRate = "RATE"
    kwWeighting = "WEIGHTING"

    variableClassDefault = [0, 0]

    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwRate: 1,
                          kwWeighting: Weightings.LINEAR})

    def __init__(self, variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):

        super(Integrator, self).__init__(variable_default,
                                         param_defaults,
                                         prefs=prefs,
                                         context=context)

    # def execute(self, old_value, new_value, param_list=NotImplemented):
    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Integrator function

        :var variable: (list) - old_value and new_value (default: [0, 0]:
        :parameter params: (dict) with entries specifying:
                        kwRate: number - rate of accumulation as relative weighting of new vs. old value  (default = 1)
                        kwWeighting: Integrator.Weightings - type of weighting (default = Weightings.LINEAR)
        :return number:
        """

        self.check_args(variable, params)

        values = self.variable
        rate = self.paramsCurrent[self.kwRate]
        weighting = self.paramsCurrent[self.kwWeighting]

        old_value = values[0]
        new_value = values[1]

        # Compute function based on weighting param
        if weighting == self.Weightings.LINEAR:
            value = old_value + rate
            return value
        elif weighting == self.Weightings.SCALED:
            value = old_value + (new_value * rate)
            return value
        elif weighting == self.Weightings.TIME_AVERAGED:
            return (1-rate)*old_value + rate*new_value
        else:
            return new_value


# LinearMatrix
# 2D list used to map the output of one mechanism to the input of another
#

class LinearMatrix(Utility_Base):  # -----------------------------------------------------------------------------------
    """Map sender vector to receiver vector using a linear weight matrix  (kwReceiver, kwMatrix)

    Use a weight matrix to convert a sender vector into a receiver vector:
    - each row of the mapping corresponds to an element of the sender vector (outer index)
    - each column of the mapping corresponds to an element of the receiver vector (inner index):

    ----------------------------------------------------------------------------------------------------------
    MATRIX FORMAT
                                     INDICES:
                                 Receiver elements:
                            0       1       2       3
                        0  [0,0]   [0,1]   [0,2]   [0,3]
    Sender elements:    1  [1,0]   [1,1]   [1,2]   [1,3]
                        2  [2,0]   [2,1]   [2,2]   [2,3]

    matrix.shape => (sender/rows, receiver/cols)

    ----------------------------------------------------------------------------------------------------------
    ARRAY FORMAT
                                                                        INDICES
                                           [ [      Sender 0 (row0)      ], [       Sender 1 (row1)      ]... ]
                                           [ [ rec0,  rec1,  rec2,  rec3 ], [ rec0,  rec1,  rec2,  rec3  ]... ]
    matrix[senders/rows, receivers/cols]:  [ [ col0,  col1,  col2,  col3 ], [ col0,  col1,  col2,  col3  ]... ]
                                           [ [[0,0], [0,1], [0,2], [0,3] ], [[1,0], [1,1], [1,2], [1,3] ]... ]

    ----------------------------------------------------------------------------------------------------------

    Initialization arguments:
    - variable (2D np.ndarray containing exactly two sub-arrays:  sender and receiver vectors
    - params (dict) specifying:
         + filler (kwFillerValue: number) value used to initialize all entries in matrix (default: 0)
         + identity (kwkwIdentityMapping: boolean): constructs identity matrix (default: False)

    Create a matrix in self.matrix that is used in calls to LinearMatrix.function.

    Returns sender 2D array linearly transformed by self.matrix
    """

    functionName = kwLinearMatrix
    functionType = kwTransferFuncton

    # Params:
    kwReceiver = "Receiver" # Specification of (dimensionality of) receiver vector 
    kwMatrix = "Matrix"     # Specification of weight matrix

    # Keywords:
    kwIdentityMatrix = "IdentityMatrix"
    kwDefaultMatrix = kwIdentityMatrix

    DEFAULT_FILLER_VALUE = 0

    VALUE = 'Value'
    VECTOR = 'Vector'

    variableClassDefault = [DEFAULT_FILLER_VALUE]  # Sender vector

    paramClassDefaults = Utility_Base.paramClassDefaults.copy()
    paramClassDefaults.update({kwMatrix: kwIdentityMatrix})


    def __init__(self,
                 variable_default=variableClassDefault,
                 param_defaults=NotImplemented,
                 prefs=NotImplemented,
                 context=NotImplemented):
        """Transforms variable (sender vector) using matrix specified by params, and returns receiver vector

        Variable = sender vector (list of numbers)

        :param variable_default: (list) - list of numbers (default: [0]
        :param param_defaults: (dict) with entries specifying:
                                kwReceiver: value - list of numbers, determines width (cols) of matrix (defalut: [0])
                                kwMatrix: value - value used to initialize matrix;  can be one of the following:
                                    + single number - used to fill self.matrix (default: DEFAULT_FILLER_VALUE)
                                    + matrix - assigned to self.matrix
                                    + kwIdentity - create identity matrix (diagonal elements = 1;  all others = 0)
        :return none
        """

        # Note: this calls validate_variable and validate_params which are overridden below;
        #       the latter implements the matrix if required
        super(LinearMatrix, self).__init__(variable_default,
                                           param_defaults,
                                           prefs=prefs,
                                           context=context)

        self.matrix = self.implement_matrix(self.paramsCurrent[self.kwMatrix])

    def validate_variable(self, variable, context=NotImplemented):
        """Insure that variable passed to LinearMatrix is a 1D np.array

        :param variable: (1D np.array)
        :param context:
        :return:
        """
        super(Utility_Base, self).validate_variable(variable, context)

        # Check that self.variable == 1D
        try:
            is_not_1D = not self.variable.ndim is 1

        except AttributeError:
            raise UtilityError("PROGRAM ERROR: variable ({0}) for {1} should be an np.ndarray".
                               format(self.variable, self.__class__.__name__))
        else:
            if is_not_1D:
                raise UtilityError("variable ({0}) for {1} must be a 1D np.ndarray".
                                   format(self.variable, self.__class__.__name__))

    def validate_params(self, request_set, target_set=NotImplemented, context=NotImplemented):
        """Validate params and assign to targets

        This overrides the class method, to perform more detailed type checking (see explanation in class method).
        Note:  this method (or the class version) is called only if the parameter_validation attribute is True

        :param request_set: (dict) - params to be validated
        :param target_set: (dict) - destination of validated params
        :param context: (str)
        :return none:
        """

        super(LinearMatrix, self).validate_params(request_set, target_set, context)
        param_set = target_set
        sender = self.variable
        # Note: this assumes self.variable is a 1D np.array, as enforced by validate_variable
        sender_len = sender.size


        # Check for and validate kwReceiver first, since it may be needed to validate and/or construct the matrix
        # First try to get receiver from specification in params
        if self.kwReceiver in param_set:
            self.receiver = param_set[self.kwReceiver]
            # Check that specification is a list of numbers or an np.array
            if ((isinstance(self.receiver, list) and all(isinstance(elem, numbers.Number) for elem in self.receiver)) or
                    isinstance(self.receiver, np.ndarray)):
# FIX: IS THIS STILL NEEDED??  SHOULDN'T IT BE 1D ARRAY??
                # convert to 2D np.ndarrray
                # self.receiver = np.atleast_2d(self.receiver)
                self.receiver = np.atleast_1d(self.receiver)
            else:
                raise UtilityError("receiver param ({0}) for {1} must be a list of numbers or an np.array".
                                   format(self.receiver, self.name))
        # No receiver, so use sender as template (assuming square — e.g., identity — matrix)
        else:
            if self.prefs.verbosePref:
                print ("Identity matrix requested but kwReceiver not specified; sender length ({0}) will be used".
                       format(sender_len))
            self.receiver = param_set[self.kwReceiver] = sender

        receiver_len = len(self.receiver)

        # Check rest of params
        message = ""
        for param_name, param_value in param_set.items():

            # Receiver param already checked above
            if param_name is self.kwReceiver:
                continue

            # Not currently used here
            if param_name is kwFunctionOutputTypeConversion:
                continue

            # Matrix specification param
            elif param_name == self.kwMatrix:

                # A number (to be used as a filler), so OK
                if isinstance(param_value, numbers.Number):
                    pass

                # Identity matrix requested (using keyword)
                elif param_value is self.kwIdentityMatrix:
                    # Receiver length doesn't equal sender length
                    if not (self.receiver.shape == sender.shape and self.receiver.size == sender.size):
                        if self.prefs.verbosePref:
                            print ("Identity matrix requested, but length of receiver ({0})"
                                   " does not match length of sender ({1});  sender length will be used".
                                   format(receiver_len, sender_len))
                        # Set receiver to sender
                        param_set[self.kwReceiver] = sender

                # Matrix provided, so validate
                elif isinstance(param_value, (list, np.ndarray, np.matrix)):
                    # get dimensions specified by:
                    #   variable (sender): width/cols/outer index
                    #   kwReceiver param: height/rows/inner index

                    # FIX: NEED TO MAKE SURE THIS WORKS;
                    weight_matrix = np.matrix(param_value)
                    if 'U' in repr(weight_matrix.dtype):
                        raise UtilityError("Non-numeric entry in kwMatrix specification ({0})".format(param_value))

                    matrix_rows = weight_matrix.shape[0]
                    matrix_cols = weight_matrix.shape[1]

                    # Check that number of rows equals length of sender vector (variable)
                    if matrix_rows != sender_len:
                        raise UtilityError("The number of rows ({0}) of the matrix provided does not equal the "
                                            "length ({1}) of the sender vector (variable)".
                                            format(matrix_rows, sender_len))
                    # Check that number of columns equals length of specified receiver vector (kwReciever)
                    if matrix_cols != receiver_len:
                        raise UtilityError("The number of columns ({0}) of the matrix provided does not equal the "
                                            "length ({1}) of the reciever vector (kwReceiver param)".
                                            format(matrix_cols, receiver_len))

                else:
                    raise UtilityError("Value of {0} param ({1}) must be a matrix, a number, or the keyword '{2}'".
                                        format(param_name, param_value, self.kwIdentityMatrix))
            else:
                message += "Param {0} not recognized by {1} function".format(param_name,self.functionName)
                continue

        if message:
            raise UtilityError(message)


    def instantiate_attributes_before_execute_method(self, context=NotImplemented):
        self.matrix = self.implement_matrix()

    def implement_matrix(self, specification=NotImplemented, context=NotImplemented):
        """Implements matrix indicated by specification

         Specification is derived from kwMatrix param (passed to self.__init__ or self.execute)

         Specification (validated in validate_params):
            + single number (used to fill self.matrix)
            + kwIdentity (create identity matrix: diagonal elements = 1,  all others = 0)
            + 2D matrix of numbers (list or np.ndarray of numbers)

        :return matrix: (2D list)
        """

        if specification is NotImplemented:
            specification = self.kwIdentityMatrix

        # Matrix provided (and validated in validate_params), so just return it
        if isinstance(specification, np.matrix):
            return specification

        sender = self.variable
        sender_len = sender.shape[0]
        try:
            receiver = self.receiver
        except:
            print("No receiver specified for {0};  will set length equal to sender ({1})".
                  format(self.__class__.__name__, sender_len))
            receiver = sender
        receiver_len = receiver.shape[0]

        # Filler specified so use that
        if isinstance(specification, numbers.Number):
            return np.matrix([[specification for n in range(receiver_len)] for n in range(sender_len)])

        # Identity matrix specified
        if specification == self.kwIdentityMatrix:
            if sender_len != receiver_len:
                raise UtilityError("Sender length ({0}) must equal receiver length ({1}) to use identity matrix".
                                     format(sender_len, receiver_len))
            return np.identity(sender_len)

        # This should never happen (should have been picked up in validate_param)
        raise UtilityError("kwMatrix param ({0}) must be a matrix, kwIdentityMatrix, or a number (filler)".
                            format(specification))


    def execute(self, variable=NotImplemented, params=NotImplemented, context=NotImplemented):
        """Transforms variable vector using either self.matrix or specification in params

        :var variable: (list) - vector of numbers with length equal of height (number of rows, inner index) of matrix
        :parameter params: (dict) with entries specifying:
                            kwMatrix: value - used to override self.matrix implemented by __init__;  must be one of:
                                                 + 2D matrix - two-item list, each of which is a list of numbers with
                                                              length that matches the length of the vector in variable
                                                 + kwIdentity - specifies use of identity matrix (dimensions of vector)
                                                 + number - used to fill matrix of same dimensions as self.matrix
        :return list of numbers: vector with length = width (number of columns, outer index) of matrix
        """

        # Note: this calls validate_variable and validate_params which are overridden above;
        self.check_args(variable, params, context=context)

        return np.dot(self.variable, self.matrix)


def enddummy():
    pass

# *****************************************   DISTRIBUTION FUNCTIONS   *************************************************

# TBI

# *****************************************   LEARNING FUNCTIONS *******************************************************

# TBI

# *****************************************   OBJECTIVE FUNCTIONS ******************************************************

# TBI

#  *****************************************   REGISTER FUNCTIONS   ****************************************************

# Register functions
functionList = {
    Arithmetic.functionName: Arithmetic,
    Linear.functionName: Linear,
    Exponential.functionName: Exponential,
    Integrator.functionName: Integrator
    }
