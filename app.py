# Copyright (c) 2025 LastPerson07 : https://github.com/LastPerson07.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os
from flask import Flask, render_template

# Get absolute path to templates (handles LastPerson07/templates structure)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

@app.route("/")
def welcome():
    # Render the welcome page with animated "LastPerson07 Bot" text
    return render_template("welcome.html")

if __name__ == "__main__":
    # Default to port 5000 if PORT not set (Render sets $PORT)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # debug=False for production
