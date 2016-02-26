# CNN Scraper
This program takes a set of urls from http://cnn.com and returns a data matrix for the total count of words in all articles. The format of the data matrix is a comma-separated value (csv) file. 

## Requirements
Python 3+ should be good enough. Written in Python 3.5. Python 2.7 not supported. Download here: https://www.python.org/downloads/
newspaper library http://newspaper.readthedocs.org/en/latest/user_guide/install.html#install
 * note: use newspaper3k module name in pip
```bash
$ pip install newspaper3k
```

## How to use
Requires argument pointing to file. Contents of the file should be urls separated by newlines
```bash
 $ cnn_parser.py ~/urls.txt 
```

If you want to save the output of the program to a file, this will work in most unix shells:
```bash
 $ cnn_parser.py ~/urls.txt > ~/output.csv
```