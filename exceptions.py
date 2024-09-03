from fastapi import HTTPException

class PokemonNotFoundError(HTTPException):
    def __init__(self, pokemon_name: str):
        super().__init__(status_code=404, detail=f"Pokémon '{pokemon_name}' no encontrado")

class InvalidPokemonNameError(HTTPException):
    def __init__(self, pokemon_name: str):
        super().__init__(status_code=400, detail=f"Nombre de Pokémon '{pokemon_name}' inválido")

class AuthenticationError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Autenticación fallida")
        
class GenerationNotFoundError(HTTPException):
    def __init__(self, generation_name: str):
        super().__init__(status_code=404, detail=f"Generación '{generation_name}' no encontrada")

class InvalidGenerationNameError(HTTPException):
    def __init__(self, generation_name: int):
        super().__init__(status_code=400, detail=f"Numero de generación '{generation_name}' inválido")