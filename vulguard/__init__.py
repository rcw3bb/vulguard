"""
vulguard - A lightweight security tool that automatically scans source code
for vulnerabilities, highlights risky patterns, and guides developers toward
safer implementations to strengthen their applications' overall security posture.

:author: Ron Webb
:since: 1.0.0
"""

from env_dir_bootstrap import EnvDirBootstrap

__version__ = "1.1.1"

_bootstrapper = EnvDirBootstrap(
    env_var="VULGUARD_CONFIG_DIR",
    resources=["logging.ini", "config.ini"],
    package="vulguard",
)

_bootstrapper.setup()

CONF_DIR = str(_bootstrapper.get_dir())
