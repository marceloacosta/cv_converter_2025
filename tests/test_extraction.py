import io
from extraction import extract_text_from_file


class FakeFile:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._buf = io.BytesIO(content)

    def read(self):
        return self._buf.read()

    def seek(self, n):
        self._buf.seek(n)


def test_extract_txt():
    f = FakeFile("resume.txt", b"John Doe\nSoftware Engineer")
    result = extract_text_from_file(f)
    assert "John Doe" in result
    assert "Software Engineer" in result


def test_extract_unsupported():
    f = FakeFile("resume.xyz", b"anything")
    result = extract_text_from_file(f)
    assert result == ""
