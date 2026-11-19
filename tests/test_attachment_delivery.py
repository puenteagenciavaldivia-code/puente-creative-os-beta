import base64
import unittest
from attachment_delivery import send_pending, fingerprint, AttachmentDeliveryError

def item(name, content=b'abc', mime='image/png'):
    return {'name': name, 'mime': mime, 'data': base64.b64encode(content).decode()}

class Response:
    def __init__(self, status_code=200, text='OK'):
        self.status_code = status_code
        self.text = text

class AttachmentTests(unittest.TestCase):
    def setUp(self):
        self.ledger = {}
        self.files = [item('a.png'), item('b.png', b'xyz')]
        self.calls = []
    def post(self, url, json, timeout):
        self.calls.append(json['attachment_key'])
        return Response()
    def send(self, post=None, files=None, sub='SUB-1'):
        return send_pending(sub, 'Marca ficticia', self.files if files is None else files, self.ledger, post or self.post, 'https://example.invalid', 'token-ficticio')
    def test_two_success(self):
        self.assertEqual(self.send(), (2, 2))
        self.assertEqual(len(self.calls), 2)
    def test_rerun_skips_confirmed(self):
        self.send()
        self.send()
        self.assertEqual(len(self.calls), 2)
    def test_partial_failure_resumes(self):
        calls = []
        def first(url, json, timeout):
            calls.append(json['attachment_key'])
            return Response() if len(calls) == 1 else Response(500, 'ERROR')
        with self.assertRaises(AttachmentDeliveryError):
            self.send(first)
        self.assertEqual(len(self.ledger['SUB-1']['confirmed']), 1)
        self.assertEqual(self.send(), (2, 2))
        self.assertEqual(len(self.calls), 1)
    def test_timeout_is_ambiguous(self):
        def fail(url, json, timeout):
            raise TimeoutError()
        with self.assertRaises(TimeoutError):
            self.send(fail)
        self.assertEqual(self.ledger['SUB-1']['confirmed'], [])
    def test_manifest_change_blocked(self):
        self.send()
        with self.assertRaises(AttachmentDeliveryError):
            self.send(files=[item('a.png')])
    def test_duplicate_files_blocked(self):
        with self.assertRaises(AttachmentDeliveryError):
            self.send(files=[item('a.png'), item('a.png')])
    def test_too_many_files(self):
        with self.assertRaises(AttachmentDeliveryError):
            self.send(files=[item(str(i)) for i in range(6)])
    def test_too_large(self):
        with self.assertRaises(AttachmentDeliveryError):
            fingerprint(item('huge.png', b'x' * (3 * 1024 * 1024 + 1)))
    def test_invalid_mime(self):
        with self.assertRaises(AttachmentDeliveryError):
            fingerprint(item('x.exe', mime='application/octet-stream'))
    def test_invalid_base64(self):
        with self.assertRaises(AttachmentDeliveryError):
            fingerprint({'name':'x.png','mime':'image/png','data':'!!'})
    def test_same_content_different_name_distinct(self):
        self.assertNotEqual(fingerprint(item('x.png')), fingerprint(item('y.png')))
    def test_new_submission_resends(self):
        self.send()
        self.send(sub='SUB-2')
        self.assertEqual(len(self.calls), 4)
    def test_non_ok_response(self):
        def bad(url, json, timeout):
            return Response(200, 'DENIED')
        with self.assertRaises(AttachmentDeliveryError):
            self.send(bad)
    def test_empty(self):
        self.assertEqual(self.send(files=[]), (0, 0))
