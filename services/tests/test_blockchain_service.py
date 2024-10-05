from django.test import TestCase
from unittest.mock import patch
from services.blockchain_service import BlockchainService
from student.models import Transaction

class BlockchainServiceTest(TestCase):

    def setUp(self):
        self.blockchain_service = BlockchainService()

    @patch('services.blockchain_service.BlockchainService.calculate_hash')
    def test_add_block(self, mock_calculate_hash):
        mock_calculate_hash.return_value = 'mocked_hash'

        auth_id = '12345'
        transactions_data = [
            {
                'type': 'registro_estudiante',
                'data': 'mock_data'  
            }
        ]

        block = self.blockchain_service.add_block(auth_id, transactions_data)

        self.assertIsNotNone(block)
        self.assertEqual(block.hash, 'mocked_hash')

        saved_transaction = Transaction.objects.get(block=block)

        self.assertNotEqual(saved_transaction.data, 'mock_data')

        decrypted_data = self.blockchain_service.decrypt_data(saved_transaction.data)
        self.assertEqual(decrypted_data, 'mock_data')

    def test_calculate_hash(self):
        hash_value = self.blockchain_service.calculate_hash(1, 'prev_hash', 'data_hash', 'tx_hashes')
        print(f'Calculated hash: {hash_value}')
        self.assertEqual(hash_value, 'e049f3da36850b2feb12100fe03183f92cb0d49e1ed602c1b388d2754121642d')

    def test_encryption_and_decryption(self):
        original_data = 'data_to_encrypt'

        encrypted_data = self.blockchain_service.cipher_suite.encrypt(original_data.encode()).decode()

        self.assertNotEqual(encrypted_data, original_data)

        decrypted_data = self.blockchain_service.decrypt_data(encrypted_data)

        self.assertEqual(decrypted_data, original_data)
