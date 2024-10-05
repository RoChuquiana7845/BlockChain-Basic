from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from services.blockchain_service import BlockchainService
from django.db import transaction

class BlockchainFillRegistersView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blockchain_service = BlockchainService()

    def post(self, request):
        institutions = request.data.get('institutions', [])
        students_registers_all = request.data.get('students', [])

        if not institutions or not students_registers_all:
            return Response({"error": "Instituciones o registros de estudiantes faltantes"}, status=status.HTTP_400_BAD_REQUEST)

        for institution in institutions:
            students_registers = [sr for sr in students_registers_all if sr['institution_id'] == institution['id']]

            for student_register in students_registers:
                try:
                    with transaction.atomic():
                        blockchain_hash = self.__process_blockchain(student_register)
                        
                        student_register['blockchain_hash'] = blockchain_hash
                        student_register['blockchain_was_register'] = True
                        
                        print(f"Estudiante {student_register['id']} registrado en la blockchain con hash {blockchain_hash}")
                except Exception as e:
                    print(f"Error registrando el estudiante {student_register['id']}: {e}")
                    return Response({"error": f"Error registrando el estudiante {student_register['id']} - {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Registros actualizados correctamente"}, status=status.HTTP_200_OK)

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
