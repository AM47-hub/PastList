from flask import Flask, request, make_response
import re
import json
import os

# --- CONSTANTS ---

SUFFIX = {
    'Road': 'Rd.', 'Street': 'St.', 'Crescent': 'Cres.', 
    'Place': 'Pl.', 'Avenue': 'Ave.', 'Lane': 'Ln.', 
    'Highway': 'Hwy.', 'Way': 'Wy.','Row': 'Rw.', 'Terrace': 'Tce.', 'Drive': 'Dr.'
}

app = Flask(__name__)

def quick_addr(text):
    # Fast extraction of address-only components
    keywords = ["flat", "number", "beside", "suburb"]

    delimit = re.compile(r'\b(' + '|'.join(keywords) + r')\b', re.I)
    chunks = list(delimit.finditer(text))
    
    tokens = {k: "" for k in keywords}
    for i in range(len(chunks)):
        start = chunks[i].end()
        end = chunks[i+1].start() if i + 1 < len(chunks) else len(text)
        tokens[chunks[i].group(1).lower()] = text[start:end].strip()

    # Formulate Location
    unit = tokens['flat'].replace(" ", "").upper()
    numb = tokens['number'].replace(" ", "").upper()
    location = f"U{unit}/{numb}" if unit else numb

    # Standardise "The" and Suffixes
    beside = re.sub(r'^the\s+', '', tokens['beside'], flags=re.I)

    full_addr = f"{location} {beside} {tokens['suburb']}"
    full_addr = re.sub(r'\s+', ' ', full_addr).strip().title()

    for full_word, abbrev in SUFFIX.items():
        full_addr = re.sub(rf'\b{full_word}\b', abbrev, full_addr, flags=re.I)
    return full_addr

@app.route('/process', methods=['POST'])
def get_unique_list():
    try:
        PassOut = request.get_json(force=True)

        raw = str(PassOut.get('text', '')).strip()
        
        # Use a SET for automatic deduplication
        unique_addresses = set()
        
        # Split into individual notes and process
        for note in [s.strip() for s in raw.split('|') if 'Content:' in s]:
            if 'Content:' in note:
                body = note.split('Content:', 1)[1]
                addr = quick_addr(body)
                if addr:
                    unique_addresses.add(addr)

        # Return as a sorted list
        return make_response(json.dumps(sorted(list(unique_addresses))), 200)

    except Exception as e:
        return make_response(json.dumps({"error": str(e)}), 500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
