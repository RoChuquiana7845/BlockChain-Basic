from django.db import transaction
from django.core.management import BaseCommand
from services.blockchain_service import BlockchainService

class Command(BaseCommand):
    help = 'blockchain fill registers'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blockchain_service = BlockchainService()

    def add_arguments(self, parser):
        parser.add_argument('--institutions', type=list, help='Lista de instituciones en formato JSON')
        parser.add_argument('--students', type=list, help='Lista de estudiantes con registros en formato JSON')

    def handle(self, *args, **options):
        institutions = options['institutions']
        students_registers_all = options['students']

        for institution in institutions:
            students_registers = [sr for sr in students_registers_all if sr['institution_id'] == institution['id']]

            for student_register in students_registers:
                try:
                    with transaction.atomic():
                        # Registrar en la blockchain
                        blockchain_hash = self.__process_blockchain(student_register)
                
                        student_register['blockchain_hash'] = blockchain_hash
                        student_register['blockchain_was_register'] = True
                    
                        print(f"Estudiante {student_register['id']} registrado en la blockchain con hash {blockchain_hash}")
                except Exception as e:
                    print(f"Error registrando el estudiante {student_register['id']}: {e}")

    def __process_blockchain(self, student_register):
        auth_id = str(student_register['student']['id'])
        transactions_data = [
            {
                'type': 'registro_estudiante', 
                'data': self.blockchain_service.create_pbnode('file', student_register['irc'].encode())
            }
        ]

        block = self.blockchain_service.add_block(auth_id, transactions_data)
        
        block.save()

        latest_block = self.blockchain_service.get_latest_block()
        return latest_block.hash if latest_block else 'Genesis Block'
