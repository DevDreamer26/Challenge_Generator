from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.db import (
    get_challenge_quota,
    create_challenge, create_challenge_quota,
    reset_quota_if_needed, get_user_challenges
)
from ..utils import Authenticate_and_get_user_details 
from ..database.db import get_db
import json
from datetime import datetime
from ..ai_generator import generate_challenge_with_ai
from ..database.models import Challenge

router = APIRouter()

class ChallengeRequest(BaseModel):
    difficulty: str
    
    class config:
        json_schema_extra = {"example": {"difficulty":"easy"}}

# --- Dependency to get user_id ---
def get_current_user_id(request: Request):
    user_details = Authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated or user ID missing.")
    return user_id


@router.post("/generate-challenge")
async def generate_challenge(request: ChallengeRequest, request_obj: Request, db: Session = Depends(get_db)):
    try:
        user_details = Authenticate_and_get_user_details(request_obj)
        user_id = user_details.get("user_id")
        
        quota = get_challenge_quota(db, user_id)
        if not quota:
            create_challenge_quota(db, user_id)
            
        quota = reset_quota_if_needed(db, quota)

        if quota.quota_remaining <= 0 :
            raise HTTPException(status_code=429, detail="Quota Exhausted")
        
        try:
            challenge_data = generate_challenge_with_ai(request.difficulty)
        except Exception as e :
            raise HTTPException(status_code=500, detail=str(e))
            
        new_challenge = create_challenge(
            db =  db,
            difficulty=request.difficulty,
            created_by=user_id,
            title=challenge_data["title"],
            options=json.dumps(challenge_data["options"]),
            correct_answer_id=challenge_data["correct_answer_id"],
            explanation=challenge_data["explanation"]
        )
        
        quota.quota_remaining -= 1
        db.commit()
         
        return {
            "id": new_challenge.id,
            "difficulty": request.difficulty,
            "title": new_challenge.title,
            "options": json.loads(new_challenge.options),
            "correct_answer_id": new_challenge.correct_answer_id,
            "explanation": new_challenge.explanation,
            "timestamp": new_challenge.date_created.isoformat()
        }
        
    except Exception as e:
        print(f"Error in generate_challenge: {e}") 
        raise HTTPException(status_code=400, detail="Failed to generate challenge.")


@router.get("/my-history")
async def my_history(request:Request, db:Session = Depends(get_db)):
    user_details = Authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated or user ID missing.")

    challenges = get_user_challenges(db, user_id)
   
    serializable_challenges = []
    for challenge in challenges:
        serializable_challenges.append({
            "id": challenge.id,
            "difficulty": challenge.difficulty,
            "title": challenge.title,
            "options": json.loads(challenge.options), # Deserialize options
            "correct_answer_id": challenge.correct_answer_id,
            "explanation": challenge.explanation,
            "timestamp": challenge.date_created.isoformat() if challenge.date_created else None
        })
    return {"Challenges": serializable_challenges}


@router.get("/quota")
async def get_quota(request:Request, db:Session = Depends(get_db)):
    user_details = Authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated or user ID missing.")
    
    quota = get_challenge_quota(db, user_id)
    if not quota:
        # Return default quota for new users if none exists
        return{
            "user_id": user_id,
            "quota_remaining": 100, 
            "last_reset_date": datetime.now().isoformat() # Convert to string for JSON
        }
    quota = reset_quota_if_needed(db, quota)
    
    
    return {
        "user_id": quota.user_id,
        "quota_remaining": quota.quota_remaining,
        "last_reset_date": quota.last_reset_date.isoformat()
    }


@router.delete("/my-history/{id}")
def delete_history_item(
    id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id) 
):
    print(f"Delete request for challenge_id={id}, user_id={user_id}")
    # Ensure you query by both id and created_by for security
    challenge = db.query(Challenge).filter_by(id=id, created_by=user_id).first()
    if not challenge:
        # Use 404 for item not found, or 403 if found but not owned by user
        raise HTTPException(status_code=404, detail="Challenge not found or not authorized to delete.")
    db.delete(challenge)
    db.commit()
    return {"detail": "Deleted"}

@router.delete("/my-history")
def clear_all_history(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id) 
):
    print(f"Clear all history request for user_id={user_id}")
    
    deleted = db.query(Challenge).filter_by(created_by=user_id).delete()
    db.commit()
    return {"detail": f"Successfully deleted {deleted} challenges."}

