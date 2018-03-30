# -*- coding: utf-8 -*-
import qi
import sys
from app_list_manager import AppListManager
from view_manager import ViewManager
from preferences_manager import PreferencesManager
from dialog_manager import DialogManager
import helpers


class AppLauncher:

    @qi.nobind
    def __init__(self, session=None):
        self._session = session
        self._module_name = self.__class__.__name__
        self.__name__ = self._module_name
        self._logger = qi.Logger(self._module_name)
        self._logger.info(":::: Starting {} ::::".format(self._module_name))
        self._pref_domain = "tool.applauncher"  # @TODO: "com.sbr.apps.app-launcher"

        # public variables
        self._logger.info("Initializing public variables...")
        self.current_state = qi.Property("s")
        self.current_state.setValue("")
        self.current_page = qi.Property("s")
        self.current_page.setValue("Home")
        self.apps_full_list = qi.Property()
        self.apps_full_list.setValue({})
        self.pages_definition = qi.Property()
        self.pages_definition.setValue({})
        self.autonomous_enabled = qi.Property("b")
        self.autonomous_enabled.setValue(True)
        self.display_app_name = qi.Property("b")
        self.display_app_name.setValue(True)
        self.ping_required = qi.Signal("(i)")

        # internal variables
        self._logger.info("Initializing internal variables...")
        self._app_uuid = helpers.find_app_name(self._logger)
        self._current_app = ""
        self._preferences_manager = PreferencesManager(self._logger, self._session, self._pref_domain)
        self._app_list_manager = AppListManager(self._logger, self._session, self._preferences_manager,
                                                self._app_uuid, self.apps_full_list, self.pages_definition)
        self._view_manager = ViewManager(self._logger, self._session, self._preferences_manager,
                                         self._app_uuid, self.current_state, self.ping_required)
        self._dialog_manager = DialogManager(self._logger, self._session, self._preferences_manager,
                                             self.pages_definition, self.autonomous_enabled, self.current_page)

        _pref_display_app_name = self._preferences_manager.get_value('behaviorNameDisplayed', True)
        if _pref_display_app_name:
            self.display_app_name.setValue(True)
        else:
            self.display_app_name.setValue(False)

        self._logger.info(":::: Ready! ::::")

    @qi.nobind
    def cleanup(self):
        try:
            self._logger.info(":::: Stopping app launcher... ::::")
        except NameError:
            print "╔══════════════════════════╦══════════════════════════╗"
            print "║ End of automatic logging ║ was the app uninstalled? ║"
            print "╚══════════════════════════╩══════════════════════════╝"

            class DummyLog:
                def __init__(self):
                    pass

                @staticmethod
                def verbose(*args):
                    for a in args:
                        print "verbose: {}".format(a)

                @staticmethod
                def info(*args):
                    for a in args:
                        print "info: {}".format(a)

                @staticmethod
                def warning(*args):
                    for a in args:
                        print "warning: {}".format(a)

                @staticmethod
                def error(*args):
                    for a in args:
                        print "error: {}".format(a)

            self._logger = DummyLog()
            self._dialog_manager._logger = self._logger
            self._view_manager._logger = self._logger
            self._app_list_manager._logger = self._logger
            self._app_list_manager._icons_storage._logger = self._logger
            self._preferences_manager._logger = self._logger
        try:
            # clean variables
            self._dialog_manager.cleanup()
            self._view_manager.cleanup()
            self._app_list_manager.cleanup()
            self._preferences_manager.cleanup()
        except Exception as e:
            self._logger.info("error while stopping app launcher: {}".format(e))

        # Reset states
        try:
            basic = self._session.service("ALBasicAwareness")
            basic.setEnabled(True)
        except Exception as e:
            self._logger.info("error while configuring ALBasicAwareness: {}".format(e))

        self._logger.info(":::: Stopped! ::::")

    """
        Public bound functions
    """
    @qi.bind(paramsType=[qi.Int32], returnType=qi.Void, methodName="ping")
    def ping(self, seconds_before_next_ping_request):
        """ This function should be called by the web page to signal that it is still alive.
        When the signal ping_required is raised, the web page should call this function.
        In case ping is not called in time, the tablet will be reset.

        Argument: delay in seconds before next ping will be asked."""
        self._view_manager.ping(seconds_before_next_ping_request)

    @qi.bind(paramsType=[], returnType=qi.Void, methodName="_updateAppList")
    def _update_app_list(self):
        """ Reload the list of applications and pages."""
        self._app_list_manager.update_app_lists(None, True)

    @qi.bind(paramsType=[qi.String], returnType=qi.Void, methodName="runBehavior")
    def run_behavior(self, behavior):
        """ Ask autonomous life to start a given behavior and check if the launch was ok after 15s.

        Argument: behavior to launch."""
        try:
            # If an error occurs during launch, the tablet will be displayed again
            app_launched_check = qi.async(self._view_manager.display_view, delay=15000000)
            # Life switch focus to the chosen app
            life = self._session.service("ALAutonomousLife")
            life.switchFocus(behavior)
            self._logger.info("Switch focus")
            app_launched_check.cancel()
            self._logger.info("Application launch end")

        except Exception as e:
            self._logger.error("Run behavior error: " + str(e))

    @qi.bind(paramsType=[], returnType=qi.Void, methodName="stopBehavior")
    def stop_behavior(self):
        """ Stop the current running behavior. """
        self._session.service('ALBehaviorManager').stop_behavior(self._current_app)
        self._logger.info("Stop behavior: {}" .format(self._current_app))

    @qi.bind(paramsType=[qi.Int32], returnType=qi.Void, methodName="adjustVolume")
    def adjust_volume(self, diff):
        """ Change the robot volume. The volume will not go higher than 100% or lower than 20%.

        Argument: delta (positive or negative) to add to the volume. """
        audio = self._session.service('ALAudioDevice')
        current_volume = audio.getOutputVolume()
        new_volume = current_volume + diff
        if new_volume > 100:
            new_volume = 100
        elif new_volume < 20:
            new_volume = 20
        audio.setOutputVolume(new_volume)
        self._logger.info("New volume: {}" .format(new_volume))


# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
def register_as_service(service_class, session):
    """
    Registers a service in naoqi
    """
    service_name = service_class.__name__
    service_instance = service_class(session)
    try:
        session.registerService(service_name, service_instance)
        print 'Successfully registered service: {}'.format(service_name)
        return service_instance
    except RuntimeError:
        print '{} already registered, attempt re-register'.format(service_name)
        for info in session.services():
            try:
                if info['name'] == service_name:
                    session.unregisterService(info['serviceId'])
                    print "Unregistered {} as {}".format(service_name, info['serviceId'])
                    break
            except (KeyError, IndexError):
                pass
        session.registerService(service_name, service_instance)
        print 'Successfully registered service: {}'.format(service_name)
        return service_instance

if __name__ == "__main__":
    """
    Registers AppLauncher as a naoqi service.
    """
    app = qi.Application(sys.argv)
    app.start()
    instance = register_as_service(AppLauncher, app.session)
    app.run()
    instance.cleanup()
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
