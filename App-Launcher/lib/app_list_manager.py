# -*- coding: utf-8 -*-
from storage import IconsStorage
import os.path
import json


class AppListManager:

    _LANGUAGE_FORMAT_CONVERSION = dict(en_US="English", fr_FR="French", ja_JP="Japanese", zh_CN="Chinese",
                                       es_ES="Spanish", de_DE="German", ko_KR="Korean", it_IT="Italian", nl_NL="Dutch",
                                       fi_FI="Finnish", pl_PL="Polish", ru_RU="Russian", tr_TR="Turkish",
                                       ar_SA="Arabic", cs_CZ="Czech", pt_PT="Portuguese", pt_BR="Brazilian",
                                       sv_SE="Swedish", da_DK="Danish", nn_NO="Norwegian", el_GR="Greek")

    def __init__(self, logger, session, pref_manager, app_uuid, apps_full_list_prop, apps_by_page_prop):
        self._logger = logger
        self._session = session
        self._logger.info("+ Creating app list manager...")

        # connect services
        self._session.waitForService("PackageManager")
        self._package_manager = self._session.service("PackageManager")
        self._session.waitForService("ALTextToSpeech")
        self._tts = self._session.service("ALTextToSpeech")

        # public variables
        self.apps_full_list = apps_full_list_prop
        self.apps_by_page = apps_by_page_prop

        # private variables
        self._app_uuid = app_uuid
        self._current_language = None
        self._current_language_pkg = None
        self._pref_hide_system_apps = None
        self._pref_hide_crg_app = None
        self._preferences_manager = pref_manager
        self._icons_storage = IconsStorage(self._logger, self._app_uuid)
        self.pref_pages_definition = {}
        temp_pref = self._preferences_manager.get_subdomain_value_list("page")
        if temp_pref:
            # For each page in preferences
            for page in temp_pref:
                # Double quote are not allowed in cloud preferences, so we use
                # simple quote and they are replaced here to stick to json format
                self.pref_pages_definition[page[0]] = json.loads(page[1].replace('\'', '"'))
        else:
            # Get the path of the file "defaultPreferences.json"
            url = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                'defaultPreferences.json'))
            with open(url) as openUrl:
                # Load the json
                self.pref_pages_definition = json.load(openUrl)
        self._logger.info("+ Pages definition is: {}".format(self.pref_pages_definition))

        # init vars
        self._on_language_changed(self._tts.locale())
        self._on_hide_system_apps_changed(self._preferences_manager.get_value("hideSystemApps", False))
        self._on_hide_crg_app_changed(self._preferences_manager.get_value("hideChoregrapheTestApp", True))
        self.update_app_lists(None, update_icons=True)

        # connect callbacks
        self._preferences_manager.add_callback("hideSystemApps", self._on_hide_system_apps_changed)
        self._preferences_manager.add_callback("hideChoregrapheTestApp", self._on_hide_crg_app_changed)

        self._con_package_installed = self._package_manager.onPackageInstalled.connect(self.update_app_lists)
        self._con_package_removed = self._package_manager.onPackageRemoved.connect(self.update_app_lists)
        self._con_language = self._tts.languageTTS.connect(self._on_language_changed)

        self._logger.info("+ ... App list manager is ready!")

    def cleanup(self):
        self._logger.info("+ Cleaning app list manager...")

        try:
            # disconnect from signals
            self._tts.languageTTS.disconnect(self._con_language)
            self._package_manager.onPackageRemoved.disconnect(self._con_package_removed)
            self._package_manager.onPackageInstalled.disconnect(self._con_package_installed)

            # clean variables
            self._icons_storage.cleanup()

            self._logger.info("+ ... App list manager is clean!")

        except Exception as e:
            self._logger.info("+ error while cleaning app list manager: {}".format(e))


    """
    CALLBACK FUNCTIONS
    """

    def _on_hide_system_apps_changed(self, new_value):
        self._pref_hide_system_apps = new_value

    def _on_hide_crg_app_changed(self, new_value):
        self._pref_hide_crg_app = new_value

    def _on_language_changed(self, new_language):
        self._logger.info("+ Language is now: {}".format(new_language))
        self._current_language_pkg = new_language
        self._current_language = self._LANGUAGE_FORMAT_CONVERSION[self._current_language_pkg]
        self.update_app_lists(None)

    """
    HELPERS
    """

    def _get_app_icon(self, uuid, create_icon=True):
        name = "{}.png".format(uuid)
        file_path = self._icons_storage.get_folder_path(name)
        if not os.path.isfile(file_path) or create_icon:
            icon = self._package_manager.packageIcon(uuid)
            if len(icon) > 0:
                with open(file_path, "wb") as fh:
                    fh.write(icon)
            else:
                name = "generic_package_icon.png"

        return "/apps/{}/icons/{}".format(self._app_uuid, name)

    """
    PUBLIC (to applauncher) FUNCTIONS
    """

    def update_app_lists(self, useless_package_info, update_icons=False):
        """Reloads the list of applications to display.
        This method will update the property: apps_full_list"""
        full_list = []
        pkg_list = self._package_manager.packages()
        for pkg in pkg_list:
            if pkg["installer"] == "system" and self._pref_hide_system_apps:
                continue
            if pkg["uuid"] == ".lastUploadedChoregrapheBehavior" and self._pref_hide_crg_app:
                continue
            for behavior in pkg["behaviors"]:
                if behavior["userRequestable"]:
                    behavior_name = pkg["uuid"]
                    if len(pkg["supportedLanguages"]) == 0 or self._current_language_pkg in pkg["supportedLanguages"]:
                        if self._current_language_pkg in behavior["langToName"].keys():
                            behavior_name = behavior["langToName"][self._current_language_pkg]
                        elif self._current_language_pkg in pkg["langToName"].keys():
                            behavior_name = pkg["langToName"][self._current_language_pkg]
                        elif self._current_language_pkg in behavior["langToTriggerSentences"].keys():
                            for trigger in behavior["langToTriggerSentences"][self._current_language_pkg]:
                                if len(trigger) > 0:
                                    behavior_name = trigger
                                    break
                    else:
                        behavior_name = "# {} not supported #".format(self._current_language)
                    icon_url = self._get_app_icon(pkg["uuid"], update_icons)
                    full_list.append({"uuid": pkg["uuid"],
                                      "behavior_path": behavior["path"],
                                      "name": behavior_name,
                                      "icon": icon_url})

        apps_full_list = sorted(full_list, key=lambda app: app["name"].lower())

        page_list = {}

        for page_id in self.pref_pages_definition.keys():
            page_title = "# {} title missing #".format(self._current_language)
            page_apps = {}

            if self._current_language in self.pref_pages_definition[page_id]["title"].keys():
                page_title = self.pref_pages_definition[page_id]['title'][self._current_language]
            elif 'English' in self.pref_pages_definition[page_id]['title'].keys():
                page_title = self.pref_pages_definition[page_id]['title']['English']

            for uuid in self.pref_pages_definition[page_id]["apps"]:
                for app_desc in [ad for ad in apps_full_list if ad["uuid"] == uuid]:
                    page_apps[len(page_apps)] = app_desc

            page_list[page_id] = {"title": page_title, "apps": page_apps}

        self.apps_full_list.setValue(apps_full_list)
        self.apps_by_page.setValue(page_list)
