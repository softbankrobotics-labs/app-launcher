# -*- coding: utf-8 -*-
import qi
import os
from shutil import copyfile


class IconsStorage:

    def __init__(self, logger, uuid):
        self._logger = logger
        self.icons_path = ""
        self.package_html_upload_folder = ""

        self._logger.info("* Creating icon storage...")

        self.icons_path = qi.path.userWritableDataPath(uuid, "icons")
        self._logger.info("*  - icons path is {}".format(self.icons_path))
        if not os.path.isdir(self.icons_path):
            os.mkdir(self.icons_path)

        copyfile(os.path.join(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "html")), "images", "generic_package_icon.png"), os.path.join(self.icons_path, "generic_package_icon.png"))

        self.package_html_upload_folder = os.path.join(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "html")),"icons")
        self._logger.info("*  - html icons folder is {}".format(self.package_html_upload_folder))
        if not os.path.islink(self.package_html_upload_folder):
            if not os.path.exists(self.package_html_upload_folder):
                os.symlink(self.icons_path, self.package_html_upload_folder)
            elif os.path.isdir(self.package_html_upload_folder):
                self.icons_path = self.package_html_upload_folder

        # @TODO: copy "generic_package_icon.png" into icons_path

        self._logger.info("* ... Icon storage is ready!")

    def cleanup(self):
        self._logger.info("* Cleaning icon storage...")

        if os.path.islink(self.package_html_upload_folder):
            os.unlink(self.package_html_upload_folder)
        elif os.path.isdir(self.package_html_upload_folder):
            os.remove(self.package_html_upload_folder)

        for the_file in os.listdir(self.icons_path):
            file_path = os.path.join(self.icons_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except:
                pass
        if os.path.isdir(self.icons_path):
            try:
                os.remove(self.icons_path)
            except Exception as e:
                self._logger.warning("* {}".format(e))
        self._logger.info("* ... Icon storage is clean!")

    def get_folder_path(self, name):
        return os.path.join(self.icons_path, name)
