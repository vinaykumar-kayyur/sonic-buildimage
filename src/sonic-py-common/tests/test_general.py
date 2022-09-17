import sys
import pytest
import subprocess
from sonic_py_common.general import getstatusoutput_noshell, getstatusoutput_noshell_pipes, check_output_pipes


def test_getstatusoutput_noshell(tmp_path):
    exitcode, output = getstatusoutput_noshell(['echo', 'sonic'])
    assert (exitcode, output) == (0, 'sonic')

    exitcode, output = getstatusoutput_noshell([sys.executable, "-c", "import sys; sys.exit(6)"])
    assert exitcode != 0

def test_getstatusoutput_noshell_pipes():
    exitcode, output = getstatusoutput_noshell_pipes(dict(args=['echo', 'sonic']), dict(args=['awk', '{print $1}']))
    assert (exitcode, output) == ([0, 0], 'sonic')

    exitcode, output = getstatusoutput_noshell_pipes(dict(args=[sys.executable, "-c", "import sys; sys.exit(6)"]), dict(args=[sys.executable, "-c", "import sys; sys.exit(8)"]))
    assert exitcode == [6, 8]

def test_check_output_pipes():
    output = check_output_pipes(dict(args=['echo', 'sonic']), dict(args=['awk', '{print $1}']))
    assert output == 'sonic\n'

    with pytest.raises(subprocess.CalledProcessError) as e:
        check_output_pipes(dict(args=[sys.executable, "-c", "import sys; sys.exit(6)"]), dict(args=[sys.executable, "-c", "import sys; sys.exit(0)"]))
        assert e.returncode == [6, 0]

    with pytest.raises(subprocess.CalledProcessError) as e:
        check_output_pipes(dict(args=[sys.executable, "-c", "import sys; sys.exit(0)"]), dict(args=[sys.executable, "-c", "import sys; sys.exit(6)"]))
        assert e.returncode == [0, 6]
