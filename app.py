import json
import traceback
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from flask import Flask, render_template, request, send_file, session, abort
import tempfile
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def index():
    return render_template("indenew.html")

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_route():
    xml1_path = request.form['xml1_path']
    xml2_path = request.form['xml2_path']

    # Function to read file and return content as a single string
    def read_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    # Function to generate JSON representation of lines
    def generate_json(xml_content):
        json_lines = []
        for line in xml_content.split('\n'):
            json_lines.append(json.dumps(line.strip()))
        return json_lines

    # Function to highlight differences between two JSON representations
    def highlight_differences(json1, json2):
        highlighted_diff = []
        mismatch_indices = set()
        for i, line in enumerate(zip(json1, json2)):
            if line[0] != line[1]:
                highlighted_diff.append((' '.join(json.loads(line[0])), ' '.join(json.loads(line[1])), 'pink'))
                mismatch_indices.add(len(highlighted_diff) - 1)
            else:
                highlighted_diff.append((' '.join(json.loads(line[0])), ' '.join(json.loads(line[1])), 'lightgreen'))
        return highlighted_diff, mismatch_indices

    # Function to generate PDF based on highlighted differences
    def generate_pdf(xml1_lines, xml2_lines):
        output_path = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

        json1 = generate_json(xml1_lines)
        json2 = generate_json(xml2_lines)
        highlighted_diff, mismatch_indices = highlight_differences(json1, json2)

        doc = SimpleDocTemplate(output_path, pagesize=landscape(letter))
        elements = []

        # Create a table to display the compared XML files side by side
        data = [[os.path.basename(xml1_path), os.path.basename(xml2_path)]]  # Using user-provided filenames
        for xml1_line, xml2_line, color in highlighted_diff:
            xml1_line = xml1_line.replace("\n", "\n\n")
            xml2_line = xml2_line.replace("\n", "\n\n")
            data.append([xml1_line, xml2_line])
        table = Table(data, colWidths=[400, 400], rowHeights=[20] * len(data))

        # Apply table style to highlight the differences and adjust text size
        style = TableStyle([('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONTSIZE', (0, 0), (-1, -1), 7)])  # Set font size to 7
        for i in mismatch_indices:
            style.add('BACKGROUND', (0, i + 1), (1, i + 1), 'pink')
        table.setStyle(style)

        elements.append(table)

        # Build PDF
        doc.build(elements)

        return output_path

    # Generate the PDF
    xml1_content = read_file(xml1_path)
    xml2_content = read_file(xml2_path)
    pdf_path = generate_pdf(xml1_content, xml2_content)

    session['pdf_path'] = pdf_path

    return {'success': True}  # Return a valid response

@app.route('/download_pdf')
def download_pdf():
    pdf_path = session.get('pdf_path')
    if pdf_path:
        return send_file(pdf_path, as_attachment=True)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
