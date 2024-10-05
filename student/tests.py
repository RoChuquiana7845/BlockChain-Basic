from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from student.models import Block, Transaction
from services.blockchain_service import BlockchainService

class BlockchainFillRegistersViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('blockchain_fill_registers')

    @patch('services.blockchain_service.BlockchainService.add_block')
    @patch('services.blockchain_service.BlockchainService.create_pbnode')
    def test_blockchain_fill_registers_success(self, mock_create_pbnode, mock_add_block):
        mock_create_pbnode.return_value = b'mock_data'
        mock_add_block.return_value = mock_add_block
        
        data = {
            "institutions": [
                {"id": 1, "name": "Institution1"},
                {"id": 2, "name": "Institution2"}
            ],
            "students": [
                {"id": 101, "irc": "abcd", "student": {"id": 1}, "institution_id": 1, "blockchain_hash": "", "blockchain_was_register": False}
            ]
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Registros actualizados correctamente")

    def test_blockchain_fill_registers_missing_data(self):
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Instituciones o registros de estudiantes faltantes")


class BlockchainDatabaseTest(TestCase):

    def setUp(self):
        self.blockchain_service = BlockchainService()

    def test_add_block_saves_to_database(self):
        transactions_data = [
            {
                'type': 'registro_estudiante', 
                'data': 'sample_data'  
            }
        ]

        new_block = self.blockchain_service.add_block(auth_id='test_auth_id', transactions_data=transactions_data)

        saved_block = Block.objects.get(index=new_block.index)
        
        print(f"Block index: {saved_block.index}")
        print(f"Block hash: {saved_block.hash}")
        print(f"Block previous hash: {saved_block.previous_hash}")
        print(f"Block validator: {saved_block.validator}")
        print(f"Block data hash: {saved_block.data_hash}")

        self.assertEqual(saved_block.index, new_block.index)
        self.assertEqual(saved_block.hash, new_block.hash)
        self.assertEqual(saved_block.previous_hash, new_block.previous_hash)
        self.assertEqual(saved_block.validator, new_block.validator)
        self.assertEqual(saved_block.data_hash, new_block.data_hash)

        saved_transaction = Transaction.objects.get(block=saved_block)

        decrypted_data = self.blockchain_service.decrypt_data(saved_transaction.data)

        print(f"Transaction type: {saved_transaction.type}")
        print(f"Transaction encrypted data: {saved_transaction.data}")
        print(f"Transaction decrypted data: {decrypted_data}")

        self.assertEqual(saved_transaction.type, transactions_data[0]['type'])
        self.assertEqual(decrypted_data, transactions_data[0]['data'])
