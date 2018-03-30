# -*- coding: utf-8 -*-
import os.path


def find_app_name(logger):
    import re
    path = os.path.dirname(os.path.realpath(__file__))
    match = re.search("(?<=/PackageManager/apps/)(?P<uid>[\w\._-]+)", path)
    if match:
        app_name = match.group(0)
        logger.info("App uuid is {} ".format(app_name))
        return app_name
    else:
        app_name = "app-launcher"
        logger.warning("Unable to find app uuid in path: {}. Defaulting to: {}".format(path, app_name))
        return app_name
