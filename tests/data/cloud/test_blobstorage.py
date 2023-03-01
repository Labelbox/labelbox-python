from labelbox.data.cloud.blobstorage import extract_file_path


def test_extract_file_path():
    path = "https://storage-acct-name.blob.core.windows.net/container/imgs/1001.jpg"
    assert extract_file_path(path) == "imgs/1001.jpg"

    assert extract_file_path("") == ""
    assert extract_file_path("/") == ""
    assert extract_file_path("https://storage-acct-name.blob.core.windows.net/") == ""
