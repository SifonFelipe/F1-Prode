# F1 Prode

A Django-based Formula 1 prediction project.

Users can:
- Predict the results of each Grand Prix during the season.
- Earn points based on the accuracy of their predictions.
- Compete in global rankings, among friends, or within private leagues.

<img src="https://raw.githubusercontent.com/SifonFelipe/F1-Prode/refs/heads/main/videos/create-predictions.gif" width="800" alt="Create predictions demo" />

---

## Technologies Used

- Python 3.12
- Django 5.2
- SQLite3 (for local database)
- HTML5, CSS3 (Bootstrap or custom styles)
- JavaScript (for countdown timers, filters, etc.)

---

## Local Installation


1. Clone this repository:

```bash
git clone https://github.com/SifonFelipe/F1-Prode.git
```

2. Navigate to the project directory:

```bash
cd F1-Prode
```

3. (Optional) Create and activate a virtual environment:

```bash
python3 -m venv formula1env
source formula1env/bin/activate  # on linux
```


4. Install the project dependencies:

```bash
pip install -r requirements.txt
```


5. Run database migrations:

```bash
python manage.py migrate
```


6. Start the development server:

```bash
python manage.py runserver
```

## License


This project is licensed under the MIT License.
See the LICENSE file for more information.


## Contributions

Contributions, issues, and feature requests are welcome!
Feel free to fork this repository or open a Pull Request.

## Author

* SifonFelipe

