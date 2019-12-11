from boardfarm.lib.bft_logging import now_short
from boardfarm.exceptions import TestError, CodeError
from termcolor import cprint

class TestResult:
    logged = {}
    def __init__(self, name, grade, message, result=None):
        self.name = name
        self.result_grade = grade
        self.result_message = message
        self.result = result

    def output(self):
        """Return output of a TestAction

        This method should only be called, while verifying TestStep
        with an expected value.

        :param self: TestResult instance for a TestAction
        :returns: result
        :rtype: TestResult.result
        """
        return self.result

class TestStep(object):
    step_id = 1

    def __init__(self, parent_test, name):
        self.parent_test = parent_test
        self.name = name
        self.actions = []
        self.result = []
        parent_test.steps.append(self)
        self.verify_f, self.v_msg = None, None

        self.msg = "[{}]::[Step {}]".format(self.parent_test.__class__.__name__, self.step_id)

    def log_msg(self, msg):
        self.parent_test.log_to_file += now_short() + msg + "\r"
        cprint(msg, None, attrs=['bold'])

    def add_verify(self, func, v_msg):
        self.verify_f = func
        self.v_msg = v_msg

    def __enter__(self):
        self.log_msg(('-' * 80))
        self.log_msg("{}: START".format(self.msg))
        self.log_msg("Description: {}".format(self.name))
        self.log_msg(('-' * 80))
        return self

    def __exit__(self, ex_type, ex_value, traceback):
        r = "PASS" if not traceback else "FAIL"
        self.log_msg(('-' * 80))
        self.log_msg("{}: END\t\tResult: {}".format(self.msg, r))
        TestStep.step_id += 1

    # msg has to be the verification message.
    def verify(self, cond, msg):
        if not cond:
            self.log_msg("{} - FAILED".format(msg))
            raise TestError('{} verification - FAILED'.format(self.msg))
        else:
            self.log_msg("{} - PASSED".format(msg))


    def execute(self):
        for a_id, action in enumerate(self.actions):
            prefix = "[{}]:[Step {}.{}]::[{}]".format(
                self.parent_test.__class__.__name__,
                self.step_id,
                a_id+1,
                action.action.func.__name__)
            tr = None

            try:
                output = action.execute()
                tr = TestResult(prefix, "OK", "", output)
                self.log_msg("{} : PASS".format(prefix))
            except Exception as e:
                tr = TestResult(prefix, "FAIL", str(e), None)
                self.log_msg("{} - FAIL :: {}:{}".format(prefix, e.__class__.__name__,e.message))
                raise(e)
            finally:
                self.result.append(tr)
        if self.verify_f:
            self.verify(self.verify_f(), self.v_msg)


class TestAction(object):

    def __init__(self, parent_step, func):
        self.name = func.func.__name__
        parent_step.actions.append(self)
        self.action = func

    def execute(self):
        try:
            output = self.action()
            return output
        except AssertionError as e:
            raise CodeError(e)

if __name__ == '__main__':
    from functools import partial

    def action1(a, m=2):
        print("\nAction 1 performed multiplication\nWill return value: {}\n".format(a*m))
        return a*m

    def action2(a, m=3):
        print("\nAction 2 performed division\nWill return value: {}\n".format(a/m))
        return a/m

    class Test1(object):
        steps = []
        log_to_file = ""

        def runTest(self):
            # this one can be used to define common test Steps
            with TestStep(self, "This is step1 of test") as ts:
                TestAction(ts, partial(action1, 2, m=3))
                TestAction(ts, partial(action2, 6, m=2))

                # add verification, call it later after execute.
                # if no verification is added, we're expecting step to pass with exception from actions
                def _verify():
                    return ts.result[0].output() == 6 and \
                           ts.result[1].output() == 3
                ts.add_verify(_verify, "verify step1 output")
                ts.execute()

            with TestStep(self, "This is step2 of test") as ts:
                TestAction(ts, partial(action1, 2, m=3))
                TestAction(ts, partial(action2, 6, m=0))
                ts.execute()
                # since we didn't add a verification before,we can call one directly as well
                ts.verify(ts.result[1].output() != 3, "verify step2 output")

    obj = Test1()
    try:
        obj.runTest()
    except Exception as e:
        # handle retry condition for TC
        print("{}:{}".format(type(e),e))