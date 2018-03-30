# -*- coding: utf-8 -*-
import qi
import time


class ViewManager:
    def __init__(self, logger, session, pref_manager, app_uuid, current_state_prop, ping_required_sig):
        self._logger = logger
        self._session = session
        self._logger.info("> Creating view manager...")

        # Private variables
        self._app_uuid = app_uuid
        self._robot_is_booting = True
        self._previous_state = ""
        self._watchdog = None
        self._launch_async = None
        self._preferences_manager = pref_manager

        # Public variables
        self.pref_view_uuid = app_uuid
        self.change_view_uuid(pref_manager.get_value('displayedApplication', app_uuid))
        pref_manager.add_callback('displayedApplication', self.change_view_uuid)
        self.pref_force_watchdog = False
        self.current_state = current_state_prop
        self.ping_required = ping_required_sig

        # Connect AutonomousLife State
        self._logger.info("> Connecting ALMemory (waiting indefinitely)")
        self._session.waitForService("ALMemory")
        self._memory = self._session.service("ALMemory")

        self._logger.info("> Connecting to ALife State")
        self._life_state_sig = self._memory.subscriber('AutonomousLife/State').signal
        self._life_state_con = self._life_state_sig.connect(self._on_life_state_changed)
        self._current_state_con = self.current_state.connect(self._on_current_state_changed)

        self._logger.info("> Initializing ALife State")
        self._on_life_state_changed(self._memory.getData("AutonomousLife/State"))

        ## prepare tablet
        #self._logger.info("> Connecting Tablet (waiting indefinitely)")
        #self._session.waitForService("ALTabletService")

        #self._logger.info("> Preparing Tablet")
        #tablet = self._session.service("ALTabletService")
        #tablet._enableResetTablet(0)
        ## tablet.setVolume(10) # @TODO: only in naoqi 2.4

        self._logger.info("> ... View manager is ready!")

    def cleanup(self):
        self._logger.info("> Cleaning app list manager...")

        try:
            self.current_state.disconnect(self._current_state_con)
            self._life_state_sig.disconnect(self._life_state_con)

            # reset tablet
            tablet = self._session.service("ALTabletService")
            tablet._enableResetTablet(1)
            tablet.resetTablet()

            self._logger.info("> ... View manager is clean!")
        except Exception as e:
            self._logger.info("error while cleaning app list manager: {}".format(e))

    def change_view_uuid(self, view_uuid):
        if view_uuid:
            self.pref_view_uuid = view_uuid
            self._logger.info("> App view is now: {}".format(self.pref_view_uuid))

    def _on_life_state_changed(self, autonomous_life_state):
        try:
            if autonomous_life_state == "solitary":
                asleep = False
                try:
                    asleep = self._memory.getData("AutonomousLife/Asleep")
                except:
                    self._logger.info("> could not read AutonomousLife/Asleep")
                if asleep:
                    self._set_current_state("sleeping")
                else:
                    self._set_current_state("ready")

            elif autonomous_life_state == "interactive":
                try:
                    self._current_app = self._memory.getData("AutonomousLife/NextActivity")
                    self._logger.info("> Running {}".format(self._current_app))
                except:
                    self._logger.info("> could not read AutonomousLife/NextActivity")

                if self._current_app != "run_dialog_dev/.":
                    self._set_current_state("running")
                else:
                    self._set_current_state("ready")

            elif autonomous_life_state == "disabled":
                self._set_current_state("sleeping")

            elif autonomous_life_state == "safeguard":
                self._set_current_state("sleeping")

        except Exception, e:
            self._logger.error("> Set AppLauncher state error: " + str(e))

    def _set_current_state(self, new_state):
        """This method checks whether the state is part of the
            permitted states and is different from the current state
        """
        try:
            if new_state not in ["sleeping", "ready", "running"]:
                raise RuntimeError("> View state cannot be {}, it must be sleeping, running or ready.".format(new_state))
            if new_state != self.current_state.value():
                self.current_state.setValue(new_state)
        except Exception, e:
            self._logger.error("> Set current state error: " + str(e))

    def _on_current_state_changed(self, current_state):
        """Each time 'current_state' is modified, this method is called
            If the robot is booting, first time current_state change to ready
            it will launch the first display_tablet and the dialog.
            Each time current_state change from "running" to another state
            display_tablet is called.
        """
        try:
            if self._robot_is_booting and current_state == "ready":
                self._robot_is_booting = False
                self._logger.info("> Robot has finished boot sequence.")
                self.display_view()
            elif current_state == self._previous_state:
                pass
            elif current_state == "running":
                self._stop_watchdog()
            elif self._previous_state == "running":
                self._logger.info("> The running app has finished. ")
                self.display_view()

            self._previous_state = current_state

        except Exception, e:
            self._logger.error("> States changed error: " + str(e))

    def display_view(self):
        self._logger.info("> Displaying {} ".format(self.pref_view_uuid))
        try:
            tablet = self._session.service("ALTabletService")
            self._logger.verbose("> - clean Web view")
            tablet.cleanWebview()
            self._logger.verbose("> - clear Web view Cache")
            tablet._clearWebviewCache(1)
            self._logger.verbose("> - disable reset tablet")
            tablet._enableResetTablet(0)
            self._logger.verbose("> - display web view")
            tablet.loadApplication(self.pref_view_uuid)
            tablet.showWebview()
            if self.pref_force_watchdog:
                self._logger.verbose("> - force watchdog")
                self._require_ping(10)
        except Exception as e:
            self._logger.error("> error: " + str(e))

    def _require_ping(self, acceptable_delay_s):
        """ Asks the web page displayed on the tablet for a ping. This will trigger the signal ping_required."""
        self._logger.verbose("> Require ping (within {}s)".format(acceptable_delay_s))
        try:
            self._watchdog.cancel()
        except:
            pass
        self._watchdog = qi.async(self._watchdog_emergency, delay=acceptable_delay_s * 1000000)
        self.ping_required(1)

    def ping(self, seconds_before_next_ping_request):
        """ This method checks if the page on the Tablet is loaded and the javascript responding.
This method is called by the tablet, each time it is called, it stops all the scheduled display_tablet and plan
a display_tablet in delay+10 seconds.
If no other ping come after, it means the javascript is no longer available.
So when the delay has elapsed, it will try to display again the tablet.
        """
        self._logger.verbose("> Ping received (next in {}s)".format(seconds_before_next_ping_request))
        self._stop_watchdog()
        self._logger.verbose(">  ... Setting next ping in {}s".format(seconds_before_next_ping_request))
        self._watchdog = qi.async(self._require_ping, 3, delay=seconds_before_next_ping_request * 1000000)
        self._logger.verbose(">  ... all done. ")

    def _watchdog_emergency(self):
        """ If 10 seconds after the display_tablet,
            the page doesn't ping this service, this method is called
            the tablet will be automaticaly restarted and the page reloaded
        """
        self._logger.info("> Watchdog emergency")
        try:
            self._watchdog.cancel()
        except:
            pass

        if self.current_state.value() == "running":
            self._logger.info("> !!! An app is running, abort the emergency to leave it a chance!")
            return

        self._logger.info("> Waiting for ALTabletService")
        self._session.waitForService("ALTabletService")
        self._logger.info("> Connecting to ALTabletService")
        tablet = self._session.service('ALTabletService')
        self._logger.info("> Restarting browser")
        tablet._restart()
        self._logger.info("> Opening web view in 3s")
        self._watchdog = qi.async(self.display_view, delay=3000000)

    def _stop_watchdog(self):
        """This method stops all the scheduled display_tablet"""
        self._logger.verbose(">  ... calling the dogs back")
        if self._watchdog:
            self._watchdog.cancel()
            while not (self._watchdog.isCanceled() or self._watchdog.isFinished()):
                self._logger.verbose(">  ... waiting for the dogs to be back")
                time.sleep(1)
            self._logger.verbose(">  ... dogs are back. ")



