"""
Canonical Knowledge Corpus for TourMate AI RAG Assistant.

Contains verified factual knowledge chunks for:
- Exactly 12 Canonical Phase 2 POIs across Agra, New Delhi, Jaipur, and Mumbai.
- Exactly 4 Canonical Destinations (Agra, New Delhi, Jaipur, Mumbai).

Every chunk has deterministic UUID, title, content, optional poi_id, and honest provenance attribution.
"""
import uuid

# Namespace for deterministic UUID generation
KNOWLEDGE_NS = uuid.UUID("e0000000-0000-0000-0000-000000000000")

def make_chunk_id(slug: str) -> str:
    """Generate deterministic UUID from slug."""
    return str(uuid.uuid5(KNOWLEDGE_NS, f"tourmate.chunk.{slug}"))

CANONICAL_KNOWLEDGE_CHUNKS = [
    # =========================================================================
    # AGRA POIs
    # =========================================================================
    {
        "id": make_chunk_id("agra-taj-mahal-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000001",
        "title": "Taj Mahal: Architecture and Historical Significance",
        "content": (
            "The Taj Mahal is an ivory-white marble mausoleum situated on the southern right bank of the "
            "Yamuna River in Agra, Uttar Pradesh. It was commissioned in 1631 by the Mughal Emperor Shah Jahan "
            "to house the tomb of his favourite wife, Mumtaz Mahal, and also houses the tomb of Shah Jahan himself. "
            "The monument is recognized globally as a UNESCO World Heritage site and is widely considered the finest "
            "masterpiece of Mughal architecture, blending Persian, Islamic, and Indian architectural styles. "
            "The complex includes a central domed mausoleum, four flanking minarets, a formal charbagh garden, "
            "a red sandstone mosque, and a matching jawab (guest house). Its exterior surfaces feature intricate "
            "pietra dura stone inlays of semi-precious gems and Quranic calligraphy."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("agra-taj-mahal-visiting"),
        "poi_id": "b0000000-0000-0000-0000-000000000001",
        "title": "Taj Mahal: Visiting Guidelines and Hours",
        "content": (
            "The Taj Mahal opens thirty minutes before sunrise and closes thirty minutes before sunset, generally "
            "operating from 06:00 to 18:30 during normal visiting months. It remains strictly closed to tourists on Fridays "
            "for congregational prayers. Visitors access the monument through the West Gate, East Gate, or South Gate, with "
            "security screening checkpoints in place. To protect the marble from pollution, no petrol or diesel vehicles "
            "are permitted within the Taj Trapezium Zone around the monument; electric battery-operated shuttles and "
            "cycle rickshaws operate between designated parking areas and the entry gates."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("agra-fort-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000002",
        "title": "Agra Fort: History and Fortifications",
        "content": (
            "Agra Fort, also known as the Red Fort of Agra, is a massive 16th-century fortress constructed of red sandstone "
            "located approximately 2.5 kilometers northwest of the Taj Mahal along the Yamuna River. Begun under Emperor Akbar "
            "in 1565 on the foundations of an older brick fort, it served as the main seat of Mughal governance until Emperor "
            "Shah Jahan shifted the capital to Delhi in 1638. Enclosed by double 21-meter-high fortified battlements, the fort "
            "encompasses palaces and administrative halls, including the Jahangiri Mahal, Diwan-i-Am (Hall of Public Audience), "
            "Diwan-i-Khas (Hall of Private Audience), and the marble Sheesh Mahal. Shah Jahan spent the final eight years of his "
            "life confined in the Musamman Burj tower of Agra Fort by his son Aurangzeb, overlooking the Taj Mahal."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("agra-mehtab-bagh-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000003",
        "title": "Mehtab Bagh: Moonlight Garden and Taj Mahal Vista",
        "content": (
            "Mehtab Bagh, meaning 'Moonlight Garden', is a charbagh (four-quartered) garden complex located north of the "
            "Taj Mahal on the opposite bank of the Yamuna River in Agra. Originally laid out by Emperor Babur in the early "
            "16th century, it was restored by Shah Jahan as the ultimate viewing point designed for admiring the Taj Mahal "
            "illuminated by the moonlight reflected upon the river water. The square garden measures approximately 300 meters "
            "by 300 meters and aligns symmetrically with the Taj Mahal complex. Today, it provides one of the premier sunset "
            "vantage points in Agra, offering unobstructed panoramic views of the Taj Mahal's north facade without the crowds "
            "present inside the main mausoleum complex."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },

    # =========================================================================
    # NEW DELHI POIs
    # =========================================================================
    {
        "id": make_chunk_id("delhi-qutub-minar-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000004",
        "title": "Qutub Minar: Monument History and Indo-Islamic Architecture",
        "content": (
            "The Qutub Minar is a 72.5-meter-tall red sandstone and marble minaret situated in the Mehrauli area of southwest "
            "Delhi. Founded by Qutb-ud-din Aibak in 1192 following the establishment of the Delhi Sultanate, it was expanded by his "
            "successor Shams-ud-din Iltutmish and later repaired and topped with marble storeys by Firoz Shah Tughlaq. The minaret "
            "tapers from a base diameter of 14.3 meters to 2.7 meters at the peak and features five distinct storeys adorned with "
            "fluted columns, intricate projecting balconies, and carved Arabic inscriptions. The surrounding Qutub complex "
            "features the Quwwat-ul-Islam Mosque, the Alai Darwaza gateway, and the renowned 4th-century Iron Pillar of Chandragupta II, "
            "celebrated for its corrosion-resistant metallurgy."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("delhi-red-fort-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000005",
        "title": "Red Fort (Lal Qila): Shahjahanabad Citadel and National Symbol",
        "content": (
            "The Red Fort, or Lal Qila, is an octagonal fortress in Old Delhi constructed between 1639 and 1648 by Mughal Emperor "
            "Shah Jahan to serve as the palace citadel of his newly planned walled capital, Shahjahanabad. Built with red sandstone "
            "ramparts extending over two kilometers along Netaji Subhash Marg, the fort features prominent monumental entrances "
            "including the Lahore Gate and Delhi Gate. Within the fort grounds lie the Naubat Khana (Drum House), Diwan-i-Am, "
            "Diwan-i-Khas, the royal bath pavilions (Hammam), and the private Moti Masjid. Every year on Independence Day (August 15), "
            "the Prime Minister of India unfurls the national tricolour flag and delivers the national address from the ramparts of the Lahore Gate."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("delhi-humayun-tomb-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000006",
        "title": "Humayun's Tomb: Mughal Garden Tomb Architecture",
        "content": (
            "Humayun's Tomb in Nizamuddin East, New Delhi, is the mausoleum of the second Mughal Emperor Humayun. Commissioned "
            "in 1558 by his senior widow Empress Bega Begum (Haji Begum) and designed by Persian architect Mirak Mirza Ghiyas, it was "
            "the first grand dynastic garden tomb built on the Indian subcontinent. The monument introduced Persian double-dome architecture "
            "and monumental symmetry that later served as the architectural prototype for the Taj Mahal in Agra. The mausoleum stands on "
            "a high terraced plinth in the center of a 30-acre quadrilateral Persian-style charbagh garden with causeways and water channels."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("delhi-lodhi-garden-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000007",
        "title": "Lodhi Garden: Sayyid and Lodhi Heritage Park",
        "content": (
            "Lodhi Garden is a 90-acre landscaped public park situated between Khan Market and Safdarjung's Tomb in central New Delhi. "
            "It preserves notable architectural monuments from the Sayyid and Lodhi dynasties of the 15th and early 16th centuries. "
            "Key structures include the octagonal Tomb of Mohammed Shah (1444), the square Tomb of Sikandar Lodi (1517), the Shisha Gumbad "
            "('Glazed Dome'), and the Bara Gumbad with its three-bay attached mosque. Landscaped during the British era and later "
            "redesigned with botanical collections, Lodhi Garden is a favored public space for morning walks, jogging, and architectural heritage study."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },

    # =========================================================================
    # JAIPUR POIs
    # =========================================================================
    {
        "id": make_chunk_id("jaipur-hawa-mahal-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000008",
        "title": "Hawa Mahal: Palace of the Winds Architecture",
        "content": (
            "Hawa Mahal, or the 'Palace of the Winds', is a five-storey palace in the heart of Jaipur, Rajasthan, built in 1799 "
            "by Maharaja Sawai Pratap Singh and designed by Lal Chand Ustad. Constructed of red and pink sandstone to resemble "
            "the crown of the Hindu deity Lord Krishna, the building's exterior features 953 miniature casements called jharokhas "
            "decorated with delicate latticework screens. These screened windows were designed to allow royal ladies to observe street "
            "festivals and daily bazaar life without being seen from outside, while simultaneously channeling airflow through the "
            "Venturi effect to cool the palace interiors during scorching summer months."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("jaipur-amer-fort-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000009",
        "title": "Amer Fort: Hilltop Rajput Palace and Sheesh Mahal",
        "content": (
            "Amer Fort (often written Amber Fort) is an expansive fortified palace complex situated on a rocky ridge in Amer, 11 kilometers "
            "northeast of central Jaipur. Founded by Raja Man Singh I in 1592 and enlarged by successive rulers including Jai Singh I, "
            "the fortress overlooks Maota Lake and is built from yellow and pink sandstone with white marble accents. The palace complex "
            "is divided into four main courtyards, housing the Diwan-i-Am, the Diwan-i-Khas, the Jas Mandir, and the celebrated Sheesh Mahal "
            "(Mirror Palace), whose walls and ceilings are inlaid with thousands of concave Belgian glass mirrors that glow when illuminated."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("jaipur-jantar-mantar-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000010",
        "title": "Jantar Mantar: Astronomical Observatory Instruments",
        "content": (
            "Jantar Mantar in Jaipur is an outdoor astronomical observatory built between 1728 and 1734 by Maharaja Sawai Jai Singh II, "
            "the mathematician-astronomer king who founded the city of Jaipur. A UNESCO World Heritage site, it contains nineteen monumental "
            "stone and brass instruments designed for naked-eye observation of celestial bodies, time measurement, predicting eclipses, and "
            "tracking planetary orbits. The centerpiece of the observatory is the Vrihat Samrat Yantra, the world's largest stone sundial, "
            "standing 27 meters tall with a gnomon that casts a shadow moving at 4 millimeters per minute to measure local solar time "
            "with a precision of two seconds."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },

    # =========================================================================
    # MUMBAI POIs
    # =========================================================================
    {
        "id": make_chunk_id("mumbai-gateway-of-india-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000011",
        "title": "Gateway of India: Waterfront Monument and History",
        "content": (
            "The Gateway of India is an arch-monument situated on the Arabian Sea waterfront at Apollo Bunder in Colaba, South Mumbai. "
            "Designed by British architect George Wittet in the Indo-Saracenic architectural style with Gujarati decorative motifs, "
            "it was erected to commemorate the landing of King George V and Queen Mary in Bombay in December 1911. Completed in 1924 "
            "in yellow basalt and reinforced concrete, the central arch rises 26 meters in height. Historically, the Gateway marked "
            "the ceremonial entrance to British India and subsequently served as the departure point for the last British military unit, "
            "the First Battalion of the Somerset Light Infantry, leaving independent India on February 28, 1948."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },
    {
        "id": make_chunk_id("mumbai-cst-overview"),
        "poi_id": "b0000000-0000-0000-0000-000000000012",
        "title": "Chhatrapati Shivaji Terminus: Victorian Gothic Railway Station",
        "content": (
            "Chhatrapati Shivaji Terminus (formerly Victoria Terminus, code CSMT) is an active central railway terminus and UNESCO "
            "World Heritage site in Fort, Mumbai. Designed by British architectural engineer Frederick William Stevens and built between "
            "1878 and 1887, the building exemplifies High Victorian Gothic Revival architecture fused with traditional Indian palace "
            "features. The station features a massive stone dome topped with a statue representing 'Progress', vaulted ceilings, "
            "ornamental brass and iron railings, stained glass windows, and carvings of gargoyles and Indian wildlife. It serves as "
            "the headquarters of Central Railway and handles hundreds of thousands of commuters daily on Mumbai's suburban train network."
        ),
        "source": "canonical_seed_data / editorial_verified",
    },

    # =========================================================================
    # DESTINATION-LEVEL KNOWLEDGE CHUNKS (poi_id = None)
    # =========================================================================
    {
        "id": make_chunk_id("dest-agra-overview"),
        "poi_id": None,
        "title": "Agra: Destination Overview and Travel Guidelines",
        "content": (
            "Agra is a historic city situated along the Yamuna River in western Uttar Pradesh, approximately 210 kilometers south "
            "of New Delhi. As the former imperial capital of the Mughal Empire under emperors Akbar, Jahangir, and Shah Jahan, Agra "
            "is home to renowned architectural monuments including the Taj Mahal, Agra Fort, and Mehtab Bagh. The best time to visit "
            "is during the cooler winter months from October to March. Summer months (April to June) experience severe heat with "
            "temperatures frequently exceeding 40 degrees Celsius. Local transport options within Agra include prepaid taxis, auto-rickshaws, "
            "and battery-operated e-rickshaws. When planning visits, note that the Taj Mahal is closed to tourists every Friday."
        ),
        "source": "curated_destination_guide / editorial_verified",
    },
    {
        "id": make_chunk_id("dest-delhi-overview"),
        "poi_id": None,
        "title": "New Delhi: Capital Heritage and Travel Guidelines",
        "content": (
            "Delhi, comprising Old Delhi and New Delhi, is the national capital territory of India and one of the world's oldest "
            "continuously inhabited urban regions. The city's layered heritage reflects centuries of rule by the Delhi Sultanate, "
            "the Mughal Empire, and the British Raj, visible in monuments such as the Red Fort, Qutub Minar, Humayun's Tomb, and "
            "Lodhi Garden. Delhi possesses an extensive and modern underground metro network (Delhi Metro) connecting major "
            "districts and tourist landmarks efficiently. The winter season between November and February provides pleasant weather "
            "for sightseeing, whereas May and June bring extreme heat and July through September brings seasonal monsoon rainfall."
        ),
        "source": "curated_destination_guide / editorial_verified",
    },
    {
        "id": make_chunk_id("dest-jaipur-overview"),
        "poi_id": None,
        "title": "Jaipur: The Pink City Heritage and Guidelines",
        "content": (
            "Jaipur is the capital and largest city of the northwestern state of Rajasthan, founded in 1727 by Maharaja Sawai Jai Singh II. "
            "Popularly known as the 'Pink City' due to the distinctive terracotta-pink wash applied to its historic walled quarter under "
            "Maharaja Sawai Ram Singh in 1876 to welcome the Prince of Wales, the city forms part of India's Golden Triangle tourist circuit "
            "alongside Delhi and Agra. Key architectural highlights include Hawa Mahal, Amer Fort, and Jantar Mantar. Jaipur is also "
            "famed for traditional arts including block printing, blue pottery, and gemstone jewelry found across Johari and Bapu Bazaars."
        ),
        "source": "curated_destination_guide / editorial_verified",
    },
    {
        "id": make_chunk_id("dest-mumbai-overview"),
        "poi_id": None,
        "title": "Mumbai: Financial Capital and Coastal Heritage Guidelines",
        "content": (
            "Mumbai, the capital of Maharashtra, is India's financial hub and most populous metropolitan region, located along the "
            "Konkan coast of the Arabian Sea. Originally an archipelago of seven islands, the city was joined through reclamation "
            "projects in the 18th and 19th centuries. Historic architectural highlights concentrate in South Mumbai, showcasing Victorian "
            "Gothic and Art Deco ensembles such as Chhatrapati Shivaji Terminus and waterfront landmarks like the Gateway of India. "
            "Travelers can navigate via Mumbai's suburban railway, local black-and-yellow (kaali-peeli) taxis, metered auto-rickshaws "
            "(suburbs only), and app-based rides. The monsoon season extends from June to September, bringing heavy rainfall."
        ),
        "source": "curated_destination_guide / editorial_verified",
    },
]
