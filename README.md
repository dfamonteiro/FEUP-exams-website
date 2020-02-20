# [The FEUP exams website no one asked for](https://dfamonteiro.github.io/FEUP-exams-website)

## Deploying the website on your computer
1. Change your working directory to the root of this project in your computer
2. Run this command
   ```
   python3 -m http.server 8080
   ```
3. Open a web browser at [localhost:8080](http://127.0.0.1:8080)

## Updating the exams' data
1. Change your working directory to the root of this project in your computer
2. Run this command
   ```
   python3 update_data.py -cue -vv
   ```
3. Drink a glass of water (the update script takes 10 minutes, more or less (depends on the state of [feupy](https://github.com/dfamonteiro/feupy)'s cache))

## Acknowledgements
+ I'd like to thank the folks at [NIAEFEUP](https://ni.fe.up.pt/) for providing a straightforward API for their [Timetable Selector tool](https://ni.fe.up.pt/tts/)
+ The curricular units and exams are scraped with [feupy](https://github.com/dfamonteiro/feupy), a Sigarra scraping library written in Python by [yours truly](https://github.com/dfamonteiro)

## Disclaimer
If you think that the Javascipt code at [main.js](https://github.com/dfamonteiro/FEUP-exams-website/blob/master/main.js) is some of the worst code you have ever seen, you may be correct. I think I'm going to use the "didn't even know Javascript a week ago" excuse :)