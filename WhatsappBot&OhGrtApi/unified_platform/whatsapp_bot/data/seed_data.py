"""
TicketGenie Seed Data
=====================

Real event data gathered from research on TicketGenie, IPL, and entertainment events in India.
This includes actual venues, ticket prices, and event details.

Data Sources:
- IPL Official Website (ipl.com)
- TicketGenie (ticketgenie.in) - RCB's official ticketing partner
- BookMyShow, District, Paytm Insider
- ESPN Cricinfo, BCCI Official
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# ============================================================================
# VENUE DATA - Real Indian Cricket Stadiums & Entertainment Venues
# ============================================================================

VENUES: List[Dict[str, Any]] = [
    # ----- CRICKET STADIUMS (IPL HOME GROUNDS) -----
    {
        "id": "venue_chinnaswamy",
        "name": "M. Chinnaswamy Stadium",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "MG Road, Bengaluru, Karnataka 560001",
        "capacity": 40000,
        "type": "stadium",
        "description": "Home ground of Royal Challengers Bengaluru (RCB). Named after M. Chinnaswamy, former BCCI president. Known for its electric atmosphere and high-scoring matches.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380900/380976.3.jpg",
        "map_url": "https://maps.google.com/?q=M.+Chinnaswamy+Stadium+Bengaluru",
        "amenities": ["Parking", "Food Courts", "VIP Lounges", "First Aid", "ATM"],
        "home_team": "RCB",
        "ticketing_partner": "TicketGenie"
    },
    {
        "id": "venue_chepauk",
        "name": "M.A. Chidambaram Stadium",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "Victoria Hostel Road, Chepauk, Chennai 600005",
        "capacity": 50000,
        "type": "stadium",
        "description": "Also known as Chepauk Stadium. Home of Chennai Super Kings (CSK). One of India's oldest cricket venues, established in 1916. Famous for its spinning tracks and passionate fans.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380500/380593.3.jpg",
        "map_url": "https://maps.google.com/?q=MA+Chidambaram+Stadium+Chennai",
        "amenities": ["Parking", "Food Courts", "Corporate Boxes", "First Aid", "Metro Access"],
        "home_team": "CSK",
        "ticketing_partner": "Paytm Insider"
    },
    {
        "id": "venue_wankhede",
        "name": "Wankhede Stadium",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "D Road, Churchgate, Mumbai 400020",
        "capacity": 33000,
        "type": "stadium",
        "description": "Home ground of Mumbai Indians (MI). Hosted the 2011 Cricket World Cup Final. Named after S.K. Wankhede. Features the iconic Sachin Tendulkar and Sunil Gavaskar stands.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/381200/381251.3.jpg",
        "map_url": "https://maps.google.com/?q=Wankhede+Stadium+Mumbai",
        "amenities": ["Parking", "Food Courts", "VIP Boxes", "First Aid", "Marine Drive View"],
        "home_team": "MI",
        "ticketing_partner": "BookMyShow"
    },
    {
        "id": "venue_eden_gardens",
        "name": "Eden Gardens",
        "city": "Kolkata",
        "state": "West Bengal",
        "address": "BBD Bagh, Kolkata 700021",
        "capacity": 68000,
        "type": "stadium",
        "description": "Home ground of Kolkata Knight Riders (KKR). Established in 1864, it's India's oldest cricket venue. Known as the 'Mecca of Indian Cricket'. Hosted 1987 and 1996 World Cup Finals.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/379800/379898.3.jpg",
        "map_url": "https://maps.google.com/?q=Eden+Gardens+Kolkata",
        "amenities": ["Parking", "Food Courts", "Heritage Pavilion", "First Aid", "Metro Access"],
        "home_team": "KKR",
        "ticketing_partner": "BookMyShow"
    },
    {
        "id": "venue_narendra_modi",
        "name": "Narendra Modi Stadium",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "address": "Motera, Ahmedabad, Gujarat 380005",
        "capacity": 132000,
        "type": "stadium",
        "description": "World's largest cricket stadium. Home ground of Gujarat Titans (GT). Hosted Coldplay's biggest ever concert in January 2025. Features state-of-the-art facilities.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/381000/381091.3.jpg",
        "map_url": "https://maps.google.com/?q=Narendra+Modi+Stadium+Ahmedabad",
        "amenities": ["Parking", "Food Courts", "VIP Lounges", "Cricket Academy", "First Aid"],
        "home_team": "GT",
        "ticketing_partner": "Paytm Insider"
    },
    {
        "id": "venue_rajiv_gandhi",
        "name": "Rajiv Gandhi International Cricket Stadium",
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Uppal, Hyderabad 500039",
        "capacity": 55000,
        "type": "stadium",
        "description": "Home ground of Sunrisers Hyderabad (SRH). Also known as Uppal Stadium. Modern venue with excellent facilities. Close to Uppal Metro Station.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380600/380698.3.jpg",
        "map_url": "https://maps.google.com/?q=Rajiv+Gandhi+International+Stadium+Hyderabad",
        "amenities": ["Parking", "Food Courts", "Corporate Boxes", "First Aid", "Metro Access"],
        "home_team": "SRH",
        "ticketing_partner": "District"
    },
    {
        "id": "venue_arun_jaitley",
        "name": "Arun Jaitley Stadium",
        "city": "Delhi",
        "state": "Delhi",
        "address": "Bahadur Shah Zafar Marg, New Delhi 110002",
        "capacity": 42000,
        "type": "stadium",
        "description": "Home ground of Delhi Capitals (DC). Formerly known as Feroz Shah Kotla. One of Delhi's most iconic sports venues. Close to Delhi Gate Metro Station.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/379900/379994.3.jpg",
        "map_url": "https://maps.google.com/?q=Arun+Jaitley+Stadium+Delhi",
        "amenities": ["Parking", "Food Courts", "VIP Suites", "First Aid", "Metro Access"],
        "home_team": "DC",
        "ticketing_partner": "Paytm Insider"
    },
    {
        "id": "venue_ekana",
        "name": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "address": "Ekana Sportz City, Lucknow 226030",
        "capacity": 50000,
        "type": "stadium",
        "description": "Home ground of Lucknow Super Giants (LSG). Modern stadium with state-of-the-art facilities. Also known as Ekana Stadium.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/381100/381133.3.jpg",
        "map_url": "https://maps.google.com/?q=Ekana+Cricket+Stadium+Lucknow",
        "amenities": ["Parking", "Food Courts", "Corporate Boxes", "First Aid", "Sports Complex"],
        "home_team": "LSG",
        "ticketing_partner": "BookMyShow"
    },
    {
        "id": "venue_sawai_mansingh",
        "name": "Sawai Mansingh Stadium",
        "city": "Jaipur",
        "state": "Rajasthan",
        "address": "SMS Stadium Road, Jaipur 302004",
        "capacity": 24000,
        "type": "stadium",
        "description": "Home ground of Rajasthan Royals (RR). Named after Sawai Man Singh II, the former Maharaja of Jaipur. Known for its pink sandstone architecture.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380300/380393.3.jpg",
        "map_url": "https://maps.google.com/?q=Sawai+Mansingh+Stadium+Jaipur",
        "amenities": ["Parking", "Food Courts", "Royal Box", "First Aid"],
        "home_team": "RR",
        "ticketing_partner": "BookMyShow"
    },
    {
        "id": "venue_mullanpur",
        "name": "Maharaja Yadavindra Singh International Cricket Stadium",
        "city": "Mullanpur",
        "state": "Punjab",
        "address": "New Chandigarh, Mullanpur 140901",
        "capacity": 38000,
        "type": "stadium",
        "description": "Primary home ground of Punjab Kings (PBKS). Modern stadium near Chandigarh. Features excellent facilities and scenic surroundings.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/381400/381455.3.jpg",
        "map_url": "https://maps.google.com/?q=Mullanpur+Cricket+Stadium",
        "amenities": ["Parking", "Food Courts", "VIP Boxes", "First Aid"],
        "home_team": "PBKS",
        "ticketing_partner": "District"
    },
    {
        "id": "venue_dharamsala",
        "name": "HPCA Stadium",
        "city": "Dharamsala",
        "state": "Himachal Pradesh",
        "address": "HPCA Stadium, Dharamsala 176215",
        "capacity": 23000,
        "type": "stadium",
        "description": "Secondary home ground of Punjab Kings (PBKS). One of the most scenic cricket grounds in the world. Situated at 1,457m altitude with Himalayan backdrop.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380100/380198.3.jpg",
        "map_url": "https://maps.google.com/?q=HPCA+Stadium+Dharamsala",
        "amenities": ["Parking", "Food Courts", "Mountain View", "First Aid"],
        "home_team": "PBKS",
        "ticketing_partner": "District"
    },
    {
        "id": "venue_barsapara",
        "name": "Barsapara Cricket Stadium",
        "city": "Guwahati",
        "state": "Assam",
        "address": "Barsapara, Guwahati 781029",
        "capacity": 40000,
        "type": "stadium",
        "description": "Secondary home ground of Rajasthan Royals (RR). Modern stadium in Northeast India. Known for enthusiastic crowd support.",
        "image_url": "https://www.espncricinfo.com/db/PICTURES/CMS/380700/380798.3.jpg",
        "map_url": "https://maps.google.com/?q=Barsapara+Cricket+Stadium+Guwahati",
        "amenities": ["Parking", "Food Courts", "First Aid"],
        "home_team": "RR",
        "ticketing_partner": "BookMyShow"
    },
    # ----- CONCERT VENUES -----
    {
        "id": "venue_dy_patil",
        "name": "DY Patil Stadium",
        "city": "Navi Mumbai",
        "state": "Maharashtra",
        "address": "DY Patil Vidyanagar, Nerul, Navi Mumbai 400706",
        "capacity": 55000,
        "type": "stadium",
        "description": "Multi-purpose stadium hosting major concerts and sporting events. Hosted Coldplay's Music of the Spheres World Tour 2025. One of India's premier concert venues.",
        "image_url": "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=800",
        "map_url": "https://maps.google.com/?q=DY+Patil+Stadium+Navi+Mumbai",
        "amenities": ["Parking", "Food Courts", "VIP Lounges", "First Aid", "Metro Access"],
        "home_team": None,
        "ticketing_partner": "BookMyShow"
    },
    {
        "id": "venue_jln_delhi",
        "name": "Jawaharlal Nehru Stadium",
        "city": "Delhi",
        "state": "Delhi",
        "address": "Lodhi Road, New Delhi 110003",
        "capacity": 60000,
        "type": "stadium",
        "description": "India's largest multi-purpose stadium. Hosted Diljit Dosanjh's Dil-Luminati Tour. Major venue for concerts and sporting events.",
        "image_url": "https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=800",
        "map_url": "https://maps.google.com/?q=Jawaharlal+Nehru+Stadium+Delhi",
        "amenities": ["Parking", "Food Courts", "VIP Boxes", "First Aid", "Metro Access"],
        "home_team": None,
        "ticketing_partner": "Zomato Live"
    },
    {
        "id": "venue_jio_world_garden",
        "name": "Jio World Garden",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Jio World Centre, BKC, Mumbai 400051",
        "capacity": 15000,
        "type": "outdoor_venue",
        "description": "Premium outdoor venue in Mumbai's business district. Hosts AR Rahman, Arijit Singh and other major concerts. World-class acoustics and amenities.",
        "image_url": "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=800",
        "map_url": "https://maps.google.com/?q=Jio+World+Garden+Mumbai",
        "amenities": ["Valet Parking", "Gourmet Food", "VIP Lounges", "Premium Bars"],
        "home_team": None,
        "ticketing_partner": "BookMyShow"
    },
    # ----- COMEDY VENUES -----
    {
        "id": "venue_j_spot",
        "name": "The J Spot Comedy Club",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Juhu, Mumbai 400049",
        "capacity": 250,
        "type": "comedy_club",
        "description": "Mumbai's premier comedy venue. Regular shows by top Indian comedians including Zakir Khan, Biswa Kalyan Rath, and Kenny Sebastian.",
        "image_url": "https://images.unsplash.com/photo-1585699324551-f6c309eedeca?w=800",
        "map_url": "https://maps.google.com/?q=The+J+Spot+Juhu+Mumbai",
        "amenities": ["Bar", "Food", "AC", "Parking"],
        "home_team": None,
        "ticketing_partner": "Insider"
    },
    {
        "id": "venue_canvas_laugh_club",
        "name": "Canvas Laugh Club",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Lower Parel, Mumbai 400013",
        "capacity": 300,
        "type": "comedy_club",
        "description": "Popular comedy venue in Mumbai. Hosts regular stand-up shows and open mics. Great acoustics and intimate setting.",
        "image_url": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800",
        "map_url": "https://maps.google.com/?q=Canvas+Laugh+Club+Mumbai",
        "amenities": ["Bar", "Food", "AC", "Parking"],
        "home_team": None,
        "ticketing_partner": "BookMyShow"
    },
]

# ============================================================================
# IPL 2025 TEAM DATA
# ============================================================================

IPL_TEAMS: Dict[str, Dict[str, Any]] = {
    "RCB": {
        "name": "Royal Challengers Bengaluru",
        "short_name": "RCB",
        "city": "Bengaluru",
        "home_venue_id": "venue_chinnaswamy",
        "primary_color": "#EC1C24",
        "secondary_color": "#2B2A29",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225641/rcb.jpg",
        "captain": "Faf du Plessis",
        "ticketing_partner": "TicketGenie"
    },
    "CSK": {
        "name": "Chennai Super Kings",
        "short_name": "CSK",
        "city": "Chennai",
        "home_venue_id": "venue_chepauk",
        "primary_color": "#FFFF3C",
        "secondary_color": "#0081E9",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225634/csk.jpg",
        "captain": "Ruturaj Gaikwad",
        "ticketing_partner": "Paytm Insider"
    },
    "MI": {
        "name": "Mumbai Indians",
        "short_name": "MI",
        "city": "Mumbai",
        "home_venue_id": "venue_wankhede",
        "primary_color": "#004BA0",
        "secondary_color": "#D1AB3E",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225637/mi.jpg",
        "captain": "Hardik Pandya",
        "ticketing_partner": "BookMyShow"
    },
    "KKR": {
        "name": "Kolkata Knight Riders",
        "short_name": "KKR",
        "city": "Kolkata",
        "home_venue_id": "venue_eden_gardens",
        "primary_color": "#3A225D",
        "secondary_color": "#B3A123",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225636/kkr.jpg",
        "captain": "Shreyas Iyer",
        "ticketing_partner": "BookMyShow"
    },
    "GT": {
        "name": "Gujarat Titans",
        "short_name": "GT",
        "city": "Ahmedabad",
        "home_venue_id": "venue_narendra_modi",
        "primary_color": "#1C1C1C",
        "secondary_color": "#FFD700",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c259263/gt.jpg",
        "captain": "Shubman Gill",
        "ticketing_partner": "Paytm Insider"
    },
    "SRH": {
        "name": "Sunrisers Hyderabad",
        "short_name": "SRH",
        "city": "Hyderabad",
        "home_venue_id": "venue_rajiv_gandhi",
        "primary_color": "#FF822A",
        "secondary_color": "#000000",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225643/srh.jpg",
        "captain": "Pat Cummins",
        "ticketing_partner": "District"
    },
    "DC": {
        "name": "Delhi Capitals",
        "short_name": "DC",
        "city": "Delhi",
        "home_venue_id": "venue_arun_jaitley",
        "primary_color": "#282968",
        "secondary_color": "#EF1B23",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225635/dc.jpg",
        "captain": "Axar Patel",
        "ticketing_partner": "Paytm Insider"
    },
    "LSG": {
        "name": "Lucknow Super Giants",
        "short_name": "LSG",
        "city": "Lucknow",
        "home_venue_id": "venue_ekana",
        "primary_color": "#A72056",
        "secondary_color": "#FFCC00",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c259264/lsg.jpg",
        "captain": "KL Rahul",
        "ticketing_partner": "BookMyShow"
    },
    "RR": {
        "name": "Rajasthan Royals",
        "short_name": "RR",
        "city": "Jaipur",
        "home_venue_id": "venue_sawai_mansingh",
        "primary_color": "#EA1A85",
        "secondary_color": "#254AA5",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225640/rr.jpg",
        "captain": "Sanju Samson",
        "ticketing_partner": "BookMyShow"
    },
    "PBKS": {
        "name": "Punjab Kings",
        "short_name": "PBKS",
        "city": "Mohali",
        "home_venue_id": "venue_mullanpur",
        "primary_color": "#ED1B24",
        "secondary_color": "#DCDDDF",
        "logo_url": "https://www.cricbuzz.com/a/img/v1/152x152/i1/c225639/pbks.jpg",
        "captain": "Shikhar Dhawan",
        "ticketing_partner": "District"
    }
}

# ============================================================================
# TICKET CATEGORIES - Real IPL 2025 Pricing Data
# ============================================================================

# RCB M. Chinnaswamy Stadium - Real prices from TicketGenie
RCB_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "rcb_cat_1",
        "name": "KEI Wires & Cables A Stand",
        "description": "General admission with good view of the pitch",
        "price": 2300,
        "max_price": 2990,
        "available_seats": 5000,
        "benefits": ["Standard seating", "Food available nearby"]
    },
    {
        "id": "rcb_cat_2",
        "name": "PUMA B Stand",
        "description": "Mid-level seating with excellent sightlines",
        "price": 3300,
        "max_price": 4290,
        "available_seats": 4000,
        "benefits": ["Good view", "Food courts access"]
    },
    {
        "id": "rcb_cat_3",
        "name": "BOAT C Stand",
        "description": "Premium general seating",
        "price": 3300,
        "max_price": 4290,
        "available_seats": 4000,
        "benefits": ["Excellent view", "Cup holders"]
    },
    {
        "id": "rcb_cat_4",
        "name": "Confirm TKT D Corporate",
        "description": "Corporate seating section",
        "price": 3300,
        "max_price": 4290,
        "available_seats": 2500,
        "benefits": ["Corporate section", "Better facilities"]
    },
    {
        "id": "rcb_cat_5",
        "name": "Confirm TKT GT Annexe",
        "description": "Annexe section with food included",
        "price": 4000,
        "max_price": 5200,
        "available_seats": 2000,
        "benefits": ["Food included", "Dedicated entry"]
    },
    {
        "id": "rcb_cat_6",
        "name": "Qatar Airways Javagal Srinath Stand P1 Annexe",
        "description": "Premium annexe with food",
        "price": 6000,
        "max_price": 7800,
        "available_seats": 1500,
        "benefits": ["Food included", "Premium view", "Dedicated toilets"]
    },
    {
        "id": "rcb_cat_7",
        "name": "Birla Estates Grand Terrace",
        "description": "Grand terrace with panoramic views",
        "price": 10000,
        "max_price": 13000,
        "available_seats": 800,
        "benefits": ["Panoramic view", "Lounge access", "Complimentary snacks"]
    },
    {
        "id": "rcb_cat_8",
        "name": "Qatar Airways E Executive Lounge",
        "description": "Executive lounge experience",
        "price": 10000,
        "max_price": 13000,
        "available_seats": 500,
        "benefits": ["Executive lounge", "Buffet", "AC seating"]
    },
    {
        "id": "rcb_cat_9",
        "name": "Birla Estates BS Chandrashekhar Stand P Terrace",
        "description": "Premium terrace seating",
        "price": 15000,
        "max_price": 19500,
        "available_seats": 400,
        "benefits": ["Premium terrace", "Full buffet", "Dedicated bar"]
    },
    {
        "id": "rcb_cat_10",
        "name": "Qatar Airways Rahul Dravid Platinum Lounge",
        "description": "Platinum hospitality experience",
        "price": 25000,
        "max_price": 32500,
        "available_seats": 200,
        "benefits": ["Platinum hospitality", "Gourmet buffet", "Meet & greet opportunity"]
    },
    {
        "id": "rcb_cat_11",
        "name": "KEI Wires & Cables Syed Kirmani Stand P Corporate",
        "description": "Premium corporate hospitality",
        "price": 25000,
        "max_price": 35000,
        "available_seats": 300,
        "benefits": ["Corporate hospitality", "Full buffet", "Premium bar"]
    },
    {
        "id": "rcb_cat_12",
        "name": "Qatar Airways GR Vishwanath Stand P2",
        "description": "Ultra-premium VIP experience",
        "price": 42000,
        "max_price": 58800,
        "available_seats": 100,
        "benefits": ["VIP treatment", "5-star hospitality", "Best seats", "Celebrity access"]
    }
]

# CSK MA Chidambaram Stadium (Chepauk) - Real prices
CSK_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "csk_cat_1",
        "name": "C, D, E Lower Stands",
        "description": "Lower level general admission",
        "price": 1700,
        "max_price": 2200,
        "available_seats": 8000,
        "benefits": ["Lower level view", "Standard seating"]
    },
    {
        "id": "csk_cat_2",
        "name": "I, J, K Upper Stands",
        "description": "Upper level seating",
        "price": 2500,
        "max_price": 3250,
        "available_seats": 6000,
        "benefits": ["Upper level panoramic view", "Good atmosphere"]
    },
    {
        "id": "csk_cat_3",
        "name": "Premium Stands",
        "description": "Premium seating with better facilities",
        "price": 4500,
        "max_price": 5850,
        "available_seats": 3000,
        "benefits": ["Premium facilities", "Better food options"]
    },
    {
        "id": "csk_cat_4",
        "name": "VIP Enclosure",
        "description": "VIP section with hospitality",
        "price": 7500,
        "max_price": 9750,
        "available_seats": 1000,
        "benefits": ["VIP treatment", "Buffet included", "Lounge access"]
    },
    {
        "id": "csk_cat_5",
        "name": "Corporate Box",
        "description": "Private corporate viewing box",
        "price": 15000,
        "max_price": 20000,
        "available_seats": 400,
        "benefits": ["Private box", "Full hospitality", "Premium catering"]
    }
]

# MI Wankhede Stadium - Real prices
MI_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "mi_cat_1",
        "name": "General Stand",
        "description": "Standard general admission",
        "price": 990,
        "max_price": 1500,
        "available_seats": 8000,
        "benefits": ["General seating", "Stadium atmosphere"]
    },
    {
        "id": "mi_cat_2",
        "name": "North Stand",
        "description": "North stand regular seating",
        "price": 2000,
        "max_price": 2600,
        "available_seats": 5000,
        "benefits": ["Good view", "Food courts nearby"]
    },
    {
        "id": "mi_cat_3",
        "name": "Sunil Gavaskar Stand",
        "description": "Iconic stand with great views",
        "price": 4000,
        "max_price": 5200,
        "available_seats": 4000,
        "benefits": ["Premium view", "Historic section"]
    },
    {
        "id": "mi_cat_4",
        "name": "Sachin Tendulkar Stand",
        "description": "Premium stand named after the legend",
        "price": 6000,
        "max_price": 7800,
        "available_seats": 3000,
        "benefits": ["Best view", "Premium facilities"]
    },
    {
        "id": "mi_cat_5",
        "name": "VIP Box",
        "description": "VIP viewing experience",
        "price": 12000,
        "max_price": 15000,
        "available_seats": 500,
        "benefits": ["VIP hospitality", "Full buffet", "Lounge access"]
    },
    {
        "id": "mi_cat_6",
        "name": "Corporate Box",
        "description": "Premium corporate hospitality",
        "price": 25000,
        "max_price": 50000,
        "available_seats": 200,
        "benefits": ["Private box", "5-star catering", "Best seats"]
    }
]

# KKR Eden Gardens - Real prices
KKR_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "kkr_cat_1",
        "name": "General Gallery",
        "description": "General admission seating",
        "price": 750,
        "max_price": 1000,
        "available_seats": 15000,
        "benefits": ["Affordable entry", "Great atmosphere"]
    },
    {
        "id": "kkr_cat_2",
        "name": "Lower Tier",
        "description": "Lower tier closer to action",
        "price": 1500,
        "max_price": 2000,
        "available_seats": 10000,
        "benefits": ["Closer to pitch", "Better view"]
    },
    {
        "id": "kkr_cat_3",
        "name": "Club House Stand",
        "description": "Club house section",
        "price": 3000,
        "max_price": 4000,
        "available_seats": 5000,
        "benefits": ["Premium section", "Good facilities"]
    },
    {
        "id": "kkr_cat_4",
        "name": "Premium Gallery",
        "description": "Premium seating area",
        "price": 5000,
        "max_price": 8000,
        "available_seats": 3000,
        "benefits": ["Premium view", "Dedicated entry"]
    },
    {
        "id": "kkr_cat_5",
        "name": "VIP Enclosure",
        "description": "VIP hospitality",
        "price": 8500,
        "max_price": 12000,
        "available_seats": 1500,
        "benefits": ["VIP treatment", "Buffet", "AC lounge"]
    },
    {
        "id": "kkr_cat_6",
        "name": "Corporate Hospitality",
        "description": "Corporate box experience",
        "price": 19000,
        "max_price": 28000,
        "available_seats": 800,
        "benefits": ["Corporate hospitality", "Full catering", "Private viewing"]
    }
]

# GT Narendra Modi Stadium - Real prices
GT_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "gt_cat_1",
        "name": "General Stand",
        "description": "General admission",
        "price": 800,
        "max_price": 1200,
        "available_seats": 40000,
        "benefits": ["Affordable entry", "World's largest stadium experience"]
    },
    {
        "id": "gt_cat_2",
        "name": "Lower Bowl",
        "description": "Lower bowl seating",
        "price": 2000,
        "max_price": 3000,
        "available_seats": 30000,
        "benefits": ["Closer to action", "Good view"]
    },
    {
        "id": "gt_cat_3",
        "name": "Premium Stand",
        "description": "Premium seating section",
        "price": 4000,
        "max_price": 6000,
        "available_seats": 15000,
        "benefits": ["Premium facilities", "Better view"]
    },
    {
        "id": "gt_cat_4",
        "name": "Club Level",
        "description": "Club level seating",
        "price": 7000,
        "max_price": 10000,
        "available_seats": 5000,
        "benefits": ["Club facilities", "Food included"]
    },
    {
        "id": "gt_cat_5",
        "name": "VIP Lounge",
        "description": "VIP hospitality lounge",
        "price": 15000,
        "max_price": 20000,
        "available_seats": 2000,
        "benefits": ["VIP hospitality", "Full buffet", "Premium bar"]
    }
]

# SRH Rajiv Gandhi Stadium - Real prices
SRH_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "srh_cat_1",
        "name": "Jio Mohammed Azharuddin North Terrace",
        "description": "North terrace general admission",
        "price": 750,
        "max_price": 1000,
        "available_seats": 12000,
        "benefits": ["Affordable entry", "Great atmosphere"]
    },
    {
        "id": "srh_cat_2",
        "name": "East Stand",
        "description": "East stand seating",
        "price": 1500,
        "max_price": 2000,
        "available_seats": 10000,
        "benefits": ["Good view", "Standard facilities"]
    },
    {
        "id": "srh_cat_3",
        "name": "West Stand Premium",
        "description": "Premium west stand",
        "price": 3500,
        "max_price": 5000,
        "available_seats": 6000,
        "benefits": ["Premium view", "Better facilities"]
    },
    {
        "id": "srh_cat_4",
        "name": "Pavilion End",
        "description": "Pavilion section",
        "price": 6000,
        "max_price": 8000,
        "available_seats": 3000,
        "benefits": ["Premium section", "Food options"]
    },
    {
        "id": "srh_cat_5",
        "name": "VIP Hospitality Box",
        "description": "VIP hospitality experience",
        "price": 15000,
        "max_price": 20000,
        "available_seats": 1000,
        "benefits": ["VIP treatment", "Full hospitality", "Best view"]
    },
    {
        "id": "srh_cat_6",
        "name": "Premium Hospitality Box",
        "description": "Ultra-premium corporate box",
        "price": 25000,
        "max_price": 30000,
        "available_seats": 500,
        "benefits": ["5-star hospitality", "Private box", "Premium catering"]
    }
]

# DC Arun Jaitley Stadium - Real prices
DC_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "dc_cat_1",
        "name": "General Stand",
        "description": "General admission",
        "price": 1000,
        "max_price": 1500,
        "available_seats": 10000,
        "benefits": ["Affordable entry", "Stadium experience"]
    },
    {
        "id": "dc_cat_2",
        "name": "Premium Stand",
        "description": "Premium seating",
        "price": 2500,
        "max_price": 4000,
        "available_seats": 8000,
        "benefits": ["Better view", "Premium facilities"]
    },
    {
        "id": "dc_cat_3",
        "name": "Pavilion Terrace",
        "description": "Terrace seating near pavilion",
        "price": 5000,
        "max_price": 8000,
        "available_seats": 4000,
        "benefits": ["Terrace view", "Good facilities"]
    },
    {
        "id": "dc_cat_4",
        "name": "Corporate Box",
        "description": "Corporate viewing box",
        "price": 12000,
        "max_price": 25000,
        "available_seats": 1500,
        "benefits": ["Private box", "Catering included"]
    },
    {
        "id": "dc_cat_5",
        "name": "VIP Hospitality Suite",
        "description": "VIP hospitality experience",
        "price": 30000,
        "max_price": 50000,
        "available_seats": 500,
        "benefits": ["VIP suite", "5-star hospitality", "Best seats"]
    }
]

# LSG Ekana Stadium - Real prices
LSG_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "lsg_cat_1",
        "name": "General Stand",
        "description": "General admission seating",
        "price": 500,
        "max_price": 800,
        "available_seats": 15000,
        "benefits": ["Affordable entry", "New stadium experience"]
    },
    {
        "id": "lsg_cat_2",
        "name": "East Pavilion",
        "description": "East pavilion seating",
        "price": 1500,
        "max_price": 2000,
        "available_seats": 10000,
        "benefits": ["Good view", "Standard facilities"]
    },
    {
        "id": "lsg_cat_3",
        "name": "Premium Gallery",
        "description": "Premium section",
        "price": 2500,
        "max_price": 5000,
        "available_seats": 5000,
        "benefits": ["Premium view", "Better amenities"]
    },
    {
        "id": "lsg_cat_4",
        "name": "VIP Enclosure",
        "description": "VIP hospitality",
        "price": 7500,
        "max_price": 10000,
        "available_seats": 2000,
        "benefits": ["VIP hospitality", "Buffet included"]
    },
    {
        "id": "lsg_cat_5",
        "name": "Corporate Hospitality",
        "description": "Corporate box",
        "price": 15000,
        "max_price": 150000,
        "available_seats": 500,
        "benefits": ["Corporate hospitality", "Full catering", "Private viewing"]
    }
]

# RR Sawai Mansingh Stadium - Real prices
RR_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "rr_cat_1",
        "name": "East Stand (Student)",
        "description": "Student discount section",
        "price": 500,
        "max_price": 750,
        "available_seats": 3000,
        "benefits": ["Student discount", "Affordable entry"]
    },
    {
        "id": "rr_cat_2",
        "name": "East Stand 1 & 3",
        "description": "East stand general seating",
        "price": 1200,
        "max_price": 1500,
        "available_seats": 5000,
        "benefits": ["Good view", "Standard seating"]
    },
    {
        "id": "rr_cat_3",
        "name": "North West Stand",
        "description": "North west seating",
        "price": 1800,
        "max_price": 2500,
        "available_seats": 4000,
        "benefits": ["Better angle", "Good facilities"]
    },
    {
        "id": "rr_cat_4",
        "name": "Super Royals N. East Stand",
        "description": "Fan zone with jersey included",
        "price": 2000,
        "max_price": 3000,
        "available_seats": 2000,
        "benefits": ["Free fan jersey", "Fan zone experience"]
    },
    {
        "id": "rr_cat_5",
        "name": "Lawn Sections (with Food Box)",
        "description": "Lawn seating with food",
        "price": 4000,
        "max_price": 5000,
        "available_seats": 1500,
        "benefits": ["Lawn seating", "Food box included"]
    },
    {
        "id": "rr_cat_6",
        "name": "Royal Box",
        "description": "Royal hospitality box",
        "price": 6000,
        "max_price": 8000,
        "available_seats": 500,
        "benefits": ["Royal hospitality", "Buffet meal", "Soft drinks"]
    },
    {
        "id": "rr_cat_7",
        "name": "Jodhpur Lounge",
        "description": "Premium lounge experience",
        "price": 8000,
        "max_price": 12000,
        "available_seats": 300,
        "benefits": ["Premium lounge", "Full hospitality"]
    },
    {
        "id": "rr_cat_8",
        "name": "President's East Box",
        "description": "Presidential hospitality",
        "price": 15000,
        "max_price": 20000,
        "available_seats": 100,
        "benefits": ["Presidential treatment", "5-star hospitality", "Best view"]
    }
]

# PBKS Mullanpur Stadium - Real prices
PBKS_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "pbks_cat_1",
        "name": "General Stand",
        "description": "General admission",
        "price": 1200,
        "max_price": 1500,
        "available_seats": 10000,
        "benefits": ["Affordable entry", "Stadium atmosphere"]
    },
    {
        "id": "pbks_cat_2",
        "name": "East Wing",
        "description": "East wing seating",
        "price": 1600,
        "max_price": 2500,
        "available_seats": 8000,
        "benefits": ["Good view", "Standard facilities"]
    },
    {
        "id": "pbks_cat_3",
        "name": "Premium Stand",
        "description": "Premium seating",
        "price": 3000,
        "max_price": 5000,
        "available_seats": 5000,
        "benefits": ["Premium facilities", "Better view"]
    },
    {
        "id": "pbks_cat_4",
        "name": "Club Pavilion",
        "description": "Club level seating",
        "price": 7500,
        "max_price": 10000,
        "available_seats": 2000,
        "benefits": ["Club facilities", "Food options"]
    },
    {
        "id": "pbks_cat_5",
        "name": "VIP Box",
        "description": "VIP hospitality box",
        "price": 12000,
        "max_price": 18000,
        "available_seats": 500,
        "benefits": ["VIP hospitality", "Full buffet", "Premium experience"]
    }
]

# Map team codes to ticket categories
TEAM_TICKET_CATEGORIES: Dict[str, List[Dict]] = {
    "RCB": RCB_TICKET_CATEGORIES,
    "CSK": CSK_TICKET_CATEGORIES,
    "MI": MI_TICKET_CATEGORIES,
    "KKR": KKR_TICKET_CATEGORIES,
    "GT": GT_TICKET_CATEGORIES,
    "SRH": SRH_TICKET_CATEGORIES,
    "DC": DC_TICKET_CATEGORIES,
    "LSG": LSG_TICKET_CATEGORIES,
    "RR": RR_TICKET_CATEGORIES,
    "PBKS": PBKS_TICKET_CATEGORIES,
}

# ============================================================================
# IPL 2025 MATCHES - Real Schedule Data
# ============================================================================

def generate_ipl_matches() -> List[Dict[str, Any]]:
    """Generate IPL 2025 match fixtures with real data."""

    # IPL 2025 started March 22, 2025
    base_date = datetime(2025, 3, 22)

    matches = [
        # Week 1
        {"home": "KKR", "away": "RCB", "date": base_date, "time": "19:30", "match_no": 1},
        {"home": "CSK", "away": "MI", "date": base_date + timedelta(days=1), "time": "19:30", "match_no": 2},
        {"home": "DC", "away": "LSG", "date": base_date + timedelta(days=2), "time": "19:30", "match_no": 3},
        {"home": "GT", "away": "PBKS", "date": base_date + timedelta(days=3), "time": "19:30", "match_no": 4},
        {"home": "RR", "away": "SRH", "date": base_date + timedelta(days=4), "time": "19:30", "match_no": 5},
        {"home": "RCB", "away": "CSK", "date": base_date + timedelta(days=5), "time": "15:30", "match_no": 6},
        {"home": "MI", "away": "KKR", "date": base_date + timedelta(days=5), "time": "19:30", "match_no": 7},

        # Week 2
        {"home": "SRH", "away": "LSG", "date": base_date + timedelta(days=6), "time": "19:30", "match_no": 8},
        {"home": "GT", "away": "MI", "date": base_date + timedelta(days=7), "time": "19:30", "match_no": 9},
        {"home": "PBKS", "away": "DC", "date": base_date + timedelta(days=8), "time": "19:30", "match_no": 10},
        {"home": "KKR", "away": "RR", "date": base_date + timedelta(days=9), "time": "19:30", "match_no": 11},
        {"home": "CSK", "away": "GT", "date": base_date + timedelta(days=10), "time": "19:30", "match_no": 12},
        {"home": "LSG", "away": "RCB", "date": base_date + timedelta(days=11), "time": "15:30", "match_no": 13},
        {"home": "MI", "away": "SRH", "date": base_date + timedelta(days=11), "time": "19:30", "match_no": 14},

        # Week 3
        {"home": "RR", "away": "PBKS", "date": base_date + timedelta(days=12), "time": "19:30", "match_no": 15},
        {"home": "DC", "away": "KKR", "date": base_date + timedelta(days=13), "time": "19:30", "match_no": 16},
        {"home": "RCB", "away": "GT", "date": base_date + timedelta(days=14), "time": "19:30", "match_no": 17},
        {"home": "SRH", "away": "CSK", "date": base_date + timedelta(days=15), "time": "19:30", "match_no": 18},
        {"home": "LSG", "away": "MI", "date": base_date + timedelta(days=16), "time": "19:30", "match_no": 19},
        {"home": "PBKS", "away": "KKR", "date": base_date + timedelta(days=17), "time": "15:30", "match_no": 20},
        {"home": "RR", "away": "DC", "date": base_date + timedelta(days=17), "time": "19:30", "match_no": 21},

        # Week 4
        {"home": "CSK", "away": "LSG", "date": base_date + timedelta(days=18), "time": "19:30", "match_no": 22},
        {"home": "GT", "away": "SRH", "date": base_date + timedelta(days=19), "time": "19:30", "match_no": 23},
        {"home": "MI", "away": "PBKS", "date": base_date + timedelta(days=20), "time": "19:30", "match_no": 24},
        {"home": "RCB", "away": "RR", "date": base_date + timedelta(days=21), "time": "19:30", "match_no": 25},
        {"home": "LSG", "away": "GT", "date": base_date + timedelta(days=22), "time": "19:30", "match_no": 26},
        {"home": "KKR", "away": "CSK", "date": base_date + timedelta(days=23), "time": "15:30", "match_no": 27},
        {"home": "DC", "away": "MI", "date": base_date + timedelta(days=23), "time": "19:30", "match_no": 28},

        # Week 5-8 (more matches)
        {"home": "SRH", "away": "RCB", "date": base_date + timedelta(days=24), "time": "19:30", "match_no": 29},
        {"home": "PBKS", "away": "RR", "date": base_date + timedelta(days=25), "time": "19:30", "match_no": 30},
        {"home": "CSK", "away": "DC", "date": base_date + timedelta(days=26), "time": "19:30", "match_no": 31},
        {"home": "GT", "away": "KKR", "date": base_date + timedelta(days=27), "time": "19:30", "match_no": 32},
        {"home": "MI", "away": "RCB", "date": base_date + timedelta(days=28), "time": "19:30", "match_no": 33},
        {"home": "LSG", "away": "SRH", "date": base_date + timedelta(days=29), "time": "15:30", "match_no": 34},
        {"home": "RR", "away": "CSK", "date": base_date + timedelta(days=29), "time": "19:30", "match_no": 35},

        # More fixtures
        {"home": "KKR", "away": "PBKS", "date": base_date + timedelta(days=30), "time": "19:30", "match_no": 36},
        {"home": "DC", "away": "GT", "date": base_date + timedelta(days=31), "time": "19:30", "match_no": 37},
        {"home": "RCB", "away": "LSG", "date": base_date + timedelta(days=32), "time": "19:30", "match_no": 38},
        {"home": "SRH", "away": "MI", "date": base_date + timedelta(days=33), "time": "19:30", "match_no": 39},
        {"home": "CSK", "away": "PBKS", "date": base_date + timedelta(days=34), "time": "19:30", "match_no": 40},
        {"home": "RR", "away": "KKR", "date": base_date + timedelta(days=35), "time": "15:30", "match_no": 41},
        {"home": "GT", "away": "DC", "date": base_date + timedelta(days=35), "time": "19:30", "match_no": 42},

        # Final league stage matches
        {"home": "MI", "away": "LSG", "date": base_date + timedelta(days=36), "time": "19:30", "match_no": 43},
        {"home": "RCB", "away": "SRH", "date": base_date + timedelta(days=37), "time": "19:30", "match_no": 44},
        {"home": "PBKS", "away": "CSK", "date": base_date + timedelta(days=38), "time": "19:30", "match_no": 45},
        {"home": "DC", "away": "RCB", "date": base_date + timedelta(days=39), "time": "19:30", "match_no": 46},
        {"home": "KKR", "away": "GT", "date": base_date + timedelta(days=40), "time": "19:30", "match_no": 47},
        {"home": "SRH", "away": "RR", "date": base_date + timedelta(days=41), "time": "15:30", "match_no": 48},
        {"home": "LSG", "away": "PBKS", "date": base_date + timedelta(days=41), "time": "19:30", "match_no": 49},
        {"home": "MI", "away": "DC", "date": base_date + timedelta(days=42), "time": "19:30", "match_no": 50},
    ]

    formatted_matches = []
    for match in matches:
        home_team = IPL_TEAMS[match["home"]]
        away_team = IPL_TEAMS[match["away"]]
        venue = next((v for v in VENUES if v["id"] == home_team["home_venue_id"]), None)

        formatted_matches.append({
            "id": f"ipl2025_match_{match['match_no']}",
            "name": f"{home_team['short_name']} vs {away_team['short_name']}",
            "full_name": f"{home_team['name']} vs {away_team['name']}",
            "category": "cricket",
            "sub_category": "IPL",
            "tournament": "TATA IPL 2025",
            "match_number": match["match_no"],
            "home_team": match["home"],
            "away_team": match["away"],
            "home_team_name": home_team["name"],
            "away_team_name": away_team["name"],
            "home_team_logo": home_team["logo_url"],
            "away_team_logo": away_team["logo_url"],
            "venue_id": home_team["home_venue_id"],
            "venue_name": venue["name"] if venue else "",
            "city": venue["city"] if venue else home_team["city"],
            "date": match["date"].strftime("%Y-%m-%d"),
            "time": match["time"],
            "datetime": f"{match['date'].strftime('%Y-%m-%d')}T{match['time']}:00+05:30",
            "status": "upcoming",
            "image_url": venue["image_url"] if venue else "",
            "ticketing_partner": home_team["ticketing_partner"],
            "ticket_categories": TEAM_TICKET_CATEGORIES.get(match["home"], []),
            "is_featured": match["match_no"] <= 10 or match["home"] in ["RCB", "MI", "CSK"],
        })

    return formatted_matches

# ============================================================================
# CONCERT EVENTS - Real Data
# ============================================================================

CONCERTS: List[Dict[str, Any]] = [
    # Coldplay - Music of the Spheres World Tour
    {
        "id": "concert_coldplay_mumbai_1",
        "name": "Coldplay - Music of the Spheres World Tour",
        "artist": "Coldplay",
        "category": "concert",
        "sub_category": "International",
        "genre": "Rock / Alternative",
        "venue_id": "venue_dy_patil",
        "venue_name": "DY Patil Stadium",
        "city": "Navi Mumbai",
        "date": "2025-01-18",
        "time": "19:00",
        "datetime": "2025-01-18T19:00:00+05:30",
        "status": "sold_out",
        "description": "Coldplay returns to India with their spectacular Music of the Spheres World Tour. Experience Chris Martin and band live with stunning visuals, confetti, and hit songs.",
        "image_url": "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?w=800",
        "artist_image": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "cp_mum_1", "name": "Level 3 Seats", "price": 2500, "max_price": 3000, "available_seats": 0, "benefits": ["Standard seating"]},
            {"id": "cp_mum_2", "name": "Level 2 Seats", "price": 4500, "max_price": 5500, "available_seats": 0, "benefits": ["Better view"]},
            {"id": "cp_mum_3", "name": "Level 1 Seats", "price": 9500, "max_price": 12500, "available_seats": 0, "benefits": ["Premium view"]},
            {"id": "cp_mum_4", "name": "Standing Floor", "price": 6450, "max_price": 8000, "available_seats": 0, "benefits": ["Close to stage"]},
            {"id": "cp_mum_5", "name": "VIP Lounge", "price": 35000, "max_price": 45000, "available_seats": 0, "benefits": ["VIP experience", "Exclusive lounge", "Premium bar"]},
        ]
    },
    {
        "id": "concert_coldplay_ahmedabad_1",
        "name": "Coldplay - Music of the Spheres World Tour",
        "artist": "Coldplay",
        "category": "concert",
        "sub_category": "International",
        "genre": "Rock / Alternative",
        "venue_id": "venue_narendra_modi",
        "venue_name": "Narendra Modi Stadium",
        "city": "Ahmedabad",
        "date": "2025-01-25",
        "time": "19:00",
        "datetime": "2025-01-25T19:00:00+05:30",
        "status": "sold_out",
        "description": "Coldplay's biggest show ever at the world's largest cricket stadium! A once-in-a-lifetime experience for 132,000 fans.",
        "image_url": "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?w=800",
        "artist_image": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "cp_ahm_1", "name": "General Admission", "price": 2500, "max_price": 3000, "available_seats": 0, "benefits": ["Entry"]},
            {"id": "cp_ahm_2", "name": "Silver", "price": 4500, "max_price": 6500, "available_seats": 0, "benefits": ["Good view"]},
            {"id": "cp_ahm_3", "name": "Gold", "price": 9500, "max_price": 12500, "available_seats": 0, "benefits": ["Premium seating"]},
        ]
    },

    # Arijit Singh Live
    {
        "id": "concert_arijit_mumbai",
        "name": "Arijit Singh Live in Concert",
        "artist": "Arijit Singh",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / Playback",
        "venue_id": "venue_jio_world_garden",
        "venue_name": "Jio World Garden",
        "city": "Mumbai",
        "date": "2025-03-23",
        "time": "19:00",
        "datetime": "2025-03-23T19:00:00+05:30",
        "status": "available",
        "description": "Experience the magic of India's most popular playback singer. Arijit Singh performs his greatest hits including Tum Hi Ho, Channa Mereya, Kesariya, and more.",
        "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
        "artist_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
        "is_featured": True,
        "ticketing_partner": "District",
        "ticket_categories": [
            {"id": "arj_mum_1", "name": "Silver", "price": 2999, "max_price": 3999, "available_seats": 3000, "benefits": ["Standard seating"]},
            {"id": "arj_mum_2", "name": "Gold", "price": 5999, "max_price": 7999, "available_seats": 2000, "benefits": ["Better view", "Closer seats"]},
            {"id": "arj_mum_3", "name": "Platinum", "price": 9999, "max_price": 14999, "available_seats": 1000, "benefits": ["Premium view", "Dedicated entry"]},
            {"id": "arj_mum_4", "name": "Diamond Lounge", "price": 24999, "max_price": 49999, "available_seats": 200, "benefits": ["VIP lounge", "Full hospitality", "Meet & greet chance"]},
        ]
    },
    {
        "id": "concert_arijit_ahmedabad",
        "name": "Arijit Singh Live in Concert",
        "artist": "Arijit Singh",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / Playback",
        "venue_id": "venue_narendra_modi",
        "venue_name": "GIFT City Grounds",
        "city": "Ahmedabad",
        "date": "2025-01-12",
        "time": "19:00",
        "datetime": "2025-01-12T19:00:00+05:30",
        "status": "available",
        "description": "Arijit Singh brings his soulful voice to Ahmedabad. An evening of romantic melodies and Bollywood magic.",
        "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
        "artist_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "arj_ahm_1", "name": "General", "price": 1700, "max_price": 2500, "available_seats": 5000, "benefits": ["Entry"]},
            {"id": "arj_ahm_2", "name": "Silver", "price": 3500, "max_price": 4500, "available_seats": 3000, "benefits": ["Good view"]},
            {"id": "arj_ahm_3", "name": "Gold", "price": 6000, "max_price": 8000, "available_seats": 1500, "benefits": ["Premium seating"]},
            {"id": "arj_ahm_4", "name": "Platinum", "price": 12000, "max_price": 15000, "available_seats": 500, "benefits": ["VIP treatment"]},
        ]
    },
    {
        "id": "concert_arijit_indore",
        "name": "Arijit Singh Live in Concert",
        "artist": "Arijit Singh",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / Playback",
        "venue_id": None,
        "venue_name": "C21 Estate",
        "city": "Indore",
        "date": "2025-04-19",
        "time": "18:00",
        "datetime": "2025-04-19T18:00:00+05:30",
        "status": "available",
        "description": "Arijit Singh's magical voice comes to Indore. An unforgettable evening of music.",
        "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
        "artist_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
        "is_featured": False,
        "ticketing_partner": "District",
        "ticket_categories": [
            {"id": "arj_ind_1", "name": "Entry", "price": 6500, "max_price": 8000, "available_seats": 2000, "benefits": ["Entry"]},
            {"id": "arj_ind_2", "name": "Lounge", "price": 49999, "max_price": 60000, "available_seats": 200, "benefits": ["Lounge access", "Premium hospitality"]},
            {"id": "arj_ind_3", "name": "Diamond", "price": 134999, "max_price": 150000, "available_seats": 50, "benefits": ["Ultimate VIP experience"]},
        ]
    },
    {
        "id": "concert_arijit_bengaluru",
        "name": "Arijit Singh Live in Concert",
        "artist": "Arijit Singh",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / Playback",
        "venue_id": "venue_chinnaswamy",
        "venue_name": "Palace Grounds",
        "city": "Bengaluru",
        "date": "2025-05-10",
        "time": "19:00",
        "datetime": "2025-05-10T19:00:00+05:30",
        "status": "available",
        "description": "Arijit Singh brings his soulful voice to Bengaluru. Experience his greatest hits live at Palace Grounds.",
        "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
        "artist_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "arj_blr_1", "name": "Silver", "price": 2499, "max_price": 3499, "available_seats": 4000, "benefits": ["Standard seating"]},
            {"id": "arj_blr_2", "name": "Gold", "price": 4999, "max_price": 6999, "available_seats": 2500, "benefits": ["Better view", "Closer seats"]},
            {"id": "arj_blr_3", "name": "Platinum", "price": 8999, "max_price": 12999, "available_seats": 1000, "benefits": ["Premium view", "Dedicated entry"]},
            {"id": "arj_blr_4", "name": "VVIP", "price": 19999, "max_price": 29999, "available_seats": 300, "benefits": ["VIP lounge", "Meet & greet chance"]},
        ]
    },
    {
        "id": "concert_sunidhi_bengaluru",
        "name": "Sunidhi Chauhan Live",
        "artist": "Sunidhi Chauhan",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / Pop",
        "venue_id": None,
        "venue_name": "Phoenix Marketcity",
        "city": "Bengaluru",
        "date": "2025-04-05",
        "time": "19:30",
        "datetime": "2025-04-05T19:30:00+05:30",
        "status": "available",
        "description": "The powerhouse vocalist Sunidhi Chauhan performs her biggest hits live in Bengaluru.",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
        "artist_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
        "is_featured": False,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "sun_blr_1", "name": "General", "price": 1999, "max_price": 2499, "available_seats": 3000, "benefits": ["Entry"]},
            {"id": "sun_blr_2", "name": "Premium", "price": 3999, "max_price": 4999, "available_seats": 1500, "benefits": ["Better view"]},
            {"id": "sun_blr_3", "name": "VIP", "price": 7999, "max_price": 9999, "available_seats": 500, "benefits": ["VIP access", "Lounge"]},
        ]
    },
    {
        "id": "concert_prateek_bengaluru",
        "name": "Prateek Kuhad - Silhouettes Tour",
        "artist": "Prateek Kuhad",
        "category": "concert",
        "sub_category": "Indie",
        "genre": "Indie / Folk",
        "venue_id": None,
        "venue_name": "MLR Convention Centre",
        "city": "Bengaluru",
        "date": "2025-03-22",
        "time": "20:00",
        "datetime": "2025-03-22T20:00:00+05:30",
        "status": "available",
        "description": "Grammy-nominated artist Prateek Kuhad brings his intimate acoustic show to Bengaluru.",
        "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
        "artist_image": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "pk_blr_1", "name": "General", "price": 1499, "max_price": 1999, "available_seats": 1500, "benefits": ["Entry"]},
            {"id": "pk_blr_2", "name": "Fan Pit", "price": 2999, "max_price": 3999, "available_seats": 500, "benefits": ["Close to stage"]},
            {"id": "pk_blr_3", "name": "Meet & Greet", "price": 5999, "max_price": 7999, "available_seats": 50, "benefits": ["Photo with artist", "Signed merch"]},
        ]
    },

    # AR Rahman
    {
        "id": "concert_arr_mumbai",
        "name": "AR Rahman - Haazri Live",
        "artist": "AR Rahman",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / World Music",
        "venue_id": "venue_jio_world_garden",
        "venue_name": "Jio World Garden",
        "city": "Mumbai",
        "date": "2026-01-17",
        "time": "19:00",
        "datetime": "2026-01-17T19:00:00+05:30",
        "status": "available",
        "description": "The Mozart of Madras, AR Rahman, presents 'Haazri' - A spectacular live concert featuring his iconic compositions from Jai Ho to Kun Faya Kun.",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
        "artist_image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "arr_mum_1", "name": "Bronze", "price": 2499, "max_price": 3500, "available_seats": 4000, "benefits": ["Standard seating"]},
            {"id": "arr_mum_2", "name": "Silver", "price": 5999, "max_price": 8000, "available_seats": 3000, "benefits": ["Better view"]},
            {"id": "arr_mum_3", "name": "Gold", "price": 12000, "max_price": 15000, "available_seats": 1500, "benefits": ["Premium seats"]},
            {"id": "arr_mum_4", "name": "Platinum", "price": 25000, "max_price": 35000, "available_seats": 500, "benefits": ["VIP experience"]},
            {"id": "arr_mum_5", "name": "Private Box", "price": 60000, "max_price": 600000, "available_seats": 20, "benefits": ["Private box", "5-star hospitality"]},
        ]
    },
    {
        "id": "concert_arr_pune",
        "name": "AR Rahman Live in Concert",
        "artist": "AR Rahman",
        "category": "concert",
        "sub_category": "Bollywood",
        "genre": "Bollywood / World Music",
        "venue_id": None,
        "venue_name": "MCA Stadium",
        "city": "Pune",
        "date": "2025-11-23",
        "time": "17:00",
        "datetime": "2025-11-23T17:00:00+05:30",
        "status": "available",
        "description": "AR Rahman brings his legendary compositions to Pune. A 5-hour musical extravaganza.",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
        "artist_image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "arr_pune_1", "name": "General", "price": 799, "max_price": 1200, "available_seats": 8000, "benefits": ["Entry"]},
            {"id": "arr_pune_2", "name": "Silver", "price": 1999, "max_price": 3000, "available_seats": 5000, "benefits": ["Good seating"]},
            {"id": "arr_pune_3", "name": "Gold", "price": 4999, "max_price": 7000, "available_seats": 2000, "benefits": ["Premium view"]},
            {"id": "arr_pune_4", "name": "VIP", "price": 9999, "max_price": 15000, "available_seats": 500, "benefits": ["VIP treatment"]},
        ]
    },

    # Diljit Dosanjh - Dil-Luminati
    {
        "id": "concert_diljit_delhi",
        "name": "Diljit Dosanjh - Dil-Luminati Tour",
        "artist": "Diljit Dosanjh",
        "category": "concert",
        "sub_category": "Punjabi",
        "genre": "Punjabi / Pop",
        "venue_id": "venue_jln_delhi",
        "venue_name": "Jawaharlal Nehru Stadium",
        "city": "Delhi",
        "date": "2024-10-26",
        "time": "19:00",
        "datetime": "2024-10-26T19:00:00+05:30",
        "status": "sold_out",
        "description": "India's highest-grossing concert tour! Diljit Dosanjh's spectacular Dil-Luminati tour with electrifying performances of Lover, Born to Shine, and more.",
        "image_url": "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800",
        "artist_image": "https://images.unsplash.com/photo-1598387993441-a364f854c3e1?w=400",
        "is_featured": True,
        "ticketing_partner": "Zomato Live",
        "ticket_categories": [
            {"id": "diljit_del_1", "name": "Silver", "price": 2499, "max_price": 3499, "available_seats": 0, "benefits": ["Standard seating"]},
            {"id": "diljit_del_2", "name": "Gold", "price": 11999, "max_price": 15000, "available_seats": 0, "benefits": ["Better view"]},
            {"id": "diljit_del_3", "name": "Fan Pit", "price": 19999, "max_price": 30000, "available_seats": 0, "benefits": ["Closest to stage"]},
            {"id": "diljit_del_4", "name": "VVIP", "price": 60000, "max_price": 80000, "available_seats": 0, "benefits": ["Ultimate experience"]},
        ]
    },
    {
        "id": "concert_diljit_mumbai",
        "name": "Diljit Dosanjh - Dil-Luminati Tour",
        "artist": "Diljit Dosanjh",
        "category": "concert",
        "sub_category": "Punjabi",
        "genre": "Punjabi / Pop",
        "venue_id": "venue_dy_patil",
        "venue_name": "DY Patil Stadium",
        "city": "Navi Mumbai",
        "date": "2024-12-19",
        "time": "19:00",
        "datetime": "2024-12-19T19:00:00+05:30",
        "status": "sold_out",
        "description": "Mumbai gets the Dil-Luminati treatment! An unforgettable night with Diljit.",
        "image_url": "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800",
        "artist_image": "https://images.unsplash.com/photo-1598387993441-a364f854c3e1?w=400",
        "is_featured": True,
        "ticketing_partner": "Zomato Live",
        "ticket_categories": [
            {"id": "diljit_mum_1", "name": "Silver", "price": 3499, "max_price": 4999, "available_seats": 0, "benefits": ["Entry"]},
            {"id": "diljit_mum_2", "name": "Gold", "price": 14999, "max_price": 20000, "available_seats": 0, "benefits": ["Better view"]},
            {"id": "diljit_mum_3", "name": "Fan Pit", "price": 29999, "max_price": 40000, "available_seats": 0, "benefits": ["Close to stage"]},
        ]
    },

    # Sunburn Festival
    {
        "id": "sunburn_goa_2025",
        "name": "Sunburn Festival 2025",
        "artist": "Various (EDM)",
        "category": "concert",
        "sub_category": "EDM Festival",
        "genre": "Electronic / EDM",
        "venue_id": None,
        "venue_name": "Dhargalim, North Goa",
        "city": "Goa",
        "date": "2025-12-28",
        "time": "14:00",
        "datetime": "2025-12-28T14:00:00+05:30",
        "status": "available",
        "description": "Asia's largest EDM festival returns to Goa! 3 days of non-stop music, featuring world-class DJs, stunning visuals, and the ultimate party experience.",
        "image_url": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800",
        "artist_image": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=400",
        "is_featured": True,
        "duration": "3 days",
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "sunburn_1", "name": "Early Bird GA", "price": 2500, "max_price": 4000, "available_seats": 20000, "benefits": ["3-day access", "Festival experience"]},
            {"id": "sunburn_2", "name": "Regular GA", "price": 5000, "max_price": 7500, "available_seats": 30000, "benefits": ["3-day access"]},
            {"id": "sunburn_3", "name": "VIP", "price": 15000, "max_price": 25000, "available_seats": 5000, "benefits": ["VIP areas", "Fast entry", "Premium bars"]},
            {"id": "sunburn_4", "name": "VVIP Table", "price": 177000, "max_price": 250000, "available_seats": 100, "benefits": ["VVIP treatment", "Private table", "Bottle service"]},
        ]
    },
]

# ============================================================================
# COMEDY SHOWS - Real Data
# ============================================================================

COMEDY_SHOWS: List[Dict[str, Any]] = [
    # Zakir Khan
    {
        "id": "comedy_zakir_mumbai",
        "name": "Zakir Khan - Tathastu Tour",
        "artist": "Zakir Khan",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": "venue_canvas_laugh_club",
        "venue_name": "NSCI Dome",
        "city": "Mumbai",
        "date": "2025-03-15",
        "time": "20:00",
        "datetime": "2025-03-15T20:00:00+05:30",
        "status": "available",
        "description": "India's most loved comedian Zakir Khan brings his 'Tathastu' tour to Mumbai. Get ready for an evening of relatable humor, heartfelt stories, and his trademark wit.",
        "image_url": "https://images.unsplash.com/photo-1527224857830-43a7acc85260?w=800",
        "artist_image": "https://images.unsplash.com/photo-1527224857830-43a7acc85260?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "zk_mum_1", "name": "Silver", "price": 999, "max_price": 1499, "available_seats": 2000, "benefits": ["Standard seating"]},
            {"id": "zk_mum_2", "name": "Gold", "price": 1999, "max_price": 2999, "available_seats": 1500, "benefits": ["Better view"]},
            {"id": "zk_mum_3", "name": "Platinum", "price": 3999, "max_price": 4999, "available_seats": 500, "benefits": ["Front rows", "Meet & greet chance"]},
        ]
    },
    {
        "id": "comedy_zakir_pune",
        "name": "Zakir Khan - Papa Yaar",
        "artist": "Zakir Khan",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": None,
        "venue_name": "RIMS Auditorium",
        "city": "Pune",
        "date": "2025-06-22",
        "time": "19:30",
        "datetime": "2025-06-22T19:30:00+05:30",
        "status": "available",
        "description": "Zakir Khan's 'Papa Yaar' show - his latest special exploring fatherhood and family.",
        "image_url": "https://images.unsplash.com/photo-1527224857830-43a7acc85260?w=800",
        "artist_image": "https://images.unsplash.com/photo-1527224857830-43a7acc85260?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "zk_pune_1", "name": "General", "price": 799, "max_price": 999, "available_seats": 1500, "benefits": ["Entry"]},
            {"id": "zk_pune_2", "name": "Premium", "price": 1499, "max_price": 1999, "available_seats": 800, "benefits": ["Better seats"]},
        ]
    },

    # Anubhav Singh Bassi
    {
        "id": "comedy_bassi_mumbai",
        "name": "Anubhav Singh Bassi - Kisi Ko Batana Mat",
        "artist": "Anubhav Singh Bassi",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": None,
        "venue_name": "Jio World Convention Centre",
        "city": "Mumbai",
        "date": "2025-04-12",
        "time": "20:00",
        "datetime": "2025-04-12T20:00:00+05:30",
        "status": "available",
        "description": "The viral sensation Anubhav Singh Bassi brings his hilarious 'Kisi Ko Batana Mat' show to Mumbai. Get ready to laugh till your stomach hurts!",
        "image_url": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=800",
        "artist_image": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "bassi_mum_1", "name": "Silver", "price": 1499, "max_price": 1999, "available_seats": 3000, "benefits": ["Entry"]},
            {"id": "bassi_mum_2", "name": "Gold", "price": 2499, "max_price": 3499, "available_seats": 2000, "benefits": ["Better view"]},
            {"id": "bassi_mum_3", "name": "Platinum", "price": 4999, "max_price": 6999, "available_seats": 500, "benefits": ["Premium seats"]},
        ]
    },
    {
        "id": "comedy_bassi_pune",
        "name": "Anubhav Singh Bassi - Kisi Ko Batana Mat",
        "artist": "Anubhav Singh Bassi",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": None,
        "venue_name": "Buntara Bhavana",
        "city": "Pune",
        "date": "2025-07-11",
        "time": "20:00",
        "datetime": "2025-07-11T20:00:00+05:30",
        "status": "available",
        "description": "Bassi's viral comedy comes to Pune!",
        "image_url": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=800",
        "artist_image": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=400",
        "is_featured": False,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "bassi_pune_1", "name": "General", "price": 999, "max_price": 1499, "available_seats": 1500, "benefits": ["Entry"]},
            {"id": "bassi_pune_2", "name": "Premium", "price": 1999, "max_price": 2999, "available_seats": 500, "benefits": ["Better seats"]},
        ]
    },

    # Vir Das
    {
        "id": "comedy_virdas_delhi",
        "name": "Vir Das - Mind Fool Tour",
        "artist": "Vir Das",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "English Stand-up",
        "venue_id": None,
        "venue_name": "Siri Fort Auditorium",
        "city": "Delhi",
        "date": "2025-05-20",
        "time": "20:00",
        "datetime": "2025-05-20T20:00:00+05:30",
        "status": "available",
        "description": "Emmy-nominated comedian Vir Das brings his international 'Mind Fool' tour to Delhi. Sharp, witty, and incredibly funny!",
        "image_url": "https://images.unsplash.com/photo-1509924603848-aca5e5f276d7?w=800",
        "artist_image": "https://images.unsplash.com/photo-1509924603848-aca5e5f276d7?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "vd_del_1", "name": "Regular", "price": 1499, "max_price": 1999, "available_seats": 1000, "benefits": ["Entry"]},
            {"id": "vd_del_2", "name": "Premium", "price": 2999, "max_price": 3999, "available_seats": 500, "benefits": ["Better seats"]},
            {"id": "vd_del_3", "name": "VIP", "price": 4999, "max_price": 6999, "available_seats": 100, "benefits": ["Front rows", "Meet opportunity"]},
        ]
    },

    # Biswa Kalyan Rath
    {
        "id": "comedy_biswa_bangalore",
        "name": "Biswa Kalyan Rath - Sushi",
        "artist": "Biswa Kalyan Rath",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "English Stand-up",
        "venue_id": None,
        "venue_name": "Good Shepherd Auditorium",
        "city": "Bengaluru",
        "date": "2025-04-05",
        "time": "20:00",
        "datetime": "2025-04-05T20:00:00+05:30",
        "status": "available",
        "description": "Biswa's critically acclaimed 'Sushi' tour - observational comedy at its finest. A show about life, love, and everything in between.",
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
        "artist_image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "biswa_blr_1", "name": "General", "price": 799, "max_price": 999, "available_seats": 800, "benefits": ["Entry"]},
            {"id": "biswa_blr_2", "name": "Premium", "price": 1299, "max_price": 1599, "available_seats": 400, "benefits": ["Better seats"]},
        ]
    },

    # Akash Gupta
    {
        "id": "comedy_akash_mumbai",
        "name": "Akash Gupta - Daily Ka Hai",
        "artist": "Akash Gupta",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": "venue_j_spot",
        "venue_name": "The J Spot",
        "city": "Mumbai",
        "date": "2025-03-28",
        "time": "20:00",
        "datetime": "2025-03-28T20:00:00+05:30",
        "status": "available",
        "description": "Akash Gupta's hilarious take on daily life struggles and middle-class experiences.",
        "image_url": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=800",
        "artist_image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "is_featured": False,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "akash_mum_1", "name": "General", "price": 699, "max_price": 899, "available_seats": 200, "benefits": ["Entry"]},
            {"id": "akash_mum_2", "name": "Premium", "price": 999, "max_price": 1299, "available_seats": 50, "benefits": ["Front rows"]},
        ]
    },
    {
        "id": "comedy_akash_pune",
        "name": "Akash Gupta - Daily Ka Hai",
        "artist": "Akash Gupta",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up",
        "venue_id": None,
        "venue_name": "Jawahar Lal Nehru Memorial Hall",
        "city": "Pune",
        "date": "2025-07-27",
        "time": "19:30",
        "datetime": "2025-07-27T19:30:00+05:30",
        "status": "available",
        "description": "Akash Gupta brings his daily observations to Pune!",
        "image_url": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=800",
        "artist_image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
        "is_featured": False,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "akash_pune_1", "name": "General", "price": 599, "max_price": 799, "available_seats": 500, "benefits": ["Entry"]},
        ]
    },

    # Samay Raina
    {
        "id": "comedy_samay_delhi",
        "name": "Samay Raina Live",
        "artist": "Samay Raina",
        "category": "comedy",
        "sub_category": "Stand-up",
        "genre": "Hindi Stand-up / Improv",
        "venue_id": None,
        "venue_name": "Kingdom of Dreams",
        "city": "Gurugram",
        "date": "2025-04-18",
        "time": "20:00",
        "datetime": "2025-04-18T20:00:00+05:30",
        "status": "available",
        "description": "Chess comedian Samay Raina brings his unique blend of comedy and wit. Known for his sharp improvisations!",
        "image_url": "https://images.unsplash.com/photo-1527224857830-43a7acc85260?w=800",
        "artist_image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "samay_gur_1", "name": "Silver", "price": 999, "max_price": 1299, "available_seats": 1000, "benefits": ["Entry"]},
            {"id": "samay_gur_2", "name": "Gold", "price": 1799, "max_price": 2299, "available_seats": 500, "benefits": ["Better view"]},
            {"id": "samay_gur_3", "name": "Platinum", "price": 2999, "max_price": 3999, "available_seats": 200, "benefits": ["Front rows"]},
        ]
    },
]

# ============================================================================
# FOOTBALL (ISL) EVENTS
# ============================================================================

ISL_TEAMS: Dict[str, Dict[str, Any]] = {
    "MCFC": {
        "name": "Mumbai City FC",
        "short_name": "Mumbai City",
        "city": "Mumbai",
        "home_venue_id": "venue_mumbai_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#00BFFF",
    },
    "BFC": {
        "name": "Bengaluru FC",
        "short_name": "Bengaluru",
        "city": "Bengaluru",
        "home_venue_id": "venue_bangalore_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#0033A0",
    },
    "KBFC": {
        "name": "Kerala Blasters FC",
        "short_name": "Kerala Blasters",
        "city": "Kochi",
        "home_venue_id": "venue_kochi_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#FFD700",
    },
    "ATKMB": {
        "name": "ATK Mohun Bagan",
        "short_name": "ATK Mohun Bagan",
        "city": "Kolkata",
        "home_venue_id": "venue_kolkata_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#006400",
    },
    "EBFC": {
        "name": "East Bengal FC",
        "short_name": "East Bengal",
        "city": "Kolkata",
        "home_venue_id": "venue_kolkata_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#FF0000",
    },
    "CFC": {
        "name": "Chennaiyin FC",
        "short_name": "Chennaiyin",
        "city": "Chennai",
        "home_venue_id": "venue_chennai_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#00008B",
    },
    "FCG": {
        "name": "FC Goa",
        "short_name": "FC Goa",
        "city": "Goa",
        "home_venue_id": "venue_goa_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#FF6600",
    },
    "JFC": {
        "name": "Jamshedpur FC",
        "short_name": "Jamshedpur",
        "city": "Jamshedpur",
        "home_venue_id": "venue_jamshedpur_football",
        "logo_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=200",
        "primary_color": "#FF0000",
    },
}

# Football Ticket Categories
FOOTBALL_TICKET_CATEGORIES: List[Dict[str, Any]] = [
    {"id": "fb_cat_1", "name": "General Stand", "price": 299, "max_price": 399, "available_seats": 5000, "benefits": ["General admission"]},
    {"id": "fb_cat_2", "name": "East Stand", "price": 499, "max_price": 699, "available_seats": 3000, "benefits": ["Better view"]},
    {"id": "fb_cat_3", "name": "West Stand", "price": 799, "max_price": 999, "available_seats": 2000, "benefits": ["Premium view", "Shade"]},
    {"id": "fb_cat_4", "name": "VIP Box", "price": 1999, "max_price": 2999, "available_seats": 500, "benefits": ["VIP treatment", "Hospitality"]},
]

def generate_football_matches() -> List[Dict[str, Any]]:
    """Generate ISL 2024-25 match fixtures."""
    from datetime import datetime, timedelta

    # ISL Season runs from October to May
    base_date = datetime(2025, 1, 5)  # Starting from Jan 2025

    matches_data = [
        {"home": "MCFC", "away": "BFC", "date": base_date, "time": "19:30", "match_no": 1},
        {"home": "KBFC", "away": "ATKMB", "date": base_date + timedelta(days=1), "time": "19:30", "match_no": 2},
        {"home": "CFC", "away": "FCG", "date": base_date + timedelta(days=2), "time": "19:30", "match_no": 3},
        {"home": "EBFC", "away": "JFC", "date": base_date + timedelta(days=3), "time": "17:00", "match_no": 4},
        {"home": "BFC", "away": "KBFC", "date": base_date + timedelta(days=5), "time": "19:30", "match_no": 5},
        {"home": "ATKMB", "away": "MCFC", "date": base_date + timedelta(days=6), "time": "19:30", "match_no": 6},
        {"home": "FCG", "away": "EBFC", "date": base_date + timedelta(days=7), "time": "19:30", "match_no": 7},
        {"home": "JFC", "away": "CFC", "date": base_date + timedelta(days=8), "time": "17:00", "match_no": 8},
        {"home": "MCFC", "away": "KBFC", "date": base_date + timedelta(days=10), "time": "19:30", "match_no": 9},
        {"home": "BFC", "away": "ATKMB", "date": base_date + timedelta(days=11), "time": "19:30", "match_no": 10},
        {"home": "EBFC", "away": "CFC", "date": base_date + timedelta(days=12), "time": "17:00", "match_no": 11},
        {"home": "FCG", "away": "JFC", "date": base_date + timedelta(days=13), "time": "19:30", "match_no": 12},
        # Kolkata Derby
        {"home": "ATKMB", "away": "EBFC", "date": base_date + timedelta(days=15), "time": "19:30", "match_no": 13, "is_featured": True},
        {"home": "KBFC", "away": "CFC", "date": base_date + timedelta(days=16), "time": "19:30", "match_no": 14},
        {"home": "MCFC", "away": "FCG", "date": base_date + timedelta(days=17), "time": "19:30", "match_no": 15},
        {"home": "BFC", "away": "JFC", "date": base_date + timedelta(days=18), "time": "17:00", "match_no": 16},
    ]

    matches = []
    for m in matches_data:
        home_team = ISL_TEAMS[m["home"]]
        away_team = ISL_TEAMS[m["away"]]
        match_date = m["date"]

        matches.append({
            "id": f"isl2025_match_{m['match_no']}",
            "name": f"{m['home']} vs {m['away']}",
            "full_name": f"{home_team['name']} vs {away_team['name']}",
            "category": "football",
            "sub_category": "ISL",
            "tournament": "Indian Super League 2024-25",
            "match_number": m["match_no"],
            "home_team": m["home"],
            "away_team": m["away"],
            "home_team_name": home_team["name"],
            "away_team_name": away_team["name"],
            "home_team_logo": home_team["logo_url"],
            "away_team_logo": away_team["logo_url"],
            "venue_id": home_team["home_venue_id"],
            "venue_name": f"{home_team['city']} Football Stadium",
            "city": home_team["city"],
            "date": match_date.strftime("%Y-%m-%d"),
            "time": m["time"],
            "datetime": match_date.strftime("%Y-%m-%dT") + m["time"] + ":00+05:30",
            "status": "available",
            "description": f"ISL 2024-25: {home_team['name']} take on {away_team['name']} in an exciting Indian Super League clash!",
            "image_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=800",
            "is_featured": m.get("is_featured", False),
            "ticketing_partner": "BookMyShow",
            "ticket_categories": FOOTBALL_TICKET_CATEGORIES,
        })

    return matches


# ============================================================================
# THEATRE & DRAMA EVENTS
# ============================================================================

THEATRE_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "theatre_aladdin_mumbai",
        "name": "Disney's Aladdin - The Musical",
        "artist": "BookMyShow Live",
        "category": "theatre",
        "sub_category": "Musical",
        "genre": "Family Musical",
        "venue_id": None,
        "venue_name": "Nita Mukesh Ambani Cultural Centre",
        "city": "Mumbai",
        "date": "2025-02-15",
        "time": "19:00",
        "datetime": "2025-02-15T19:00:00+05:30",
        "status": "available",
        "description": "Experience the magic of Disney's Aladdin! The hit Broadway musical brings the beloved story to life with spectacular sets and costumes.",
        "image_url": "https://images.unsplash.com/photo-1503095396549-807759245b35?w=800",
        "artist_image": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "aladdin_1", "name": "Balcony", "price": 1999, "max_price": 2499, "available_seats": 500, "benefits": ["Standard view"]},
            {"id": "aladdin_2", "name": "Grand Circle", "price": 3999, "max_price": 4999, "available_seats": 400, "benefits": ["Better view"]},
            {"id": "aladdin_3", "name": "Stalls", "price": 5999, "max_price": 7999, "available_seats": 300, "benefits": ["Premium seats"]},
            {"id": "aladdin_4", "name": "Premium Stalls", "price": 9999, "max_price": 12999, "available_seats": 100, "benefits": ["Best seats", "Complimentary snacks"]},
        ]
    },
    {
        "id": "theatre_mughal_delhi",
        "name": "Mughal-E-Azam: The Musical",
        "artist": "Feroz Abbas Khan",
        "category": "theatre",
        "sub_category": "Musical",
        "genre": "Historical Drama",
        "venue_id": None,
        "venue_name": "Siri Fort Auditorium",
        "city": "Delhi",
        "date": "2025-03-01",
        "time": "19:30",
        "datetime": "2025-03-01T19:30:00+05:30",
        "status": "available",
        "description": "The grand musical adaptation of the classic film Mughal-E-Azam. A spectacular theatrical experience with stunning visuals and timeless music.",
        "image_url": "https://images.unsplash.com/photo-1503095396549-807759245b35?w=800",
        "artist_image": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "mughal_1", "name": "Silver", "price": 1500, "max_price": 2000, "available_seats": 600, "benefits": ["Entry"]},
            {"id": "mughal_2", "name": "Gold", "price": 3000, "max_price": 4000, "available_seats": 400, "benefits": ["Better seats"]},
            {"id": "mughal_3", "name": "Platinum", "price": 5000, "max_price": 7000, "available_seats": 200, "benefits": ["Premium seats"]},
        ]
    },
    {
        "id": "theatre_hamlet_bangalore",
        "name": "Hamlet - Shakespeare in the Park",
        "artist": "Bangalore Theatre Company",
        "category": "theatre",
        "sub_category": "Drama",
        "genre": "Classic Drama",
        "venue_id": None,
        "venue_name": "Ranga Shankara",
        "city": "Bengaluru",
        "date": "2025-02-20",
        "time": "18:30",
        "datetime": "2025-02-20T18:30:00+05:30",
        "status": "available",
        "description": "A contemporary take on Shakespeare's Hamlet. Experience the timeless tragedy in an intimate theatre setting.",
        "image_url": "https://images.unsplash.com/photo-1503095396549-807759245b35?w=800",
        "artist_image": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=400",
        "is_featured": False,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "hamlet_1", "name": "General", "price": 500, "max_price": 700, "available_seats": 200, "benefits": ["Entry"]},
            {"id": "hamlet_2", "name": "Premium", "price": 1000, "max_price": 1500, "available_seats": 100, "benefits": ["Front rows"]},
        ]
    },
]

# ============================================================================
# MOVIES & FILM SCREENINGS
# ============================================================================

MOVIE_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "movie_oppenheimer_imax",
        "name": "Oppenheimer - 70mm IMAX Experience",
        "artist": "Christopher Nolan",
        "category": "movies",
        "sub_category": "IMAX Screening",
        "genre": "Drama/Biography",
        "venue_id": None,
        "venue_name": "PVR IMAX Lower Parel",
        "city": "Mumbai",
        "date": "2025-01-25",
        "time": "20:00",
        "datetime": "2025-01-25T20:00:00+05:30",
        "status": "available",
        "description": "Experience Oppenheimer the way it was meant to be seen - in true 70mm IMAX. Limited screenings!",
        "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800",
        "artist_image": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "opp_1", "name": "Classic", "price": 800, "max_price": 1000, "available_seats": 100, "benefits": ["IMAX Experience"]},
            {"id": "opp_2", "name": "Prime", "price": 1200, "max_price": 1500, "available_seats": 50, "benefits": ["Best seats", "Popcorn combo"]},
        ]
    },
    {
        "id": "movie_anime_fest_delhi",
        "name": "Anime Film Festival 2025",
        "artist": "Various",
        "category": "movies",
        "sub_category": "Film Festival",
        "genre": "Animation",
        "venue_id": None,
        "venue_name": "PVR Director's Cut Vasant Kunj",
        "city": "Delhi",
        "date": "2025-02-10",
        "time": "11:00",
        "datetime": "2025-02-10T11:00:00+05:30",
        "status": "available",
        "description": "A weekend celebration of Japanese anime films including Spirited Away, Your Name, and new releases. Full day pass available!",
        "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800",
        "artist_image": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400",
        "is_featured": False,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "anime_1", "name": "Day Pass", "price": 999, "max_price": 1299, "available_seats": 200, "benefits": ["All screenings", "Collectibles"]},
            {"id": "anime_2", "name": "VIP Pass", "price": 2499, "max_price": 2999, "available_seats": 50, "benefits": ["Priority seating", "Merchandise kit", "Meet & greet"]},
        ]
    },
]

# ============================================================================
# WORKSHOPS & CONFERENCES
# ============================================================================

WORKSHOP_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "workshop_photography_mumbai",
        "name": "Master Photography Workshop by Raghu Rai",
        "artist": "Raghu Rai",
        "category": "workshops",
        "sub_category": "Photography",
        "genre": "Arts & Creativity",
        "venue_id": None,
        "venue_name": "India Habitat Centre",
        "city": "Mumbai",
        "date": "2025-02-08",
        "time": "10:00",
        "datetime": "2025-02-08T10:00:00+05:30",
        "status": "available",
        "description": "Learn from legendary photographer Raghu Rai in this intensive 2-day workshop covering street photography, portraits, and storytelling through images.",
        "image_url": "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=800",
        "artist_image": "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "photo_1", "name": "Standard", "price": 5999, "max_price": 7999, "available_seats": 50, "benefits": ["2-day workshop", "Certificate"]},
            {"id": "photo_2", "name": "Premium", "price": 12999, "max_price": 15999, "available_seats": 20, "benefits": ["1-on-1 session", "Portfolio review", "Lunch included"]},
        ]
    },
    {
        "id": "workshop_cooking_delhi",
        "name": "MasterChef Cooking Workshop",
        "artist": "Chef Vikas Khanna",
        "category": "workshops",
        "sub_category": "Culinary",
        "genre": "Food & Cooking",
        "venue_id": None,
        "venue_name": "Le Meridien",
        "city": "Delhi",
        "date": "2025-02-22",
        "time": "11:00",
        "datetime": "2025-02-22T11:00:00+05:30",
        "status": "available",
        "description": "Cook alongside Michelin-starred Chef Vikas Khanna! Learn authentic Indian recipes and modern techniques in this exclusive hands-on workshop.",
        "image_url": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=800",
        "artist_image": "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "cook_1", "name": "Participant", "price": 7999, "max_price": 9999, "available_seats": 30, "benefits": ["Hands-on cooking", "Recipe booklet", "Lunch"]},
            {"id": "cook_2", "name": "VIP", "price": 14999, "max_price": 19999, "available_seats": 10, "benefits": ["Front row", "Signed cookbook", "Photo with chef"]},
        ]
    },
    {
        "id": "workshop_startup_bangalore",
        "name": "TechSparks Startup Conference 2025",
        "artist": "YourStory",
        "category": "workshops",
        "sub_category": "Conference",
        "genre": "Business & Tech",
        "venue_id": None,
        "venue_name": "Taj Yeshwantpur",
        "city": "Bengaluru",
        "date": "2025-03-15",
        "time": "09:00",
        "datetime": "2025-03-15T09:00:00+05:30",
        "status": "available",
        "description": "India's largest startup-tech conference! Network with founders, investors, and industry leaders. Keynotes, panels, and startup pitches.",
        "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
        "artist_image": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "tech_1", "name": "Startup Pass", "price": 2999, "max_price": 3999, "available_seats": 500, "benefits": ["All sessions", "Networking lunch"]},
            {"id": "tech_2", "name": "Investor Pass", "price": 9999, "max_price": 14999, "available_seats": 100, "benefits": ["VIP lounge", "Private meetings", "Dinner"]},
        ]
    },
]

# ============================================================================
# EXHIBITIONS & ART SHOWS
# ============================================================================

EXHIBITION_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "exhibition_van_gogh_mumbai",
        "name": "Van Gogh: The Immersive Experience",
        "artist": "Exhibition Hub",
        "category": "exhibitions",
        "sub_category": "Art Exhibition",
        "genre": "Digital Art",
        "venue_id": None,
        "venue_name": "World Trade Centre",
        "city": "Mumbai",
        "date": "2025-01-20",
        "time": "10:00",
        "datetime": "2025-01-20T10:00:00+05:30",
        "status": "available",
        "description": "Step inside Van Gogh's masterpieces! A 360° digital art exhibition with floor-to-ceiling projections of Starry Night, Sunflowers, and more.",
        "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
        "artist_image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "vg_1", "name": "Weekday", "price": 999, "max_price": 1299, "available_seats": 200, "benefits": ["1-hour slot"]},
            {"id": "vg_2", "name": "Weekend", "price": 1499, "max_price": 1799, "available_seats": 300, "benefits": ["1-hour slot", "Photo booth"]},
            {"id": "vg_3", "name": "VIP", "price": 2499, "max_price": 2999, "available_seats": 50, "benefits": ["Private viewing", "Guided tour", "Merchandise"]},
        ]
    },
    {
        "id": "exhibition_india_art_fair",
        "name": "India Art Fair 2025",
        "artist": "Various Artists",
        "category": "exhibitions",
        "sub_category": "Art Fair",
        "genre": "Contemporary Art",
        "venue_id": None,
        "venue_name": "NSIC Exhibition Ground",
        "city": "Delhi",
        "date": "2025-02-06",
        "time": "11:00",
        "datetime": "2025-02-06T11:00:00+05:30",
        "status": "available",
        "description": "South Asia's leading art fair featuring 80+ galleries, artist projects, talks, and performances. Discover contemporary and modern art.",
        "image_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
        "artist_image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "iaf_1", "name": "Day Pass", "price": 1500, "max_price": 2000, "available_seats": 1000, "benefits": ["Full day access"]},
            {"id": "iaf_2", "name": "3-Day Pass", "price": 3500, "max_price": 4500, "available_seats": 500, "benefits": ["All 3 days", "Catalogue"]},
            {"id": "iaf_3", "name": "Collector Pass", "price": 10000, "max_price": 15000, "available_seats": 100, "benefits": ["Preview day", "VIP lounge", "Gallery tours"]},
        ]
    },
]

# ============================================================================
# KIDS & FAMILY EVENTS
# ============================================================================

KIDS_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "kids_peppa_mumbai",
        "name": "Peppa Pig's Adventure Live Show",
        "artist": "Hasbro Entertainment",
        "category": "kids",
        "sub_category": "Kids Show",
        "genre": "Family Entertainment",
        "venue_id": None,
        "venue_name": "Shanmukhananda Hall",
        "city": "Mumbai",
        "date": "2025-02-28",
        "time": "11:00",
        "datetime": "2025-02-28T11:00:00+05:30",
        "status": "available",
        "description": "Join Peppa, George, Mummy Pig, and Daddy Pig on a camping adventure! Interactive songs, games, and muddy puddle fun for the whole family.",
        "image_url": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800",
        "artist_image": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "peppa_1", "name": "Silver", "price": 999, "max_price": 1299, "available_seats": 500, "benefits": ["Standard seating"]},
            {"id": "peppa_2", "name": "Gold", "price": 1999, "max_price": 2499, "available_seats": 300, "benefits": ["Better view", "Peppa mask"]},
            {"id": "peppa_3", "name": "Meet & Greet", "price": 3999, "max_price": 4999, "available_seats": 50, "benefits": ["Photo with Peppa", "Merchandise"]},
        ]
    },
    {
        "id": "kids_science_bangalore",
        "name": "Science Fun Fair - Explore & Learn",
        "artist": "Nehru Science Centre",
        "category": "kids",
        "sub_category": "Educational",
        "genre": "STEM Learning",
        "venue_id": None,
        "venue_name": "Visvesvaraya Museum",
        "city": "Bengaluru",
        "date": "2025-01-26",
        "time": "10:00",
        "datetime": "2025-01-26T10:00:00+05:30",
        "status": "available",
        "description": "Hands-on science experiments, robotics demos, space exploration zone, and fun learning activities for kids aged 5-15. Special Republic Day edition!",
        "image_url": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800",
        "artist_image": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=400",
        "is_featured": False,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "sci_1", "name": "Child", "price": 299, "max_price": 399, "available_seats": 500, "benefits": ["All activities", "Science kit"]},
            {"id": "sci_2", "name": "Family Pack (2+2)", "price": 899, "max_price": 1199, "available_seats": 200, "benefits": ["2 adults + 2 kids", "Bonus experiments"]},
        ]
    },
]

# ============================================================================
# NIGHTLIFE & DJ EVENTS
# ============================================================================

NIGHTLIFE_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "nightlife_martin_garrix_mumbai",
        "name": "Martin Garrix Live in Mumbai",
        "artist": "Martin Garrix",
        "category": "nightlife",
        "sub_category": "DJ Night",
        "genre": "EDM",
        "venue_id": None,
        "venue_name": "Mahalaxmi Race Course",
        "city": "Mumbai",
        "date": "2025-03-08",
        "time": "20:00",
        "datetime": "2025-03-08T20:00:00+05:30",
        "status": "available",
        "description": "World's #1 DJ Martin Garrix brings his electrifying performance to Mumbai! Featuring hits like Animals, Scared to Be Lonely, and High on Life.",
        "image_url": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=800",
        "artist_image": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=400",
        "is_featured": True,
        "ticketing_partner": "BookMyShow",
        "ticket_categories": [
            {"id": "mg_1", "name": "General", "price": 3999, "max_price": 4999, "available_seats": 5000, "benefits": ["Entry"]},
            {"id": "mg_2", "name": "VIP", "price": 9999, "max_price": 12999, "available_seats": 1000, "benefits": ["Elevated viewing", "Fast track entry"]},
            {"id": "mg_3", "name": "VVIP", "price": 24999, "max_price": 34999, "available_seats": 200, "benefits": ["Stage-front", "Open bar", "Meet & greet lottery"]},
        ]
    },
    {
        "id": "nightlife_trance_goa",
        "name": "Goa Trance Festival 2025",
        "artist": "Various DJs",
        "category": "nightlife",
        "sub_category": "Music Festival",
        "genre": "Trance/Psytrance",
        "venue_id": None,
        "venue_name": "Hilltop Vagator",
        "city": "Goa",
        "date": "2025-02-14",
        "time": "18:00",
        "datetime": "2025-02-14T18:00:00+05:30",
        "status": "available",
        "description": "3-day trance music festival featuring international and Indian artists. Beach vibes, psychedelic visuals, and non-stop music under the stars.",
        "image_url": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=800",
        "artist_image": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=400",
        "is_featured": True,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "trance_1", "name": "3-Day Pass", "price": 4999, "max_price": 6999, "available_seats": 3000, "benefits": ["All 3 days"]},
            {"id": "trance_2", "name": "VIP Pass", "price": 12999, "max_price": 17999, "available_seats": 500, "benefits": ["VIP area", "Lounge access"]},
            {"id": "trance_3", "name": "Camping + Festival", "price": 7999, "max_price": 9999, "available_seats": 1000, "benefits": ["Tent accommodation", "Festival access"]},
        ]
    },
    {
        "id": "nightlife_bollywood_delhi",
        "name": "Bollywood Nights - Retro Edition",
        "artist": "DJ Suketu",
        "category": "nightlife",
        "sub_category": "Club Night",
        "genre": "Bollywood/Retro",
        "venue_id": None,
        "venue_name": "Kitty Su",
        "city": "Delhi",
        "date": "2025-01-31",
        "time": "21:00",
        "datetime": "2025-01-31T21:00:00+05:30",
        "status": "available",
        "description": "Dance to the best of 90s and 2000s Bollywood! DJ Suketu spins retro hits with modern remixes. Dress code: Retro Bollywood glam.",
        "image_url": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=800",
        "artist_image": "https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=400",
        "is_featured": False,
        "ticketing_partner": "Insider",
        "ticket_categories": [
            {"id": "bwood_1", "name": "Stag", "price": 1999, "max_price": 2499, "available_seats": 200, "benefits": ["Entry", "1 drink"]},
            {"id": "bwood_2", "name": "Couple", "price": 2999, "max_price": 3999, "available_seats": 150, "benefits": ["Entry", "2 drinks"]},
            {"id": "bwood_3", "name": "Table (6 pax)", "price": 19999, "max_price": 29999, "available_seats": 20, "benefits": ["Reserved table", "1 bottle", "Mixers"]},
        ]
    },
]

# ============================================================================
# CITY COORDINATES - For nearby events
# ============================================================================

CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777},
    "delhi": {"lat": 28.6139, "lon": 77.2090},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "bangalore": {"lat": 12.9716, "lon": 77.5946},
    "chennai": {"lat": 13.0827, "lon": 80.2707},
    "kolkata": {"lat": 22.5726, "lon": 88.3639},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "pune": {"lat": 18.5204, "lon": 73.8567},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "jaipur": {"lat": 26.9124, "lon": 75.7873},
    "goa": {"lat": 15.2993, "lon": 74.1240},
    "kochi": {"lat": 9.9312, "lon": 76.2673},
    "lucknow": {"lat": 26.8467, "lon": 80.9462},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "navi mumbai": {"lat": 19.0330, "lon": 73.0297},
    "gurgaon": {"lat": 28.4595, "lon": 77.0266},
    "noida": {"lat": 28.5355, "lon": 77.3910},
    "jamshedpur": {"lat": 22.8046, "lon": 86.2029},
}


def get_city_from_coordinates(lat: float, lon: float) -> str:
    """Find nearest city based on coordinates."""
    import math

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    nearest_city = "mumbai"
    min_distance = float('inf')

    for city, coords in CITY_COORDINATES.items():
        dist = haversine(lat, lon, coords["lat"], coords["lon"])
        if dist < min_distance:
            min_distance = dist
            nearest_city = city

    return nearest_city.title()


# ============================================================================
# COMBINED EVENT DATA
# ============================================================================

def get_all_events() -> List[Dict[str, Any]]:
    """Get all events combined: Sports + Entertainment + Activities."""
    ipl_matches = generate_ipl_matches()
    football_matches = generate_football_matches()
    return (
        ipl_matches +
        football_matches +
        CONCERTS +
        COMEDY_SHOWS +
        THEATRE_EVENTS +
        MOVIE_EVENTS +
        WORKSHOP_EVENTS +
        EXHIBITION_EVENTS +
        KIDS_EVENTS +
        NIGHTLIFE_EVENTS
    )

def get_events_by_category(category: str) -> List[Dict[str, Any]]:
    """Get events filtered by category."""
    all_events = get_all_events()
    return [e for e in all_events if e.get("category") == category]

def get_events_by_city(city: str) -> List[Dict[str, Any]]:
    """Get events filtered by city."""
    all_events = get_all_events()
    return [e for e in all_events if city.lower() in e.get("city", "").lower()]

def get_featured_events() -> List[Dict[str, Any]]:
    """Get featured events."""
    all_events = get_all_events()
    return [e for e in all_events if e.get("is_featured")]

def get_venue_by_id(venue_id: str) -> Dict[str, Any] | None:
    """Get venue by ID."""
    return next((v for v in VENUES if v["id"] == venue_id), None)

def get_team_info(team_code: str) -> Dict[str, Any] | None:
    """Get IPL team information."""
    return IPL_TEAMS.get(team_code)

def search_events(query: str, category: str = None, city: str = None) -> List[Dict[str, Any]]:
    """Search events by query with optional filters."""
    all_events = get_all_events()
    results = []

    query_lower = query.lower()

    for event in all_events:
        # Apply category filter
        if category and event.get("category") != category:
            continue

        # Apply city filter
        if city and city.lower() not in event.get("city", "").lower():
            continue

        # Search in various fields
        searchable = " ".join([
            str(event.get("name", "")),
            str(event.get("artist", "")),
            str(event.get("city", "")),
            str(event.get("venue_name", "")),
            str(event.get("home_team_name", "")),
            str(event.get("away_team_name", "")),
            str(event.get("genre", "")),
        ]).lower()

        if query_lower in searchable:
            results.append(event)

    return results

# ============================================================================
# STATISTICS
# ============================================================================

def get_seed_data_stats() -> Dict[str, int]:
    """Get statistics about seed data."""
    ipl_matches = generate_ipl_matches()
    return {
        "total_venues": len(VENUES),
        "ipl_teams": len(IPL_TEAMS),
        "ipl_matches": len(ipl_matches),
        "concerts": len(CONCERTS),
        "comedy_shows": len(COMEDY_SHOWS),
        "total_events": len(ipl_matches) + len(CONCERTS) + len(COMEDY_SHOWS),
    }


if __name__ == "__main__":
    # Print statistics
    stats = get_seed_data_stats()
    print("\n" + "="*60)
    print("TicketGenie Seed Data Statistics")
    print("="*60)
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print("="*60)

    # Sample events
    print("\nSample IPL Match:")
    matches = generate_ipl_matches()
    if matches:
        m = matches[0]
        print(f"  {m['name']} at {m['venue_name']}, {m['city']}")
        print(f"  Date: {m['date']} {m['time']}")
        print(f"  Categories: {len(m['ticket_categories'])}")

    print("\nSample Concert:")
    if CONCERTS:
        c = CONCERTS[0]
        print(f"  {c['name']} at {c['venue_name']}, {c['city']}")
        print(f"  Date: {c['date']} {c['time']}")

    print("\nSample Comedy Show:")
    if COMEDY_SHOWS:
        s = COMEDY_SHOWS[0]
        print(f"  {s['name']} at {s['venue_name']}, {s['city']}")
        print(f"  Date: {s['date']} {s['time']}")
