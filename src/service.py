## {{{ http://code.activestate.com/recipes/551780/ (r3)
# winservice.py

from os.path import splitext, abspath
from sys import modules, stderr

import win32service
import win32event
import win32api
import sys
import win32serviceutil
import servicemanager

class Service(win32serviceutil.ServiceFramework):
    _svc_name_ = '_unNamed'
    _svc_display_name_ = '_Service Template'

    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.log('init')
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def sleep(self, sec):
        win32api.Sleep(sec * 1000, True)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('start')
            self.start()
            self.log('wait')
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            self.log('done')
        except Exception, x:
            self.log('Exception : %s' % x)
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.log('stopping')
        self.stop()
        self.log('stopped')
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    # to be overridden
    def start(self):
        pass

    # to be overridden
    def stop(self):
        pass


def _prepareClass(cls, display_name, name):
    cls._svc_name_ = name
    cls._svc_display_name_ = display_name or name
    try:
        module_path = modules[cls.__module__].__file__
    except AttributeError:
        # maybe py2exe went by
        from sys import executable

        module_path = executable
    module_file = splitext(abspath(module_path))[0]
    cls._svc_reg_class_ = '%s.%s' % (module_file, cls.__name__)

def instart(cls, name, display_name=None, stay_alive=True):
    ''' Install and  Start (auto) a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
        display_name : the name displayed in the service manager
        stay_alive : Service will stop on logout if False
    '''
    install(cls, name, display_name, stay_alive)
    start(cls, name)

def install(cls, name, display_name=None, stay_alive=True):
    ''' Install a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
        display_name : the name displayed in the service manager
        stay_alive : Service will stop on logout if False
    '''
    _prepareClass(cls, display_name, name)

    if stay_alive:
        win32api.SetConsoleCtrlHandler(lambda x: True, True)

    try:
        win32serviceutil.QueryServiceStatus(cls._svc_name_)
    except Exception, x:
        if not 'service does not exist as an installed service' in x.strerror:
            sys.stderr.write(x.strerror + "\n")
        else:
            try:
                win32serviceutil.InstallService(
                    cls._svc_reg_class_,
                    cls._svc_name_,
                    cls._svc_display_name_,
                    startType=win32service.SERVICE_AUTO_START
                )
                print "Service installed"

            except Exception, x:
                sys.stderr.write(x.strerror + "\n")


# def start(cls, name, display_name=None, stay_alive=True):
def start(cls, name):
    ''' Start a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
        display_name : the name displayed in the service manager
        stay_alive : Service will stop on logout if False
    '''
    cls._svc_name_ = name
    # _prepareClass(cls, display_name, name)

    try:
        win32serviceutil.StartService(
            cls._svc_name_
        )
        print 'Service started'
    except Exception, x:
        sys.stderr.write(x.strerror + "\n")


def stop(cls, name):
    ''' Stop a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
    '''
    cls._svc_name_ = name

    try:
        status = win32serviceutil.StopService(cls._svc_name_)
        print "Service stopped"
    except Exception, x:
        sys.stderr.write(x.strerror + "\n")

def uninstall(cls, name):
    ''' First stop, then delete a Service

        cls : the class (derived from Service) that implement the Service
        name : Service name
    '''
    cls._svc_name_ = name

    try:
        status = win32serviceutil.QueryServiceStatus(cls._svc_name_)
        if status[1] != win32service.SERVICE_STOPPED:
            stop(cls, name)
            win32serviceutil.WaitForServiceStatus(cls._svc_name_, win32service.SERVICE_STOPPED, 15)

        win32serviceutil.RemoveService(cls._svc_name_)
        print "Service uninstalled"

    except Exception, x:
        sys.stderr.write(x.strerror + "\n")