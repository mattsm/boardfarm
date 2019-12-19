import pexpect

class BftBaseException(Exception):
    '''
    Base exception all Bft exceptions inherit from
    '''

class TestError(BftBaseException):
    """
    Raise this if a TestStep verification fails
    """
    pass

class TestImportError(Exception):
    '''
    Raise this if there is an exception when importing a test.
    '''
    pass

class BftNotSupportedDevice(BftBaseException):
    pass

class SkipTest(BftBaseException):
    '''
    Raise this to skip running a test.
    '''
    pass

class BootFail(BftBaseException):
    '''
    Raise this if the board fails to boot.
    This exception is special because if it
    occurs then most likely no other test
    can successfully run.
    '''
    pass

class CodeError(BftBaseException):
    """Raise this if an code assert fails

    This exception is only meant for custom assert
    clause used inside libraries.
    Not to be used with TestStep verification.
    """
    pass

class PexpectErrorTimeout(pexpect.TIMEOUT, BftBaseException):
    """
    Raise this if pexpect times out
    """
    pass

class ConfigKeyError(BftBaseException):
    '''
    Invalid use of key in config object
    '''
    pass

class DeviceDoesNotExistError(BftBaseException):
    '''
    Device does not exist
    '''
