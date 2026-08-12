# TravelOS — travel_knowledge

This folder contains 30 country JSON files.

Each country has 8 category records:
- culture
- transportation
- packing
- safety
- destination_information
- entry_requirements
- visa
- activities

The category source is country-specific and category-specific. Tourism topics
use the country's official tourism portal; legal/safety topics use an official
government portal. A site-specific search URL is stored so the user can reach
relevant information even when the exact official page path changes.

Every record also contains:
- official source portals
- a category-specific source/search
- a browser fallback search

Do not use static RAG records as proof of current travel rules. Route
time-sensitive requests to live services or show the authoritative current
source.
