"""Authenticated snapshot for the Panorama tab, rebuilt from the Squad 1 base by scripts/build_panorama_base.py."""
from pathlib import Path
from fastapi import APIRouter,Depends
from fastapi.responses import FileResponse
from auth import reader
router=APIRouter(prefix='/api/panorama')
DATA=Path(__file__).resolve().parents[2]/'data'/'panorama'
@router.get('')
def panorama(user=Depends(reader)):
    return FileResponse(DATA/'panorama.json',media_type='application/json')
