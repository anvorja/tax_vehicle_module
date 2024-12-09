class DocumentService:
    @staticmethod
    def validate_document_number(doc_type: str, number: str) -> bool:
        """Valida el número de documento según su tipo"""
        if not doc_type or not number:
            return False

        # Reglas específicas por tipo de documento
        validators = {
            'CC': lambda x: x.isdigit() and len(x) <= 10,
            'CE': lambda x: len(x) <= 12,
            'NIT': lambda x: x.replace('-', '').isdigit() and len(x) <= 11,
            'PP': lambda x: len(x) <= 15
        }

        return validators.get(doc_type, lambda x: True)(number)

    @staticmethod
    def format_document_number(doc_type: str, number: str) -> str:
        """Formatea el número de documento según su tipo"""
        if doc_type == 'NIT':
            # Formato: XXXXXXXXX-D
            base = number.replace('-', '')
            if len(base) > 9:
                return f"{base[:-1]}-{base[-1]}"
        return number
