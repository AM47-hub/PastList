from flask import Flask, request, make_response
import re
import json
import os

# --- GLOBAL CONSTANT BLOCK ---
# Digitize Natural Language
CARDINALS = {
    'one': '1', 'won': '1', 'two': '2', 'to': '2',
    'three': '3', 'four': '4', 'for': '4',
    'five': '5', 'six': '6',
    'seven': '7', 'eight': '8', 'ate': '8',
    'nine': '9', 'ten': '10', 'zero': '0', 'none':'0', 'nill':'0',
    'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14',
    'fifteen': '15', 'sixteen': '16', 'seventeen': '17', 'eighteen': '18', 'nineteen': '19',
    'twenty': '20', 'thirty': '30', 'forty':'40', 'fifty':'50',
    '\u002d': '-', '\u2010': '-', '\u2011': '-', '\u2012': '-',
    '\u2013': '-', '\u2014': '-', '\u2212': '-',
    'dash': '-', '–': '-', '—': '-', 'hyphen': '-'
}

# Address abbreviations
SUFFIX = {
    'Road': 'Rd.', 'Street': 'St.', 'Crescent': 'Cres.', 
    'Place': 'Pl.', 'Avenue': 'Ave.', 'Lane': 'Ln.', 
    'Highway': 'Hwy.', 'Way': 'Wy.','Row': 'Rw.', 'Terrace': 'Tce.', 'Drive': 'Dr.'
}

KEYWORDS = {
    "flat", "number", "beside", "suburb", "type", "rent", "rooms", 
    "available", "viewing", "from", "until", "agency", 
    "person", "mobile", "comments"
}

app = Flask(__name__)

@app.route('/ping', methods=['GET', 'HEAD'])
def wakeup():
    return make_response("Ready", 200)

def initial_parse(dictated):
    delimit = re.compile(r'\b(' + '|'.join(KEYWORDS) + r')\b', re.I)
    chunks = list(delimit.finditer(dictated))
    raw_vals = {k: "" for k in KEYWORDS}
    for i in range(len(chunks)):
        start = chunks[i].end()
        end = chunks[i+1].start() if i + 1 < len(chunks) else len(dictated)
        raw_vals[chunks[i].group(1).lower()] = dictated[start:end].strip()
    return raw_vals

def repair_addr(tokens):
    unit = tokens.get('flat', '').replace(" ", "").upper()
    numb = tokens.get('number', '').replace(" ", "").upper()

    if unit:
        # If 'flat' starts with number, add the "U"
        if unit[0].isdigit():
            location = f"U{unit}/{numb}"
        else:
            location = f"{unit}/{numb}"
    else:
        location = numb

    # Standardize 'beside' tokens
    beside = re.sub(r'^the\s+kingsway', 'Kingsway', tokens.get('beside', ''), flags=re.I)
    full_addr = f"{location} {beside} {tokens.get('suburb', '')}"
    full_addr = re.sub(r'\s+', ' ', full_addr).strip().title()

    for full_word, abbrev in SUFFIX.items():
        full_addr = re.sub(rf'\b{full_word}\b', abbrev, full_addr, flags=re.I)
    return full_addr

@app.route('/process', methods=['POST'])
def process():
    try:
        PassOut = request.get_json(force=True)
        payload = PassOut.get('dictated', '')
        raw = str(payload).replace('\xa0', ' ').strip()
        
        # Use a set for simple deduplication
        unique_addresses = set()

        # Split into individual notes then process
        for note in [s.strip() for s in raw.split('|') if 'Content:' in s]:
            body = note.split('Content:', 1)[1]

            # Global Cardinal Repairs
            for word, digit in CARDINALS.items():
                body = re.sub(rf'\b{word}\b', digit, body, flags=re.I)
            # Parse into tokens
            tokens = initial_parse(body)
            # Construct canonical address string
            addr = repair_addr(tokens)
            if len(addr) > 3:
                unique_addresses.add(addr)

        # Return as a sorted list
        def sort_by_street(addr):
            # Split the address take everything from the second token onwards
            parts = addr.split(' ', 1)
            return parts[1] if len(parts) > 1 else addr
        # Sort using the street name as the key
        final_list = sorted(list(unique_addresses), key=sort_by_street)

        return make_response(json.dumps(final_list), 200)

    except Exception as e:
        return make_response(json.dumps({"error": str(e)}), 500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
