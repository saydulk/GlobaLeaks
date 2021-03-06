import os

from OpenSSL import crypto
from twisted.trial.unittest import TestCase

from globaleaks.utils import letsencrypt

from globaleaks.tests import helpers

class TestRunAcmeReg(TestCase):
    def test_run_acme(self):
        # TODO handle registration
        bad_regr = 'https://not-lets-encrypt.undomain/account/23434'
        pass

    def test_format_asn1_date(self):
        s = '20170827153000Z'

        d = letsencrypt.convert_asn1_date(s)

        self.assertEqual(d.year, 2017)
        self.assertEqual(d.month, 8)
        self.assertEqual(d.day, 27)

    def test_format_as1_date_from_certs(self):
        test_cases = [
            {'path': 'valid/cert.pem',
             'year': 2027,
             'month': 2,
             'day': 25,
            },
            {'path': 'invalid/expired_cert.pem',
             'year': 2017,
             'month': 2,
             'day': 4,
            },
            {'path': 'invalid/glbc_le_stage_cert.pem',
             'year': 2017,
             'month': 8,
             'day': 22,
            },
        ]

        for tc in test_cases:
            path = os.path.join(helpers.DATA_DIR, 'https', tc['path'])
            with open(path, 'r') as f:
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())

            s = cert.get_notAfter()
            date = letsencrypt.convert_asn1_date(s)
            self.assertEquals(date.year, tc['year'])
            self.assertEquals(date.month, tc['month'])
            self.assertEquals(date.day, tc['day'])
