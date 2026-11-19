"""QA 04.01: no real client files, no network."""
import unittest
from types import SimpleNamespace
from adjuntos_seguro import reconcile_selection, MAX_FILES, MAX_SIZE


class Uploaded:
    def __init__(self, name="logo.png", data=b"png synthetic", mime="image/png", size=None):
        self.name = name
        self.data = data
        self.type = mime
        self.size = len(data) if size is None else size

    def getvalue(self):
        return self.data


def state():
    return {"attachments_store": [], "answers_store": {}, "files_consent": False}


class AttachmentsFailClosedTests(unittest.TestCase):
    def test_accept_valid_png(self):
        s = state()
        r = reconcile_selection(s, [Uploaded()])
        self.assertTrue(r["ok"])
        self.assertEqual(r["count"], 1)

    def test_clear_attachments_and_consent(self):
        s = state()
        reconcile_selection(s, [Uploaded()])
        s["files_consent"] = True
        s["answers_store"]["files_consent"] = True
        reconcile_selection(s, [])
        self.assertFalse(s["attachments_store"])
        self.assertFalse(s["files_consent"])
        self.assertNotIn("files_consent", s["answers_store"])

    def test_same_files_keep_consent(self):
        s = state()
        reconcile_selection(s, [Uploaded()])
        s["files_consent"] = True
        s["answers_store"]["files_consent"] = True
        r = reconcile_selection(s, [Uploaded()])
        self.assertFalse(r["changed"])
        self.assertTrue(s["files_consent"])

    def test_replacement_invalidates_consent(self):
        s = state()
        reconcile_selection(s, [Uploaded()])
        s["files_consent"] = True
        s["answers_store"]["files_consent"] = True
        r = reconcile_selection(s, [Uploaded(data=b"other")])
        self.assertTrue(r["changed"])
        self.assertFalse(s["files_consent"])
        self.assertNotIn("files_consent", s["answers_store"])

    def test_too_many_files_clears(self):
        s = state()
        reconcile_selection(s, [Uploaded()])
        s["files_consent"] = True
        r = reconcile_selection(s, [Uploaded() for _ in range(MAX_FILES + 1)])
        self.assertFalse(r["ok"])
        self.assertEqual(s["attachments_store"], [])
        self.assertFalse(s["files_consent"])

    def test_large_real_payload_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(data=b"1" * (MAX_SIZE + 1))])["ok"])

    def test_size_mismatch_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(data=b"123", size=2)])["ok"])

    def test_spoofed_mime_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(mime="text/html")])["ok"])

    def test_invalid_name_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(name="../test.png")])["ok"])

    def test_empty_file_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(data=b"")])["ok"])

    def test_unreadable_file_rejected(self):
        s = state()
        bad = Uploaded()
        bad.getvalue = lambda: (_ for _ in ()).throw(IOError("test"))
        self.assertFalse(reconcile_selection(s, [bad])["ok"])

    def test_forged_nonbytes_payload_rejected(self):
        s = state()
        self.assertFalse(reconcile_selection(s, [Uploaded(data="string-data")])["ok"])


if __name__ == "__main__":
    unittest.main()
