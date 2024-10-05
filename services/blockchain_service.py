from django.utils import timezone
from cryptography.fernet import Fernet
from student.models import Block, Transaction
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from services.proto import merkledag_pb2  
from services.proto import unixfs_pb2
import hashlib
import random

class BlockchainService:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.validators = {
            "Validator1": 100,
            "Validator2": 200,
            "Validator3": 300
        }
        self.stake_amount = 100
        self.create_genesis_block()

    def create_genesis_block(self):
        try:
            Block.objects.get(index=0)
        except ObjectDoesNotExist:
            genesis_data = self.create_pbnode('raw', b'Genesis Block')
            genesis_block = Block(
                index=0,
                previous_hash='0',
                timestamp=timezone.now(),
                data_hash='Genesis Block',
                hash=self.calculate_hash(0, '0', genesis_data , ''),
                validator="Genesis Validator"
            )
            genesis_block.save()

    def calculate_hash(self, index, previous_hash, data_hash, transaction_hashes):
        index = str(index) if index is not None else ''
        previous_hash = previous_hash or ''
        data_hash = data_hash or ''
        transaction_hashes = transaction_hashes or ''
        hash_input = f'{index}{previous_hash}{data_hash}{transaction_hashes}'.encode()
        return hashlib.sha256(hash_input).hexdigest()

    def create_pbnode(self, data_type, data_bytes):
        unixfs_data = unixfs_pb2.Data()
        if data_type == 'file':
            unixfs_data.Type = unixfs_pb2.Data.File
        elif data_type == 'directory':
            unixfs_data.Type = unixfs_pb2.Data.Directory
        else:
            unixfs_data.Type = unixfs_pb2.Data.Raw

        unixfs_data.Data = data_bytes
        unixfs_data.filesize = len(data_bytes)

        serialized_data = unixfs_data.SerializeToString()
        
        pbnode = merkledag_pb2.PBNode()
        pbnode.Data = serialized_data

        return pbnode.SerializeToString()

    def calculate_merkle_root_from_pbnode(self, pbnode):
        transaction_hashes = [hashlib.sha256(f"{tx.type}{tx.data}{tx.previous_transaction_hash}".encode()).hexdigest() for tx in pbnode.transactions]
        if not transaction_hashes:
            return None

        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 == 1:
                transaction_hashes.append(transaction_hashes[-1])

            new_level = []
            for i in range(0, len(transaction_hashes), 2):
                combined_hash = hashlib.sha256(
                    (transaction_hashes[i] + transaction_hashes[i + 1]).encode()
                ).hexdigest()
                new_level.append(combined_hash)
                
            transaction_hashes = new_level
            
        return transaction_hashes[0]

    @transaction.atomic
    def add_block(self, auth_id, transactions_data):
        latest_block = self.get_latest_block()
        previous_hash = latest_block.hash if latest_block else '0'
        
        
        new_block = Block(
            index=latest_block.index + 1 if latest_block else 0,
            previous_hash=previous_hash,
            timestamp=timezone.now(),
            validator=self.select_validator()
        )
        new_block.save()
        
        previous_transaction_hash = ''
        pbnode = merkledag_pb2.PBNode()
        for tx_data in transactions_data:
            if isinstance(tx_data['data'], bytes):
                encrypted_data = self.cipher_suite.encrypt(tx_data['data'])
            else:
                encrypted_data = self.cipher_suite.encrypt(tx_data['data'].encode())
            tx = Transaction(
                type=tx_data['type'],
                data=encrypted_data.decode(),
                hash=self.generate_transaction_hash(tx_data['type'], tx_data['data'], previous_transaction_hash),
                block=new_block
            )
            previous_transaction_hash = tx.hash
            tx.save()
        
        pbnode.transactions.append(merkledag_pb2.Transaction(
            type=tx_data['type'],
            data=encrypted_data.decode(),
            previous_transaction_hash=previous_transaction_hash
        ))
        
        merkle_root = self.calculate_merkle_root_from_pbnode(pbnode)
        
        new_block.data_hash = self.calculate_hash(new_block.index, new_block.previous_hash, auth_id, merkle_root)
        new_block.hash = new_block.data_hash
        new_block.save()
        
        return new_block
    
    def select_validator(self):
        eligible_validators = [v for v, stake in self.validators.items() if stake >= self.stake_amount]
        return random.choice(eligible_validators) if eligible_validators else "No valid validator"

    def generate_transaction_hash(self, tx_type, data, previous_transaction_hash):
        return hashlib.sha256(f'{tx_type}{data}{previous_transaction_hash}'.encode()).hexdigest()

    def get_latest_block(self):
        return Block.objects.order_by('-index').first()
    
    def decrypt_data(self, encrypted_data):
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        return decrypted_data