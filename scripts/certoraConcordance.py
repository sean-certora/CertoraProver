#!/usr/bin/env python3
#      The Certora Prover
#      Copyright (C) 2025  Certora Ltd.
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, version 3 of the License.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Bootstrap: use bundled Python if available
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from Shared.certoraBootstrap import maybe_reexec_into_bundled_python
maybe_reexec_into_bundled_python()

import sys
from concordance.main import main

if __name__ == "__main__":
    sys.exit(main())
