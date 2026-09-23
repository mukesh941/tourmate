"""Data migration: update accommodation media to verified high-availability lodging images.

Revision ID: 006_update_accommodation_media
Revises: 005_seed_knowledge_corpus
Create Date: 2026-09-23 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic (max 32 chars).
revision: str = "006_update_accommodation_media"
down_revision: Union[str, None] = "005_seed_knowledge_corpus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACC_IMAGE_MAP = {
    # Agra
    "The Oberoi Amarvilas": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Tajview - IHCL SeleQtions": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Agra": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # New Delhi
    "The Imperial New Delhi": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Janpath": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    "The Claridges New Delhi": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    
    # Jaipur
    "Rambagh Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Alsisar Haveli": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
    "Zostel Jaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Mumbai
    "The Taj Mahal Palace": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Residency Hotel Fort": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Zostel Mumbai": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Bengaluru
    "The Leela Palace Bengaluru": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Bloomrooms @ Indiranagar": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80",
    
    # Goa
    "Taj Fort Aguada Resort & Spa": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=80",
    "Santana Beach Resort": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Goa (Morjim)": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Varanasi
    "BrijRama Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    "Stops Hostel Varanasi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Kochi / Kerala
    "Brunton Boatyard": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80",
    "Zostel Kochi": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Udaipur
    "Taj Lake Palace": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Udaipur": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Amritsar
    "Taj Swarna Amritsar": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=80",
    "Jugaadus Hostel": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Hyderabad
    "Taj Falaknuma Palace": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    
    # Chennai
    "Taj Coromandel": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    
    # Mysuru
    "Lalitha Mahal Palace Hotel": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
    
    # Manali
    "Johnson Lodge & Spa": "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
    "Zostel Manali": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
    
    # Srinagar / Kashmir
    "The Lalit Grand Palace Srinagar": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
    "Zostel Srinagar": "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=1200&q=80",
}


def upgrade() -> None:
    conn = op.get_bind()
    for acc_name, img_url in ACC_IMAGE_MAP.items():
        conn.execute(
            text("""
                UPDATE images
                SET url = :img_url, thumbnail_url = :img_url, source = 'curated_unsplash', license_type = 'Unsplash License'
                WHERE id IN (
                    SELECT ai.image_id
                    FROM accommodation_images ai
                    JOIN accommodations a ON a.id = ai.accommodation_id
                    WHERE a.name = :acc_name
                );
            """),
            {"img_url": img_url, "acc_name": acc_name}
        )


def downgrade() -> None:
    pass
