# -*- coding: utf-8 -*-


class PreferencesManager:

    def __init__(self, logger, session, domain):
        self._logger = logger
        self._session = session
        self._domain = domain
        self._logger.info("= Creating preferences manager for domain {}...".format(self._domain))
        self._callbacks_list = {}
        self._session.waitForService("ALPreferenceManager")
        self._preference_manager = self._session.service("ALPreferenceManager")
        self._con_preference_added = self._preference_manager.preferenceAdded.connect(self._on_pref_added_or_updated)
        self._con_preference_updated = self._preference_manager.preferenceUpdated.connect(self._on_pref_added_or_updated)
        self._con_preference_removed = self._preference_manager.preferenceRemoved.connect(self._on_pref_removed)
        self._con_domain_removed = self._preference_manager.preferenceDomainRemoved.connect(self._on_domain_removed)
        self._con_preferences_synchronized = self._preference_manager.preferencesSynchronized.connect(self._on_preferences_synchronized)
        self._logger.info("= ... Preferences manager is ready!")

    def cleanup(self):
        self._logger.info("= Cleaning preferences manager...")
        try:
            self._preference_manager.preferencesSynchronized.disconnect(self._con_preferences_synchronized)
            self._preference_manager.preferenceAdded.disconnect(self._con_preference_added)
            self._preference_manager.preferenceUpdated.disconnect(self._con_preference_updated)
            self._preference_manager.preferenceRemoved.disconnect(self._con_preference_removed)
            self._preference_manager.preferenceDomainRemoved.disconnect(self._con_domain_removed)
            self._logger.info("= ... Preferences manager is clean!")

        except Exception as e:
            self._logger.info("error while cleaning preferences manager: {}".format(e))

    def _on_pref_added_or_updated(self, domain, name, value):
        self._logger.info("= Pref added or updated: {}, {}, {}".format(domain, name, value))
        if domain != self._domain:
            return
        try:
            for callback in self._callbacks_list[domain][name]:
                # self._logger.info("Calling {}".format(callback.__name__))
                callback(value)
        except KeyError as e:
            self._logger.warning("= Error: {}".format(e))

    def _on_pref_removed(self, domain, name):
        self._logger.info("= Pref removed: {}, {}".format(domain, name))
        if domain != self._domain:
            return
        try:
            for callback in self._callbacks_list[domain][name]:
                # self._logger.info("Calling {}".format(callback.__name__))
                callback(None)
        except KeyError as e:
            self._logger.warning("= Error: {}".format(e))

    def _on_domain_removed(self, domain):
        self._logger.info("= Pref domain removed: {}".format(domain))
        if domain != self._domain:
            return
        try:
            for name in self._callbacks_list.keys():
                for callback in self._callbacks_list[name]:
                    # self._logger.info("= Calling {}".format(callback.__name__))
                    callback(None)
        except KeyError as e:
            self._logger.warning("= Error: {}".format(e))

    def _on_preferences_synchronized(self):
        self._logger.info("= Pref synchronized!")
        try:
            for name in self._callbacks_list.keys():
                for callback in self._callbacks_list[name]:
                    # self._logger.info("= Calling {}".format(callback.__name__))
                    callback(self._preference_manager.getValue(self._domain, name))
        except KeyError as e:
            self._logger.warning("= Error: {}".format(e))

    def add_callback(self, name, callback):
        self._logger.info("= Adding callback {} to preference {}".format(callback.__name__, name))
        if not (name in self._callbacks_list.keys()):
            self._callbacks_list[name] = []
        self._callbacks_list[name].append(callback)

    def get_value(self, name, default):
        domain = self._domain
        v = False
        try:
            v = self._preference_manager.getValue(domain, name)
        except Exception as e:
            self._logger.error("= Error getting preference {}: {}".format(name, e))
        if v:
            return v
        else:
            return default

    def get_subdomain_value_list(self, subdomain):
        return self._preference_manager.getValueList(self._domain+"."+subdomain)
