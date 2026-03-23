#     The Certora Prover
#     Copyright (C) 2025  Certora Ltd.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Bootstrap module to automatically use the bundled Python if available.

This module re-execs into the bundled Python installation (.certora_python)
when available, providing users with a self-contained environment without
requiring them to set up a virtual environment manually.
"""

import os
import sys
from pathlib import Path


def maybe_reexec_into_bundled_python() -> None:
	"""
	If the bundled Python is available and we are not already running inside it,
	re-exec into it. This function never returns when it re-execs.

	This is designed to be called early in entry scripts, before any certora
	imports that might fail if dependencies aren't installed in the system Python.
	"""
	# Guard: already bootstrapped (avoids infinite recursion)
	if os.environ.get("CERTORA_BOOTSTRAP_DONE") == "1":
		return

	bundled_python = _find_bundled_python()
	if bundled_python is None:
		return  # PyPI install or developer machine - nothing to do

	# Check if we are already running the bundled Python
	# (covers the case where the user has manually set PATH to include it)
	current_exe = Path(sys.executable).resolve()
	if current_exe == bundled_python.resolve():
		return

	# Mark environment so the re-exec'd process skips this block
	env = {**os.environ, "CERTORA_BOOTSTRAP_DONE": "1"}

	# Sanitize Python-related environment variables to ensure complete isolation
	# from any activated venv or system Python environment. This guarantees that
	# the bundled Python has a clean environment and won't accidentally import
	# packages from a user's venv or system Python.
	_sanitize_python_environment(env)

	if sys.platform == "win32":
		# os.execve is available on Windows but is less reliable with
		# inherited handles; use subprocess + sys.exit instead.
		import subprocess
		result = subprocess.run(
			[str(bundled_python)] + sys.argv,
			env=env
		)
		sys.exit(result.returncode)
	else:
		# Replace the current process in-place (zero overhead, same PID,
		# which is important for process managers and signal handling).
		os.execve(str(bundled_python), [str(bundled_python)] + sys.argv, env)
		# os.execve does not return.


def _find_bundled_python() -> Path | None:
	"""
	Return the path to the bundled Python binary, or None if not present.
	Looks for the binary relative to the directory of the calling script
	(sys.argv[0]), then relative to $CERTORA.
	"""
	# Prefer the sibling .certora_python next to the scripts directory.
	# When installed via copy-assets, scripts land directly in $CERTORA,
	# so this is $CERTORA/.certora_python.
	script_dir = Path(sys.argv[0]).resolve().parent

	candidates = [script_dir / ".certora_python"]
	certora_env = os.environ.get("CERTORA")
	if certora_env:
		candidates.append(Path(certora_env) / ".certora_python")

	for base in candidates:
		if sys.platform == "win32":
			binary = base / "Scripts" / "python.exe"
		else:
			binary = base / "install" / "bin" / "python3"
		if binary.is_file():
			return binary
	return None


def _sanitize_python_environment(env: dict[str, str]) -> None:
	"""
	Remove Python-specific environment variables that could cause the bundled
	Python to import packages from a user's venv or system Python.

	Clears:
	- PYTHONPATH: Custom module search paths
	- PYTHONHOME: Standard library location (could be wrong for bundled Python)
	- PYTHONUSERBASE: User site-packages location
	- VIRTUAL_ENV: Marker set by venv activation
	- PYTHONEXECUTABLE: Could confuse subprocesses about which Python to use

	This ensures 100% isolation: running Certora Prover will never accidentally
	use packages from an activated venv or system Python, even if those are set
	in the user's environment.
	"""
	for var in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE", "VIRTUAL_ENV", "PYTHONEXECUTABLE"):
		env.pop(var, None)
