from distutils import dir_util
import os
import pytest
import shutil
import tempfile

@pytest.fixture
def tmpfile():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name

def tmpdir():
    with tempfile.mkdtemp() as f:
        yield f
    shutil.rmtree(f)


@pytest.fixture
def datadir(tmpdir, request):
    '''
    Fixture responsible for searching a folder with the same name of test
    module and, if available, moving all contents to a temporary directory so
    tests can use them freely.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(tmpdir))

    return tmpdir
