from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from pathlib import Path


app = FastAPI(title="ConsultBae Automation API")


# Project root directory
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "consultbae.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/automation/gig-workers")
def get_gig_workers():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            g.id AS profile_id,
            p.id AS person_id,
            p.canonical_name,
            g.skill_tags,
            g.status,
            g.rate_amount,
            g.rate_period
        FROM gig_worker_profiles g
        JOIN people p
            ON p.id = g.person_id
        WHERE g.skill_tags IS NOT NULL
          AND TRIM(g.skill_tags) != ''
        ORDER BY g.id
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


class CategoryUpdate(BaseModel):
    category: str


@app.patch("/automation/gig-workers/{profile_id}/category")
def update_category(profile_id: int, payload: CategoryUpdate):

    allowed_categories = {
    "AI/ML",
    "Software Development",
    "Data Engineering",
    "Data Analysis",
    "Cloud/DevOps",
    "Web Development",
    "Mobile Development",
    "QA/Testing",
    "Design",
    "Other",
}

    if payload.category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {payload.category}"
        )

    conn = get_connection()

    cursor = conn.execute("""
        UPDATE gig_worker_profiles
        SET skill_category = ?
        WHERE id = ?
    """, (payload.category, profile_id))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Profile {profile_id} not found"
        )

    conn.close()

    return {
        "success": True,
        "profile_id": profile_id,
        "category": payload.category
    }