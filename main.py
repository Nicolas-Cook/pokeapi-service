from fastapi import FastAPI, Depends, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import httpx
from typing import List, Annotated
from auth import get_current_user, fake_hash_password, fake_users_db
from user import UserInDB
from exceptions import PokemonNotFoundError, InvalidPokemonNameError, AuthenticationError, GenerationNotFoundError, InvalidGenerationNameError

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Autenticación de usuario.

    Recibe un formulario con el campo "username" y "password".

    Si el usuario existe y la contraseña es correcta, devuelve un token de
    autenticación en el formato "bearer" para futuras peticiones (requests).
    """
    
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise AuthenticationError()
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise AuthenticationError()

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/pokemon/{pokemon_name}")
async def get_pokemon(pokemon_name: str, token: Annotated[str, Depends(get_current_user)]):
    """
    Obtiene la información de un pokémon por su nombre.
        
    Returns:
        La información del pokémon.
    """
    if not pokemon_name.isalpha():
        raise InvalidPokemonNameError(pokemon_name)
    pokemon_name = pokemon_name.lower()
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 404:
            raise PokemonNotFoundError(pokemon_name)
        data = response.json()
        shiny_image = data["sprites"]["front_shiny"]
        name = data["name"]
        type_ = [t["type"]["name"] for t in data["types"]]
        weight = data["weight"]
        height = data["height"]
        stats = [ {"name": s["stat"]["name"], "value": s["base_stat"]} for s in data["stats"] if s["stat"]["name"] in ["attack", "defense",]]
        moves = []
        for move in data["moves"]:
            move_url = move["move"]["url"]
            move_response = await client.get(move_url)
            move_data = move_response.json()
            move_power = move_data["power"]
            moves.append({"name": move["move"]["name"], "power": move_power})
        moves = [move for move in moves if move["power"] is not None]
        moves = sorted(moves, key=lambda x: x["power"], reverse=True)[:3]
        return {"shiny_image": shiny_image, "name": name, "type": type_, "weight": weight, "height": height, "stats": stats, "moves": moves}

@app.get("/generation/{generation}", response_model=List[str])
async def get_generation(
    generation: int,
    token: Annotated[str, Depends(get_current_user)],
    page: int = Query(1, gt=0),  
    page_size: int = Query(20, gt=0, le=100) 
):
    """
    Obtiene la lista de nombres de pokémon de una generación.
    
    Args:
        generation: La generación de los pokémon.
        page: El número de página de la lista.
        page_size: El tamaño de cada página.
    
    Returns:
        La lista de nombres de pokémon.
    """
    url = f"https://pokeapi.co/api/v2/generation/{generation}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 404:
            raise GenerationNotFoundError(generation)
        if response.status_code == 400:
            raise InvalidGenerationNameError(generation)
        data = response.json() 
        pokemon_names = [pokemon['name'] for pokemon in data['pokemon_species']]
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_names = pokemon_names[start_index:end_index]
        
        return paginated_names
    
