from flask import Flask, request, make_response
import re
import json
import os

# --- CONSTANTS ---

REPAIRS = {
    'one': '1', 'won': '1', 'two': '2', 'to': '2',
    'three': '3', 'four': '4', 'for': '4',
    'five': '5', 'six': '6',
    'seven': '7', 'eight': '8', 'ate': '8',
    'nine': '9', 'zero': '0', 'none':'0', 'nill':'0',
    'dash': '-'
}

SUFFIX = {
    'Road': 'Rd.', 'Street': 'St.', 'Crescent': 'Cres.', 
    'Place': 'Pl.', 'Avenue': 'Ave.', 'Lane': 'Ln.', 
    'Highway': 'Hwy.', 'Way': 'Wy.','Row': 'Rw.', 'Terrace': 'Tce.', 'Drive': 'Dr.'
}

app = Flask(__name__)

@app.route('/ping', methods=['GET', 'HEAD'])
def health_check():

def fast_parse(text):

    keywords = ["flat", "number", "beside", "suburb"]

    delimit = re.compile(r'\b(' + '|'.join(keywords) + r')\b', re.I)
    chunks = list(delimit.finditer(text))

    raw_vals = {k: "" for k in keywords}
    for i in range(len(chunks)):
        start = chunks[i].end()

        end = chunks[i+1].start() if i + 1 < len(chunks) else len(text)

        raw_vals[chunks[i].group(1).lower()] = text[start:end].strip()
    return raw_vals

def quick_addr(tokens):

    unit = tokens.get('flat', '').replace(" ", "").upper()
    numb = tokens.get('number', '').replace(" ", "").upper()

    location = f"U{unit}/{numb}" if unit else numb

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

        raw = str(PassOut.get('text', '')).replace('\xa0', ' ').strip()
        
        # Use a set for simple deduplication
        unique_addresses = set()

        for note in [s.strip() for s in raw.split('|') if 'Content:' in s]:

            body = note.split('Content:', 1)[1]

            # Apply your REPAIRS logic
            for word, digit in REPAIRS.items():
                body = re.sub(rf'\b{word}\b', digit, body, flags=re.I)
            
            # Parse and Construct
            tokens = fast_parse(body)
            addr = quick_addr(tokens)
            
            if addr:
                unique_addresses.add(addr)
        # Return as a sorted list
        return make_response(json.dumps(sorted(list(unique_addresses))), 200)

    except Exception as e:
        return make_response(json.dumps({"error": str(e)}), 500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
