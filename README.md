# Web Article Mining
This program takes a set of urls from most news sites and returns a data matrix for the total count of words in all articles. 
Supported news sites are included in [this list](https://github.com/codelucas/newspaper/blob/master/newspaper/resources/misc/popular_sources.txt). The format of the data matrix is a comma-separated value (csv) file. 

## Requirements
 * Python 3+ should be good enough. Written in Python 3.5. Python 2.7 not supported. Download here: https://www.python.org/downloads/

 * "newspaper" library http://newspaper.readthedocs.org/en/latest/user_guide/install.html#install. Use newspaper3k module name in pip. You don't want regular newspaper for this project.
```bash
$ pip install newspaper3k
```

## How to use
Requires argument pointing to file. **Contents of the file should be urls separated by newlines**
```bash
 $ cnn_parser.py ~/urls.txt 
```

If you want to save the output of the program to a file, this will work in most unix shells:
```bash
 $ cnn_scrape.py ~/urls.txt > ~/output.csv
```
