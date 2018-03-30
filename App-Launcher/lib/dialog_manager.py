# -*- coding: utf-8 -*-
import qi


class DialogManager:

    _LANGUAGE_FORMAT_CONVERSION = dict(en_US="enu", fr_FR="frf", ja_JP="jpj", zh_CN="mnc",
                                       es_ES="spe", de_DE="ged", ko_KR="kok", it_IT="iti", nl_NL="dun",
                                       fi_FI="fif", pl_PL="plp", ru_RU="rur", tr_TR="trt",
                                       ar_SA="arw", cs_CZ="czc", pt_PT="ptp", pt_BR="ptb",
                                       sv_SE="sws", da_DK="dad", nn_NO="nor", el_GR="grg")

    def __init__(self, logger, session, pref_manager, pages_definition_property, autonomous_enabled_property,
                 current_page_property):
        self._logger = logger
        self._session = session
        self._logger.info("@ Creating Dialog manager...")
        self._pref_manager = pref_manager
        self._pages_definition = pages_definition_property
        self._current_language = None
        self._current_language_dlg = None
        self._current_page = current_page_property
        self._autonomous_enabled = autonomous_enabled_property
        self._connection_pagedef = self._pages_definition.connect(self._create_pages_triggers_dialog)
        self._session.waitForService("ALTextToSpeech")
        self._tts = self._session.service("ALTextToSpeech")

        self._on_language_changed(self._tts.locale())
        self._con_language = self._tts.languageTTS.connect(self._on_language_changed)

        qi.async(self._create_pages_triggers_dialog, self._pages_definition.value(), delay=1000000)
        self._pref_dialog_always_running = self._pref_manager.get_value('dialogAlwaysRunning', True)
        self.connection_autoena = self._autonomous_enabled.connect(self._on_autonomous_enabled_changed)
        self._session.waitForService("ALMemory")
        self.page_subscriber = self._session.service("ALMemory").subscriber("AppLauncher/PageRequired")
        self.page_connection = self.page_subscriber.signal.connect(self.on_page_required)
        self._logger.info("@ Dialog manager created!")

    def cleanup(self):
        self._logger.info("@ Cleaning dialog manager...")
        try:
            self._tts.languageTTS.disconnect(self._con_language)
            self.page_subscriber.signal.disconnect(self.page_connection)
            self._pages_definition.disconnect(self._connection_pagedef)
            self._autonomous_enabled.disconnect(self.connection_autoena)
        except Exception as e:
            self._logger.info("@ Error while cleaning dialog manager: {}".format(e))
        self._logger.info("@ Dialog manager is clean!")

    def _create_pages_triggers_dialog(self, pages_definition):
        self._logger.info("@ Updating dialog concept for pages")
        page_name_list = []
        for page_id in pages_definition.keys():
            page_name = pages_definition[page_id]["title"]
            page_name_list.append(page_name)

        self._session.waitForService("ALDialog")
        dialog = self._session.service("ALDialog")
        dialog.setConcept("applauncher_pages_names", self._current_language_dlg, page_name_list)
        self._logger.info("@ Pages are: {}".format(page_name_list))

    def _on_language_changed(self, new_language):
        self._logger.info("@ Language is now: {}".format(new_language))
        self._current_language_pkg = new_language
        self._current_language_dlg = self._LANGUAGE_FORMAT_CONVERSION[self._current_language_pkg]

    def _on_autonomous_enabled_changed(self, enabled):
        try:
            forbidden = True
            life = self._session.service("ALAutonomousLife")
            if enabled:
                forbidden = False
            self._logger.info("@ Autonomous: {} (forbidden: {})".format(enabled, forbidden))
            life._forbidAutonomousInteractiveStateChange(forbidden)
            if forbidden:
                self._stop_dialog()
            else:
                self._start_dialog()
        except Exception as e:
            self._logger.info("@ Error while changing automous mode: {}".format(e))

    def _start_dialog(self):
        try:
            if self._pref_dialog_always_running:
                self._logger.info("@ dialogAlwaysRunning: True -> starting dialog")
                life = self._session.service("ALAutonomousLife")
                mem = self._session.service("ALMemory")
                mem.insertData("Dialog/DoNotStop", 1)
                life.switchFocus("run_dialog_dev/.")
        except Exception as e:
            self._logger.error("@ Run dialog error: " + str(e))

    def _stop_dialog(self):
        try:
            bm = self._session.service("ALBehaviorManager")
            bm.stopBehavior("run_dialog_dev/.")
        except Exception as e:
            self._logger.error("@ Stop dialog error: " + str(e))

    def on_page_required(self, page_request):
        if page_request == "homepage":
            self._current_page.setValue("Home")
            return
        list_page = self._pages_definition.value()
        for page_id in list_page.keys():
            if page_request in list_page[page_id]["title"]:
                self._current_page.setValue(page_id)
                return
