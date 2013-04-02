import glob
import os
import sys
import logging

logger = logging.getLogger(__name__)

import yaml

class InvalidConfig(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return "Unable to open config file %s." % (self.filename)

def load_config(config_file='config.yaml'):
    stack = []
    root = os.path.split(os.path.abspath(config_file))[0]
    def recursive_preprocess(filename):
        stack.append(os.path.abspath(filename))
        c = []
        try:
            fd = open(filename)
        except IOError, e:
            # This should only happen with the top level config file, since
            # we use glob.glob on includes
            if e.errno == 2:
                logger.warning("Could not find file '%s'.  Skipping." % (
                    filename))
                return c
            if e.errno == 13:
                logger.warning("Invalid permissions to open '%s'. "
                        "Skipping." % (filename))
                return c
            raise

        with fd:
            for lineno, line in enumerate(fd):
                line = line.rstrip()
                if line.startswith('!include '):
                    path = line.split(None, 1)[1]
                    # if the include doesn't have a fully qualified path then
                    # assume the relative path is based off the directory of
                    # the initial config file
                    if not path.startswith('/'):
                        path = os.path.join(root, path)
                    files = glob.glob(path)
                    if not files:
                        logger.warning("Include statement '%s' at %s:%d did "
                                "not match any files.  Skipping." % (line,
                                        filename, lineno))
                        continue
                    for f in files:
                        f = os.path.abspath(f)
                        if f in stack:
                            logger.warning("Already parsed %s, skipping "
                                    "(%s:%d) to avoid infinite loop." % (f,
                                            filename, lineno))
                            continue
                        if os.path.isfile(f):
                            logger.info("Parsing include (%s:%d): %s" % (
                                    filename, lineno, f))
                            c.extend(recursive_preprocess(f))
                        else:
                            logger.warning("%s is not a regular file, "
                                    "skipping (%s:%d)." % (f, filename,
                                            lineno))
                    continue
                c.append(line)
        return c
    logger.info("Loading config file: %s" % (config_file))
    config = recursive_preprocess(config_file)
    if not config:
        raise InvalidConfig(config_file)
    return yaml.safe_load(os.linesep.join(config))
