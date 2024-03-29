from flask import Flask, request
from operator import itemgetter
import glob
import xlrd
import os
from flask import redirect, url_for, render_template
from werkzeug import secure_filename
import sqlite3

conn = sqlite3.connect('site.db', check_same_thread=False)

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/admin')
def admindisplay():
    return render_template('admin.html')

@app.route('/registercomplaint', methods=['GET', 'POST'])
def register_complaint():
    if request.method == 'POST':
        file = request.files['file']
        form = request.form

        conn = sqlite3.connect('site.db')
        conn.execute("""INSERT INTO complaints VALUES(?,?,?,?,?,?,?)""", (form['district'], form['block'], form['name'], form['address'], form['complaint'], form['product'], form['email']))
        conn.commit()
        conn.close()

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('register_complaint'))
    else:
        return render_template('registercomplaint/index.html')

@app.route("/map", methods=['GET'])
def map():
    filenames=glob.glob('*.xls')
    cnt_names = ["nakli", "fake", "counterfeit", "amk"]
    districts = []

    for sheet in filenames:
            desc_cell = 13
            workbook = xlrd.open_workbook(sheet)
            worksheet = workbook.sheet_by_name('Sheet1')
            rows = worksheet.nrows

            for curr_row in range(13, rows):
                    cell_value = worksheet.cell_value(curr_row, desc_cell)
                    for word in cnt_names:
                            if cell_value.find(word) != -1:
                                districts.append({"district": worksheet.cell_value(curr_row,7), "block": worksheet.cell_value(curr_row,8), "industry": worksheet.cell_value(curr_row,9)})
                                break

    # print(districts[0]['district'])

    new_data = {}

    rv = []

    cursor = conn.execute("""SELECT district, block, product FROM complaints""")

    for row in cursor:
        if not any(d["district"] == row['district'] for d in rv):
            districts.append({"district": row[0], "block": row[1], "industry": row[2]})

    for district in districts:
        if not any(d["district"] == district['district'] for d in rv):
            #does not exist
            rv.append({"district": district['district'], "frequency": 1, "blocks": [district['block']]})
        else:

            for d in rv:
                if d['district'] == district['district']:
                    d['frequency'] += 1
                    d['blocks'].append(district['block'])

                    d['blocks'] = list(set(d['blocks']))

    print(rv[0]['frequency'])

    for i in rv:
        new_data.update({str(i['district']):i['frequency']})


    print new_data
    newer_data = []
    for i in reversed(sorted(new_data.items(), key=itemgetter(1))):
        newer_data.append(i)

    return render_template('map.html', addresses=new_data)

@app.route("/", methods=['GET'])
def root():
    return render_template('index.html')


@app.route("/consumerfeed", methods=['GET'])
def feed():
    return render_template('feeds.html')


@app.route("/userfeed", methods=['GET'])
def userfeed():
    return render_template('userfeed.html')


if __name__ == "__main__":
    app.run(debug=True)
