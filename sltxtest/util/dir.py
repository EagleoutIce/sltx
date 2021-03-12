import tempfile


def retrieve_tmpdir():
    return tempfile.mkdtemp('sltxxtest')