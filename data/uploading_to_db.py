import csv, sqlite3


conn = sqlite3.connect("db.sqlite3")
curs = conn.cursor()
with open('ingredients.csv', encoding='utf-8') as r_file:
    reader = csv.reader(r_file, delimiter=',')
    count = 1
    for row in reader:
        to_db = [count, row[0], row[1]]
        curs.execute("INSERT INTO recipes_ingredient VALUES (?, ?, ?);", to_db)
        count += 1

    conn.commit()
    conn.close()
