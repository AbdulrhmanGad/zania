# Copyright (C) 2021 TREVI Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import base64

from cryptography.fernet import Fernet

from odoo.tests.common import TransactionCase


class TestAccess(TransactionCase):
    def setUp(self):
        super().setUp()

        self.ItAccess = self.env["itm.access"]
        self.ItSite = self.env["itm.site"]
        self.defaultSite = self.ItSite.create({"name": "site"})

        # Prime salt and decryption password creation
        self.ItAccess.create(
            {"name": "a", "password": "a", "site_id": self.defaultSite.id}
        )

    def _decrypt(self, ciphertext):
        key = self.ItAccess.get_urlsafe_key()
        f = Fernet(key)

        token = base64.urlsafe_b64decode(ciphertext)
        plaintext = f.decrypt(token).decode()
        return plaintext

    def test_change_password(self):
        """Changing password results in encrypted version of new password"""

        cred = self.ItAccess.create(
            {"name": "a", "password": "123", "site_id": self.defaultSite.id}
        )
        self.assertEqual("123", self._decrypt(cred.password))
        cred.write({"password": "456"})
        self.assertEqual("456", self._decrypt(cred.password))

    def test_random_password(self):
        """Random password isn't mangled"""

        # Not sure there's a way to test randomness. Just test that
        # it's the expected length.
        #
        cred = self.ItAccess.create({"name": "a", "site_id": self.defaultSite.id})
        self.assertFalse(cred.password)
        cred.get_random_password()
        strRandom = self.ItAccess.decrypt_password_as_string(cred.id)
        self.assertEqual(16, len(strRandom))
